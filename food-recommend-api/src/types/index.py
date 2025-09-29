# filepath: food-recommend-api/src/types/index.py
# This file defines any custom types or interfaces that may be used throughout the application, providing type safety and clarity.

from typing import List, Optional

class FoodRecommendation:
    def __init__(self, ten_mon: str, ingredients: str, link: Optional[str], similarity: float, keyword_score: float, final_score: float):
        self.ten_mon = ten_mon
        self.ingredients = ingredients
        self.link = link
        self.similarity = similarity
        self.keyword_score = keyword_score
        self.final_score = final_score

class QueryRequest:
    def __init__(self, query: str, top_k: int = 5, alpha: float = 0.7):
        self.query = query
        self.top_k = top_k
        self.alpha = alpha