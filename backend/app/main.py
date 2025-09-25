from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.data_upload import router as data_upload_router
from app.routers.dashboard import router as dashboard_data_router
from app.routers.customer_analysis import router as customer_analysis_router
from app.routers.product_analysis import router as product_analysis_router
import cloudinary
from dotenv import load_dotenv
import os

load_dotenv()
# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

app = FastAPI(debug=True)

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
app.include_router(customer_analysis_router)
app.include_router(product_analysis_router)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
