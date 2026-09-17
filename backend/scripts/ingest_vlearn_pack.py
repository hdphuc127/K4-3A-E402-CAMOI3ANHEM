import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.vector_search.embedding import embed_texts
from pypdf import PdfReader

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6663").rstrip("/")
COLLECTION = os.getenv("QDRANT_SOURCES_COLLECTION", "mistaketutor_sources")
VECTOR_SIZE = int(os.getenv("EMBEDDING_DIM", "1536"))
DATA_PATH = Path(os.getenv("VLEARN_PACK_PATH", "/app/data/vlearn-pack"))
MAX_CHATLOG_ROWS = int(os.getenv("VLEARN_CHATLOG_MAX_ROWS", "3000"))
CHUNK_CHARS = int(os.getenv("RAG_CHUNK_CHARS", "1400"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "180"))
BATCH_SIZE = int(os.getenv("RAG_INGEST_BATCH_SIZE", "64"))


def request(
    method: str,
    path: str,
    body: dict | None = None,
    timeout: int = 30,
    *,
    ignore_conflict: bool = False,
    ignore_not_found: bool = False,
) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{QDRANT_URL}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw_error = exc.read().decode("utf-8")
        if ignore_conflict and exc.code == 409:
            return {}
        if ignore_not_found and exc.code == 404:
            return {}
        raise RuntimeError(f"Qdrant error {exc.code}: {raw_error}") from exc
    return json.loads(raw) if raw else {}


def wait_for_qdrant() -> None:
    last_error = ""
    for _ in range(30):
        try:
            request("GET", "/collections", timeout=5)
            return
        except Exception as exc:  # noqa: BLE001 - printed for operator feedback
            last_error = str(exc)
            time.sleep(1)
    raise RuntimeError(f"Qdrant is not ready: {last_error}")


def ensure_collection() -> None:
    if collection_vector_size() not in {None, VECTOR_SIZE}:
        delete_collection()
    request(
        "PUT",
        f"/collections/{COLLECTION}",
        {"vectors": {"size": VECTOR_SIZE, "distance": "Cosine"}},
        ignore_conflict=True,
    )
    for field_name, field_schema in {
        "source_id": "keyword",
        "source_pack": "keyword",
        "source_type": "keyword",
        "source_path": "keyword",
        "module_slug": "keyword",
        "concept_slug": "keyword",
        "track": "keyword",
        "tags": "keyword",
        "created_at": "datetime",
    }.items():
        request(
            "PUT",
            f"/collections/{COLLECTION}/index",
            {"field_name": field_name, "field_schema": field_schema},
            ignore_conflict=True,
        )


def collection_vector_size() -> int | None:
    try:
        response = request("GET", f"/collections/{COLLECTION}")
    except RuntimeError:
        return None
    vectors = response.get("result", {}).get("config", {}).get("params", {}).get("vectors", {})
    if isinstance(vectors, dict) and "size" in vectors:
        return int(vectors["size"])
    return None


def delete_collection() -> None:
    request("DELETE", f"/collections/{COLLECTION}", ignore_not_found=True)


def already_ingested() -> bool:
    response = request(
        "POST",
        f"/collections/{COLLECTION}/points/count",
        {
            "exact": False,
            "filter": {
                "must": [
                    {"key": "source_pack", "match": {"value": "vlearn-pack"}},
                ]
            },
        },
    )
    return int(response.get("result", {}).get("count", 0)) > 0


def delete_existing_pack_points() -> None:
    request(
        "POST",
        f"/collections/{COLLECTION}/points/delete?wait=true",
        {
            "filter": {
                "must": [
                    {"key": "source_pack", "match": {"value": "vlearn-pack"}},
                ]
            }
        },
        timeout=60,
    )


def stable_point_id(source_id: str) -> str:
    digest = hashlib.md5(source_id.encode("utf-8")).hexdigest()  # noqa: S324 - stable id, not security
    return f"{digest[:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


def text_chunks(text: str, *, max_chars: int = CHUNK_CHARS) -> Iterable[tuple[int, str]]:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return
    start = 0
    chunk_index = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            split_at = max(text.rfind("\n\n", start, end), text.rfind(". ", start, end))
            if split_at > start + max_chars // 2:
                end = split_at + 1
        chunk = text[start:end].strip()
        if chunk:
            yield chunk_index, chunk
            chunk_index += 1
        if end >= len(text):
            break
        start = max(0, end - CHUNK_OVERLAP)


