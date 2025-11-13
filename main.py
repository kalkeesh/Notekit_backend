from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from authent import router as auth_router
from notes import router as notes_router
from auth_google import router as google_router
from todos import router as todos_router

app = FastAPI(title="NoteKit API ", description="Combined Auth & Notes API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include routers
app.include_router(auth_router)
app.include_router(notes_router)
app.include_router(google_router)
app.include_router(todos_router)

@app.get("/")
async def root():
    return {"message": "Welcome to Kalki API — Auth + Notes combined!"}

