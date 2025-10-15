from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.data_upload import router as data_upload_router
from app.routers.dashboard import router as dashboard_data_router
from app.routers.customer_analysis import router as customer_analysis_router
from app.routers.product_analysis import router as product_analysis_router
from app.routers.order_analysis import router as order_analysis_router
from app.routers.auth import router as auth_router
from app.routers.data_selection import router as data_selection_router
from app.routers.sync import router as sync_router
from app.routers.whatsapp_message import router as whatsapp_message_router
import cloudinary
from dotenv import load_dotenv
import os
from fastapi import Request, Response
import uuid

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
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # or ["*"] if testing locally
    allow_credentials=True,
    allow_methods=["*"],              # allow all HTTP methods
    allow_headers=["*"],              # allow all headers
)

@app.middleware("http")
async def guest_id_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    guest_id = request.cookies.get("guest_id")
    if not guest_id:
        guest_id = str(uuid.uuid4())
        response.set_cookie(
            key="guest_id",
            value=guest_id,
            max_age=30*24*60*60,  # 30 days
            httponly=True
        )
    return response

# Mount routers
app.include_router(data_upload_router)
app.include_router(dashboard_data_router)
app.include_router(customer_analysis_router)
app.include_router(product_analysis_router)
app.include_router(order_analysis_router)
app.include_router(auth_router)
app.include_router(data_selection_router)
app.include_router(sync_router)
app.include_router(whatsapp_message_router)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
