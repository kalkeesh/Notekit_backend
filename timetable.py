# timetable.py
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os, uuid
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/api/timetable", tags=["Timetable"])

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["NOTEkiT"]

# --------------------------------------------
# Utils
# --------------------------------------------
def get_template_collection(username: str):
    return db[f"{username}_templates"]

def get_streak_collection(username: str):
    return db[f"{username}_task_streaks"]  # per-task streaks

def ensure_slot_id(slot: dict):
    if "slot_id" not in slot or not slot["slot_id"]:
        slot["slot_id"] = str(uuid.uuid4())
    return slot

# --------------------------------------------
# GET /templates (load constant + weekday + mode)
# --------------------------------------------
@router.get("/templates")
async def get_templates(username: str = Query(...)):
    coll = get_template_collection(username)
    doc = await coll.find_one({"_id": "templates"})

    if not doc:
        # return empty template
        return {
            "mode": "constant",
            "constant": [],
            "monday": [], "tuesday": [], "wednesday": [],
            "thursday": [], "friday": [], "saturday": [], "sunday": []
        }

    doc.pop("_id", None)
    return doc


# --------------------------------------------
# POST /templates  (save all templates)
# --------------------------------------------
@router.post("/templates")
async def save_templates(payload: dict, username: str = Query(...)):
    coll = get_template_collection(username)

    # Normalize slot_ids
    for key, value in payload.items():
        if isinstance(value, list):
            for slot in value:
                ensure_slot_id(slot)

    payload["_id"] = "templates"
    await coll.update_one({"_id": "templates"}, {"$set": payload}, upsert=True)

    return {"message": "templates_saved"}


# --------------------------------------------
# GET /today (return tasks of today depending on mode)
# --------------------------------------------
@router.get("/today")
async def get_today(username: str = Query(...)):
    coll = get_template_collection(username)
    streak_coll = get_streak_collection(username)

    doc = await coll.find_one({"_id": "templates"})
    if not doc:
        return {"mode": "constant", "slots": []}

    mode = doc["mode"]
    today = datetime.now().strftime("%Y-%m-%d")
    weekday = datetime.now().strftime("%A").lower()  # monday, tuesday ...

    if mode == "constant":
        slots = doc.get("constant", [])
    else:
        slots = doc.get(weekday, [])

    # attach streak + completed
    enriched = []

    for s in slots:
        slot_id = s["slot_id"]

        streak_doc = await streak_coll.find_one({"slot_id": slot_id})
        streak = streak_doc["streak"] if streak_doc else 0
        last_completed = streak_doc["last_date"] if streak_doc else None

        enriched.append({
            **s,
            "streak": streak,
            "completed": (last_completed == today)
        })

    return {
        "mode": mode,
        "slots": enriched
    }


# --------------------------------------------
# POST /mark-complete  (per-task streak)
# --------------------------------------------
@router.post("/mark-complete")
async def mark_complete(payload: dict, username: str = Query(...)):
    slot_id = payload["task_id"]
    date = payload["date"]

    streak_coll = get_streak_collection(username)

    doc = await streak_coll.find_one({"slot_id": slot_id})

    today = datetime.fromisoformat(date).date()
    yesterday = today - timedelta(days=1)

    if doc:
        # continue streak if yesterday matched
        if doc.get("last_date") == yesterday.isoformat():
            new_streak = doc["streak"] + 1
        else:
            new_streak = 1
    else:
        new_streak = 1

    await streak_coll.update_one(
        {"slot_id": slot_id},
        {
            "$set": {
                "slot_id": slot_id,
                "streak": new_streak,
                "last_date": today.isoformat()
            }
        },
        upsert=True
    )

    return {"message": "done", "new_streak": new_streak}
