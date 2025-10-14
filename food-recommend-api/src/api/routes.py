from fastapi import APIRouter
from src.models.schemas import QueryRequest
from src.services.recommender import recommend_food
from .nutrition import router as nutrition_router
from src.services.top_foods import get_top_foods
from fastapi import Query

router = APIRouter()

@router.post("/recommend")
def recommend(req: QueryRequest):
    # print("Request:", req)
    results = recommend_food(req.query, top_k=req.top_k, alpha=req.alpha)
    # print("Results:", results)
    return {"query": req.query, "results": results}

router.include_router(nutrition_router)

@router.get("/top-foods")
def get_top_foods_api(limit: int = Query(6, ge=1, le=20, description="Số lượng món ăn muốn lấy")):
    """
    Lấy top món ăn có lượt xem cao nhất
    """
    try:
        data = get_top_foods(limit)
        return {"count": len(data), "results": data}
    except Exception as e:
        return {"error": str(e)}