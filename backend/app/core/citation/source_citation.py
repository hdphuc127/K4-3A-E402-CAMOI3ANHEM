from app.schemas.diagnosis import SourceCitation


def build_source_citation(
    source_id: str,
    title: str,
    excerpt: str,
    confidence: float = 0.72,
) -> SourceCitation:
    return SourceCitation(
        source_id=source_id,
        title=title,
        excerpt=excerpt,
        confidence=confidence,
    )
