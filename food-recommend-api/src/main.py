from fastapi import FastAPI
from src.api.routes import router as api_router

app = FastAPI(title="Food Recommendation API")

app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "Food Recommendation API is running 🚀"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)