def retrieve_tokenization_context(lesson_id: str) -> dict[str, str]:
    """Return a safe local fixture until the real vector store is connected."""
    return {
        "source_id": f"{lesson_id}:tokenization-03",
        "title": "Transcript T06 - Tokenization",
        "excerpt": (
            "Tokenization la buoc chia van ban thanh cac don vi nho hon de "
            "mo hinh xu ly. Trong vi du don gian, ta co the tam tach theo "
            "khoang trang."
        ),
    }
