from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    alpha: float = 0.7