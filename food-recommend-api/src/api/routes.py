from fastapi import APIRouter
from src.models.schemas import QueryRequest
from src.services.recommender import recommend_food
from .nutrition import router as nutrition_router
from src.services.food_db import get_top_foods, get_food_detail
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
def top_foods(limit: int = Query(6, ge=1, le=50), category: str | None = None):
    """
    Lấy top món ăn có lượt xem cao nhất (có thể lọc theo category)
    """
    data = get_top_foods(limit=limit, category=category)
    return {"count": len(data), "results": data}


@router.get("/foods/{food_id}")
def food_detail(food_id: int):
    """
    Lấy chi tiết món ăn theo ID
    """
    data = get_food_detail(food_id)
    if not data:
        raise HTTPException(status_code=404, detail="Không tìm thấy món ăn")
    return data