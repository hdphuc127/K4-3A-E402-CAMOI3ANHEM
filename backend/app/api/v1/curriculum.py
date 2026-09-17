from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from app.db.curriculum import (
    ConceptRecord,
    LearningModuleRecord,
    get_learning_module,
    list_concepts_by_module,
    list_learning_modules,
)
from app.db.review_data import get_review_data as load_review_data
from app.schemas.common import ApiResponse, ResponseMeta
from app.schemas.curriculum import Concept, ConceptList, LearningModule, ReviewData

router = APIRouter()


@router.get("/modules", response_model=ApiResponse[list[LearningModule]])
def get_modules() -> ApiResponse[list[LearningModule]]:
    modules = [
        _module_to_schema(module)
        for module in list_learning_modules()
    ]
    return ApiResponse(
        success=True,
        data=modules,
        error=None,
        meta=ResponseMeta(timestamp=datetime.now(timezone.utc)),
    )


@router.get(
    "/modules/{module_id}/concepts",
    response_model=ApiResponse[ConceptList],
)
def get_module_concepts(module_id: int) -> ApiResponse[ConceptList]:
    module = get_learning_module(module_id)
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning module not found",
        )

    concepts = [
        _concept_to_schema(concept)
        for concept in list_concepts_by_module(module_id)
    ]
    return ApiResponse(
        success=True,
        data=ConceptList(
            module=_module_to_schema(module),
            concepts=concepts,
        ),
        error=None,
        meta=ResponseMeta(timestamp=datetime.now(timezone.utc)),
    )


@router.get("/review-data", response_model=ApiResponse[ReviewData])
def get_review_data() -> ApiResponse[ReviewData]:
    return ApiResponse(
        success=True,
        data=load_review_data(),
        error=None,
        meta=ResponseMeta(timestamp=datetime.now(timezone.utc)),
    )


def _module_to_schema(module: LearningModuleRecord) -> LearningModule:
    return LearningModule(
        id=module.id,
        slug=module.slug,
        title=module.title,
        description=module.description,
        track=module.track,
        created_at=module.created_at,
    )


def _concept_to_schema(concept: ConceptRecord) -> Concept:
    return Concept(
        id=concept.id,
        module_id=concept.module_id,
        slug=concept.slug,
        title=concept.title,
        expected_summary=concept.expected_summary,
        common_gap=concept.common_gap,
        created_at=concept.created_at,
    )
