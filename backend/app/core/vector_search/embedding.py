from openai import OpenAI

from app.core.config import settings


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Create OpenAI embeddings from extracted text only."""

    if settings.embedding_provider != "openai":
        msg = "Only OpenAI embeddings are configured for this MVP RAG pipeline."
        raise RuntimeError(msg)
    if not settings.openai_api_key:
        msg = "OPENAI_API_KEY is required for RAG embeddings."
        raise RuntimeError(msg)

    client = OpenAI(api_key=settings.openai_api_key, timeout=60.0, max_retries=2)
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]
