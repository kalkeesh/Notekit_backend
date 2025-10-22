from fastapi import APIRouter, HTTPException, Query
from models import Note
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/api/notes", tags=["Notes"])

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["NOTEkiT"]


def note_serializer(note) -> dict:
    return {
        "id": str(note["_id"]),
        "title": note["title"],
        "content": note["content"],
    }


def get_user_collection(username: str):
    """Return collection for the given username."""
    if not username:
        raise HTTPException(status_code=400, detail="Username is required in request")
    return db[username]  # Dynamic collection per user


@router.post("")
async def create_note(note: Note, username: str = Query(...)):
    """Create a note for a specific user."""
    notes_collection = get_user_collection(username)
    note_dict = note.dict(by_alias=True)
    note_dict.pop("_id", None)
    result = await notes_collection.insert_one(note_dict)
    new_note = await notes_collection.find_one({"_id": result.inserted_id})
    return note_serializer(new_note)


@router.get("")
async def get_all_notes(username: str = Query(...)):
    """Get all notes for a specific user."""
    notes_collection = get_user_collection(username)
    notes = []
    async for note in notes_collection.find():
        notes.append(note_serializer(note))
    return notes


@router.put("/{id}")
async def update_note(id: str, updated_note: Note, username: str = Query(...)):
    """Update a specific note for a specific user."""
    notes_collection = get_user_collection(username)
    result = await notes_collection.update_one(
        {"_id": ObjectId(id)}, {"$set": updated_note.dict(by_alias=True)}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Note not found with id {id}")
    updated = await notes_collection.find_one({"_id": ObjectId(id)})
    return note_serializer(updated)


@router.delete("/{id}")
async def delete_note(id: str, username: str = Query(...)):
    """Delete a specific note for a specific user."""
    notes_collection = get_user_collection(username)
    result = await notes_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Note not found with id {id}")
    return {"message": f"Note {id} deleted successfully"}


@router.get("/health")
async def health_check():
    return {"status": "healthy"}
