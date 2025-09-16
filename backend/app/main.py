from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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



@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
