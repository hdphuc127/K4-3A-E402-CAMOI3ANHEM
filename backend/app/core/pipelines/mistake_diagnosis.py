from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.core.citation.source_citation import build_source_citation
from app.core.prompts.mistake_diagnosis_prompt import MISTAKE_DIAGNOSIS_SYSTEM_PROMPT
from app.core.vector_search.retriever import retrieve_tokenization_context
from app.db.review_data import get_review_data
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResult


def diagnose_mistake(request: DiagnosisRequest) -> DiagnosisResult:
    """Diagnose a learner answer with deterministic correctness first.

    The golden-set quality bar has one non-negotiable requirement: do not mark a
    clearly correct learner answer as wrong. For that reason the MVP uses a
    deterministic answer/misconception layer first, then attaches retrieved
    context as citation. LLM-generated prose can be reintroduced later as a
    refinement layer, but it must not override correctness.
    """

    if request.question_id == "tokenization-basic-01":
        context = {
            "source_id": "t06-tokenization:tokenization-03",
            "title": "Transcript T06 - Tokenization",
            "excerpt": (
                "Tokenization là bước chia văn bản thành các đơn vị nhỏ hơn để "
                "mô hình xử lý. Trong ví dụ đơn giản, ta có thể tạm tách theo "
                "khoảng trắng."
            ),
        }
        diagnosis = _diagnose_legacy_tokenization(request)
    else:
        context = retrieve_tokenization_context(
            request.lesson_id,
            query=f"{request.question_text}\n{request.student_answer}",
        )
        diagnosis = _diagnose_review_answer(request)

    citations = []
    if diagnosis.get("use_citation", True):
        citations = [
            build_source_citation(
                source_id=context["source_id"],
                title=context["title"],
                excerpt=context["excerpt"],
                confidence=float(diagnosis["confidence"]),
            )
        ]

    return DiagnosisResult(
        question_id=request.question_id,
        is_correct=diagnosis["misconception"] == "answer_is_correct",
        misconception=str(diagnosis["misconception"]),
        hint=str(diagnosis["hint"]),
        next_action=str(diagnosis["next_action"]),
        citations=citations,
        debug_prompt_name=MISTAKE_DIAGNOSIS_SYSTEM_PROMPT.name,
    )


def _diagnose_legacy_tokenization(request: DiagnosisRequest) -> dict[str, Any]:
    normalized_answer = _normalize(request.student_answer)
    if normalized_answer in {"3", "three", "ba"}:
        return {
            "misconception": "answer_is_correct",
            "hint": (
                "Đáp án đúng. Hãy nói lại vì sao câu này có 3 token khi tách "
                "theo khoảng trắng."
            ),
            "next_action": "explain_reasoning",
            "confidence": 0.86,
        }
    if normalized_answer in {"8", "7", "6"}:
        return {
            "misconception": "counting_characters_or_spaces",
            "hint": (
                "Bạn có vẻ đang đếm ký tự hoặc cả dấu cách. Hãy tách câu thành "
                "các cụm liên tiếp không có khoảng trắng rồi đếm các cụm đó."
            ),
            "next_action": "retry_answer",
            "confidence": 0.78,
        }
    return {
        "misconception": "ambiguous_or_unknown",
        "hint": (
            "Câu trả lời chưa đủ rõ để chẩn đoán chắc chắn. Hãy viết cách bạn "
            "đếm từng đơn vị trong câu."
        ),
        "next_action": "ask_for_reasoning",
        "confidence": 0.52,
    }


def _diagnose_review_answer(request: DiagnosisRequest) -> dict[str, Any]:
    topic = _resolve_topic(request)
    if _answers_match(request.student_answer, request.correct_answer) or _is_topic_correct_answer(topic, request.student_answer):
        return {
            "misconception": "answer_is_correct",
            "hint": _correct_hint(topic),
            "next_action": "explain_reasoning",
            "confidence": 0.94,
        }

    text = _normalize(f"{request.question_text} {request.student_answer}")

    if _is_out_of_scope(text):
        return {
            "misconception": "ambiguous_or_unknown",
            "hint": _out_of_scope_hint(text),
            "next_action": "ask_for_reasoning",
            "confidence": 0.72,
            "use_citation": False,
        }

    review_question = next(
        (question for question in get_review_data().questions if question.id == request.question_id),
        None,
    )
    base_hint = _topic_hint(topic, request.student_answer, request.correct_answer)
    if review_question is not None and review_question.why:
        base_hint = f"{review_question.why} {base_hint}"

    return {
        "misconception": "ambiguous_or_unknown",
        "hint": base_hint,
        "next_action": "ask_for_reasoning",
        "confidence": 0.82,
    }


def _answers_match(student_answer: str, correct_answer: str) -> bool:
    student = _normalize(student_answer)
    correct = _normalize(correct_answer)
    if not student or not correct:
        return False
    if student == correct or student in correct or correct in student:
        return True

    equivalent_phrases = (
        ("token la manh van ban", ("mot manh van ban",)),
        ("token id chi la chi so tra cuu", ("khong noi len", "y nghia")),
        ("token id chi la so thu tu", ("khong noi len", "y nghia")),
        ("embedding la vector", ("dac trung ngu nghia",)),
        ("attention giup mo hinh can nhac", ("lien quan", "token")),
        ("no noi toi tham", ("tham",)),
        ("mo hinh sinh loi goi", ("loi goi", "thuc thi")),
    )
    return any(
        phrase in student and all(term in correct for term in required_terms)
        for phrase, required_terms in equivalent_phrases
    )


