from fastapi import APIRouter
from src.models.schemas import QueryRequest
from src.services.recommender import recommend_food
from .nutrition import router as nutrition_router

router = APIRouter()

@router.post("/recommend")
def recommend(req: QueryRequest):
    print("Request:", req)
    results = recommend_food(req.query, top_k=req.top_k, alpha=req.alpha)
    print("Results:", results)
    return {"query": req.query, "results": results}

router.include_router(nutrition_router)