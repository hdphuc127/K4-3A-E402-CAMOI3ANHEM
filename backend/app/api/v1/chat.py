from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
def chat_placeholder() -> dict[str, object]:
    return {
        "success": True,
        "data": {
            "message": (
                "Chat API is reserved for the next MVP iteration. Use "
                "/api/v1/diagnosis for teach-back feedback in this version."
            )
        },
        "error": None,
        "meta": {},
    }
