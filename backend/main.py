from fastapi import FastAPI
from routes.profiles import router as profile_router
from routes.auth import router as auth_router
from routes.posts import router as posts_router
from routes.resources import router as resources_router
from fastapi.middleware.cors import CORSMiddleware
from routes.genie import router as genie_router

app = FastAPI(title="Campus Genie Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(profile_router)
app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(resources_router)
app.include_router(genie_router)

@app.get("/")
def root():
    return {"message": "Campus Genie Backend is running"}

# Based on the complete main.py supplied in this conversation.
from fastapi import FastAPI
from routes.profiles import router as profile_router
from routes.auth import router as auth_router
from routes.posts import router as posts_router
from routes.resources import router as resources_router
from routes.genie import router as genie_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Campus Genie Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(profile_router)
app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(resources_router)
app.include_router(genie_router)


@app.get("/")
def root():
    return {"message": "Campus Genie Backend is running"}