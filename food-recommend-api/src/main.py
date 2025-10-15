from fastapi import FastAPI
from src.api.routes import router as api_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="Food Recommendation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hoặc ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "Food Recommendation API is running 🚀"}

# Thư mục chứa ảnh local
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "category_images")

# Cho phép FastAPI phục vụ file ảnh trong thư mục này qua đường dẫn /static
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)