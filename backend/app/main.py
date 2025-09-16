from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.data_upload import router as data_upload_router
from app.routers.dashboard import router as dashboard_data_router

app = FastAPI()

# CORS configuration
origins = [
    # "https://sultan-feeds-crm-frontend-git-main-muhammed-harifs-projects.vercel.app",
    # "https://sultan-feeds-crm-frontend-47i3qtslm-muhammed-harifs-projects.vercel.app/",
    "http://localhost:5173",  # your frontend
    "http://localhost:5173/",
    "http://127.0.0.1:5173",
    "http://localhost:5174/",
    "http://localhost:5174"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # or ["*"] if testing locally
    allow_credentials=True,
    allow_methods=["*"],              # allow all HTTP methods
    allow_headers=["*"],              # allow all headers
)

# Mount routers
app.include_router(data_upload_router)
app.include_router(dashboard_data_router)



@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
