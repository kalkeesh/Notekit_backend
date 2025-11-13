# todos.py
from fastapi import APIRouter, HTTPException, Query
from typing import List
from models import TodoBlockIn, TodoBlock  # adjust import if needed
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/api/todos", tags=["Todos"])

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI not set in environment")
client = AsyncIOMotorClient(MONGO_URI)
db = client["NOTEkiT"]


def todo_serializer(doc) -> dict:
    """Convert Mongo document to API-friendly dict and include reminder fields."""
    return {
        "id": str(doc["_id"]),
        "title": doc.get("title", ""),
        "items": [
            {
                "id": int(item.get("id")),
                "text": item.get("text", ""),
                "done": bool(item.get("done", False)),
                "reminderDate": item.get("reminderDate", "") or "",
                "reminderTime": item.get("reminderTime", "") or ""
            }
            for item in doc.get("items", [])
        ],
    }


def get_user_collection(username: str):
    """Return per-user todos collection name, validate username."""
    if not username:
        raise HTTPException(status_code=400, detail="Username is required in request")
    return db[f"{username}_todos"]


def _assign_ids_to_items(items: List[dict], starting_id: int = 1) -> List[dict]:
    """
    Ensure each item has a unique integer id.
    If item already has an id, keep it; otherwise assign increasing ids.
    Preserve reminderDate/reminderTime fields.
    """
    assigned = []
    current = starting_id
    for it in items:
        if it is None:
            it = {}
        # Normalize fields
        text = it.get("text", "") or ""
        done = bool(it.get("done", False))
        reminderDate = it.get("reminderDate", "") or ""
        reminderTime = it.get("reminderTime", "") or ""
        if "id" in it and it.get("id") is not None:
            iid = int(it["id"])
            assigned.append({
                "id": iid,
                "text": text,
                "done": done,
                "reminderDate": reminderDate,
                "reminderTime": reminderTime
            })
            if iid >= current:
                current = iid + 1
        else:
            assigned.append({
                "id": current,
                "text": text,
                "done": done,
                "reminderDate": reminderDate,
                "reminderTime": reminderTime
            })
            current += 1
    return assigned


@router.post("", response_model=TodoBlock)
async def create_todo_block(todo: TodoBlockIn, username: str = Query(...)):
    """Create a new Todo block; Option B: seed with one empty item (with reminder fields empty)."""
    coll = get_user_collection(username)
    items_input = todo.items or []
    if not items_input:
        items_input = [{"id": 1, "text": "", "done": False, "reminderDate": "", "reminderTime": ""}]
    # convert possible pydantic objects to dicts
    raw_items = [it.dict() if hasattr(it, "dict") else it for it in items_input]
    items_assigned = _assign_ids_to_items(raw_items, starting_id=1)
    doc = {"title": todo.title or "Untitled List", "items": items_assigned}
    result = await coll.insert_one(doc)
    inserted = await coll.find_one({"_id": result.inserted_id})
    return todo_serializer(inserted)


@router.get("", response_model=List[TodoBlock])
async def get_all_todo_blocks(username: str = Query(...)):
    coll = get_user_collection(username)
    blocks = []
    async for doc in coll.find().sort([("_id", 1)]):
        blocks.append(todo_serializer(doc))
    return blocks


@router.get("/{id}", response_model=TodoBlock)
async def get_todo_block(id: str, username: str = Query(...)):
    coll = get_user_collection(username)
    doc = await coll.find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Todo block not found with id {id}")
    return todo_serializer(doc)


@router.put("/{id}", response_model=TodoBlock)
async def update_todo_block(id: str, updated: TodoBlockIn, username: str = Query(...)):
    coll = get_user_collection(username)
    existing = await coll.find_one({"_id": ObjectId(id)})
    if not existing:
        raise HTTPException(status_code=404, detail=f"Todo block not found with id {id}")

    existing_items = existing.get("items", []) or []
    existing_max_id = 0
    for it in existing_items:
        try:
            existing_max_id = max(existing_max_id, int(it.get("id", 0)))
        except Exception:
            continue

    incoming = updated.items or []
    incoming_raw = [it.dict() if hasattr(it, "dict") else it for it in incoming]

    with_ids = [it for it in incoming_raw if it.get("id") is not None]
    without_ids = [it for it in incoming_raw if it.get("id") is None]

    normalized_with_ids = [{
        "id": int(it["id"]),
        "text": it.get("text", "") or "",
        "done": bool(it.get("done", False)),
        "reminderDate": it.get("reminderDate", "") or "",
        "reminderTime": it.get("reminderTime", "") or ""
    } for it in with_ids]

    max_existing_or_incoming = existing_max_id
    for it in normalized_with_ids:
        if it["id"] > max_existing_or_incoming:
            max_existing_or_incoming = it["id"]

    assigned_new = _assign_ids_to_items(without_ids, starting_id=max_existing_or_incoming + 1)

    final_items = normalized_with_ids + assigned_new
    final_items = sorted(final_items, key=lambda x: x["id"])

    update_doc = {
        "title": updated.title or existing.get("title", "Untitled List"),
        "items": final_items
    }

    result = await coll.update_one({"_id": ObjectId(id)}, {"$set": update_doc})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Todo block not found with id {id}")

    new_doc = await coll.find_one({"_id": ObjectId(id)})
    return todo_serializer(new_doc)


@router.delete("/{id}")
async def delete_todo_block(id: str, username: str = Query(...)):
    coll = get_user_collection(username)
    result = await coll.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Todo block not found with id {id}")
    return {"message": f"Todo block {id} deleted successfully"}

