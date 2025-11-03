from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from authent import router as auth_router
from notes import router as notes_router
from auth_google import router as google_router

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

@app.get("/")
async def root():
    return {"message": "Welcome to Kalki API — Auth + Notes combined!"}


# from fastapi import FastAPI, HTTPException
# from models import Note
# from bson import ObjectId
# from motor.motor_asyncio import AsyncIOMotorClient
# import os
# from dotenv import load_dotenv

# from fastapi.middleware.cors import CORSMiddleware



# load_dotenv()

# app = FastAPI(title="NoteKit API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # or your frontend origin
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# MONGO_URI = os.getenv("MONGO_URI")
# client = AsyncIOMotorClient(MONGO_URI)
# db = client["NOTEkiT"] 
# notes_collection = db["notes"]

# # Utility to convert MongoDB document to dict
# def note_serializer(note) -> dict:
#     return {
#         "id": str(note["_id"]),
#         "title": note["title"],
#         "content": note["content"],
#     }

# @app.get("/health")
# async def health_check():
#     return {"status": "healthy"}

# # Create Note (POST)
# @app.post("/api/notes")
# async def create_note(note: Note):
#     note_dict = note.dict(by_alias=True)
#     # 🧹 Remove _id so MongoDB auto-generates it
#     if "_id" in note_dict:
#         del note_dict["_id"]

#     result = await notes_collection.insert_one(note_dict)
#     new_note = await notes_collection.find_one({"_id": result.inserted_id})
#     return note_serializer(new_note)


# # Get All Notes (GET)
# @app.get("/api/notes")
# async def get_all_notes():
#     notes = []
#     async for note in notes_collection.find():
#         notes.append(note_serializer(note))
#     return notes

# # Update Note (PUT)
# @app.put("/api/notes/{id}")
# async def update_note(id: str, updated_note: Note):
#     note_data = updated_note.dict(by_alias=True)
#     result = await notes_collection.update_one(
#         {"_id": ObjectId(id)}, {"$set": note_data}
#     )
#     if result.matched_count == 0:
#         raise HTTPException(status_code=404, detail=f"Note not found with id {id}")
#     updated = await notes_collection.find_one({"_id": ObjectId(id)})
#     return note_serializer(updated)

# @app.delete("/api/notes/{id}")
# async def delete_note(id: str):
#     result = await notes_collection.delete_one({"_id": ObjectId(id)})
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail=f"Note not found with id {id}")
#     return {"message": f"Note with id {id} deleted successfully"}