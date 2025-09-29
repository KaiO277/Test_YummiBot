from fastapi import APIRouter
from src.models.schemas import QueryRequest
from src.services.recommender import recommend_food

router = APIRouter()

@router.post("/recommend")
def recommend(req: QueryRequest):
    results = recommend_food(req.query, top_k=req.top_k, alpha=req.alpha)
    return {"query": req.query, "results": results}