def build_point(
    *,
    source_id: str,
    source_type: str,
    source_path: str,
    title: str,
    text: str,
    tags: list[str],
    extra: dict | None = None,
) -> dict:
    payload = {
        "source_id": source_id,
        "source_pack": "vlearn-pack",
        "source_type": source_type,
        "source_path": source_path,
        "title": title,
        "text": text,
        "track": "D",
        "module_slug": "llm-review",
        "concept_slug": "",
        "tags": tags,
        "created_at": "2026-09-17T00:00:00Z",
    }
    if extra:
        payload.update(extra)
    return {
        "id": stable_point_id(source_id),
        "embedding_text": f"{title}\n{text}",
        "payload": payload,
    }


def iter_markdown_points(root: Path) -> Iterable[dict]:
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), relative)
        for chunk_index, chunk in text_chunks(text):
            source_id = f"vlearn:{relative}:chunk:{chunk_index}"
            yield build_point(
                source_id=source_id,
                source_type="transcript" if "transcript/" in relative else "metadata",
                source_path=relative,
                title=title,
                text=chunk,
                tags=["vlearn", "markdown"],
                extra={"chunk_index": chunk_index},
            )


def iter_chatlog_points(root: Path) -> Iterable[dict]:
    path = root / "chatlog" / "tutor_turns.csv"
    if not path.exists():
        return
    with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as file:
        reader = csv.DictReader(file)
        for row_index, row in enumerate(reader):
            if row_index >= MAX_CHATLOG_ROWS:
                break
            question = (row.get("student_question") or "").strip()
            reply = (row.get("tutor_reply") or "").strip()
            if not question and not reply:
                continue
            turn_id = row.get("turn_id") or f"row-{row_index}"
            lecture_title = row.get("lecture_title") or "VLearn tutor turn"
            text = f"Student question:\n{question}\n\nTutor reply:\n{reply}".strip()
            yield build_point(
                source_id=f"vlearn:chatlog:{turn_id}",
                source_type="chatlog",
                source_path="chatlog/tutor_turns.csv",
                title=f"{turn_id} - {lecture_title}",
                text=text[:3000],
                tags=[
                    "vlearn",
                    "chatlog",
                    row.get("cohort_hint") or "",
                    row.get("lecture_code") or "",
                ],
                extra={
                    "turn_id": turn_id,
                    "period": row.get("period") or "",
                    "cohort_hint": row.get("cohort_hint") or "",
                    "lecture_code": row.get("lecture_code") or "",
                    "lecture_title": lecture_title,
                    "has_citation": row.get("has_citation") or "",
                    "move_used": row.get("move_used") or "",
                },
            )


def iter_slide_pdf_points(root: Path) -> Iterable[dict]:
    for path in sorted((root / "slides").glob("*.pdf")):
        relative = path.relative_to(root).as_posix()
        reader = PdfReader(str(path))
        for page_index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            for chunk_index, chunk in text_chunks(text):
                source_id = f"vlearn:{relative}:page:{page_index}:chunk:{chunk_index}"
                yield build_point(
                    source_id=source_id,
                    source_type="slide_pdf",
                    source_path=relative,
                    title=f"{path.stem} - page {page_index}",
                    text=chunk,
                    tags=["vlearn", "slides", "pdf"],
                    extra={
                        "page": page_index,
                        "chunk_index": chunk_index,
                    },
                )


def upsert(points: list[dict], *, batch_number: int) -> None:
    if not points:
        return
    print(
        json.dumps({"status": "embedding", "batch": batch_number, "points": len(points)}),
        file=sys.stderr,
        flush=True,
    )
    embeddings = embed_texts([point.pop("embedding_text") for point in points])
    for point, embedding in zip(points, embeddings, strict=True):
        point["vector"] = embedding
    request(
        "PUT",
        f"/collections/{COLLECTION}/points?wait=true",
        {"points": points},
        timeout=60,
    )


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"VLearn data pack not found: {DATA_PATH}")
    wait_for_qdrant()
    ensure_collection()
    force_reingest = os.getenv("RAG_FORCE_REINGEST", "false").lower() == "true"
    if already_ingested() and not force_reingest:
        print(json.dumps({"status": "skipped", "reason": "vlearn-pack already ingested"}))
        return
    if force_reingest:
        delete_existing_pack_points()

    total = 0
    batch_number = 0
    batch: list[dict] = []
    sources = [
        iter_markdown_points(DATA_PATH),
        iter_chatlog_points(DATA_PATH),
        iter_slide_pdf_points(DATA_PATH),
    ]
    for point in (item for source in sources for item in source):
        batch.append(point)
        if len(batch) >= BATCH_SIZE:
            batch_number += 1
            upsert(batch, batch_number=batch_number)
            total += len(batch)
            batch = []
    if batch:
        batch_number += 1
    upsert(batch, batch_number=batch_number)
    total += len(batch)
    print(
        json.dumps(
            {
                "status": "ok",
                "qdrant_url": QDRANT_URL,
                "collection": COLLECTION,
                "data_path": str(DATA_PATH),
                "points_upserted": total,
                "embedding": "openai",
                "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