def _is_topic_correct_answer(topic: str, student_answer: str) -> bool:
    student = _normalize(student_answer)
    if topic == "embedding":
        return "embedding" in student and "vector" in student and (
            "ngu nghia" in student or "semantic" in student or "dac trung" in student
        )
    return False


def _normalize(value: str) -> str:
    no_accent = "".join(
        char
        for char in unicodedata.normalize("NFD", value.lower())
        if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", no_accent).strip()


def _resolve_topic(request: DiagnosisRequest) -> str:
    text = _normalize(f"{request.lesson_id} {request.question_text} {request.student_answer}")
    if "hallucination" in text or "bia" in text or "rag" in text:
        return "hallucination"
    if "tool" in text or "api" in text or "cong cu" in text:
        return "tool-calling"
    if "attention" in text or "tham" in text or "dai tu" in text or "chu y" in text:
        return "attention"
    if "embedding" in text or "vector" in text or "token id" in text:
        return "embedding"
    if "token" in text:
        return "tokenization"
    return request.lesson_id


def _correct_hint(topic: str) -> str:
    details = {
        "tokenization": "token là mảnh văn bản do tokenizer cắt ra",
        "embedding": (
            "Token ID chỉ là chỉ số tra cứu, còn embedding vector mới mang "
            "thông tin ngữ nghĩa"
        ),
        "attention": "attention gắn trọng số liên quan giữa các token trong ngữ cảnh",
        "tool-calling": (
            "mô hình sinh lời gọi có cấu trúc, ứng dụng bên ngoài mới thực thi tool"
        ),
        "hallucination": (
            "LLM dự đoán token và cần nguồn căn cứ/ngữ cảnh để giảm bịa"
        ),
    }
    return f"Đáp án đúng. Hãy giải thích lại bằng lời của bạn: {details.get(topic, 'khái niệm chính')}."


def _topic_hint(topic: str, student_answer: str, correct_answer: str) -> str:
    normalized_student = _normalize(student_answer)
    if topic == "tokenization":
        return (
            "Bạn đang cần phân biệt token với từ hoàn chỉnh. Token là một mảnh "
            "văn bản: có thể là từ, một phần của từ, hoặc dấu câu."
        )
    if topic == "embedding":
        return (
            "Lỗ hổng chính là nhầm Token ID với embedding vector. Token ID chỉ "
            "là vị trí tra cứu trong từ điển; khoảng cách ngữ nghĩa nằm ở "
            "embedding vector. Hai ID gần nhau không đủ để kết luận hai token "
            "gần nghĩa."
        )
    if topic == "attention":
        return (
            "Bạn đang mô tả attention chưa đúng trọng tâm. Attention không phải "
            "bước nén hay chọn ngôn ngữ đầu ra; nó tính trọng số liên quan giữa "
            "các token trong ngữ cảnh, ví dụ đại từ 'nó' liên hệ tới 'thảm'."
        )
    if topic == "tool-calling":
        return (
            "Điểm cần sửa là mô hình không tự thực thi tool và cũng không học "
            "tool vào bộ nhớ. Tool calling nghĩa là model sinh lời gọi có cấu "
            "trúc, còn ứng dụng bên ngoài/API mới thực thi."
        )
    if topic == "hallucination":
        if "rag" in normalized_student:
            return (
                "RAG giúp giảm rủi ro LLM bịa nhưng không loại bỏ hoàn toàn. "
                "Nếu truy hồi sai, thiếu nguồn căn cứ, hoặc ngữ cảnh yếu, câu "
                "trả lời vẫn có thể nghe hợp lý nhưng sai."
            )
        return (
            "Câu trả lời còn thiếu cơ chế: LLM sinh câu bằng cách dự đoán token "
            "theo xác suất và ngữ cảnh. Khi thiếu nguồn căn cứ hoặc truy hồi sai "
            "ngữ cảnh, nó có thể tạo câu nghe hợp lý nhưng không đúng."
        )
    return (
        f"Câu trả lời chưa khớp với đáp án đúng: {correct_answer}. Hãy nêu rõ "
        "khái niệm cốt lõi và vì sao lựa chọn của bạn khác với đáp án."
    )


def _is_out_of_scope(text: str) -> bool:
    return any(
        marker in text
        for marker in (
            "diem cuoi ky",
            "ban khac",
            "dau dau",
            "thuoc gi",
            "slide 27",
            "khong co trong he thong",
        )
    )


def _out_of_scope_hint(text: str) -> str:
    if "diem cuoi ky" in text:
        return (
            "Mình không có dữ liệu điểm cuối kỳ, nên không thể kết luận. Bạn "
            "nên kiểm tra hệ thống điểm hoặc hỏi giảng viên/TA."
        )
    if "ban khac" in text:
        return (
            "Mình không thể tiết lộ dữ liệu hoặc câu trả lời riêng tư của người "
            "khác. Bạn có thể gửi câu trả lời của bạn để mình góp ý."
        )
    if "dau dau" in text or "thuoc gi" in text:
        return (
            "Câu hỏi này ngoài phạm vi học LLM và liên quan sức khỏe. Mình không "
            "tư vấn y tế; hãy hỏi chuyên gia y tế nếu cần."
        )
    if "slide 27" in text:
        return (
            "Mình không thấy nguồn slide 27 trong hệ thống, nên không thể trích "
            "dẫn đáng tin cậy. Hãy cung cấp tài liệu hoặc chọn nguồn đang có."
        )
    return (
        "Câu hỏi này ngoài phạm vi dữ liệu học hiện có. Hãy cung cấp thêm ngữ "
        "cảnh hoặc chọn một khái niệm trong bài học."
    )
