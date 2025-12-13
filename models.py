from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime

class Note(BaseModel):
    id: Optional[str] = Field(default=None)
    title: str
    content: str


    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            # converts ObjectId to string
            # helpful for returning valid JSON
        }


# ================= AUTH MODELS =================
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phoneNumber: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPassword(BaseModel):
    email: EmailStr

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str

class ResetPassword(BaseModel):
    email: EmailStr
    password: str

# # todo - models

from pydantic import BaseModel, Field
from typing import List, Optional

class TodoItemIn(BaseModel):
    id: Optional[int] = None          # optional on input; server will assign if missing
    text: str = ""
    done: bool = False
    reminderDate: Optional[str] = ""   # "YYYY-MM-DD" or empty string
    reminderTime: Optional[str] = ""   # "HH:MM" (24-hour) or empty string

class TodoBlockIn(BaseModel):
    title: Optional[str] = "Untitled List"
    items: Optional[List[TodoItemIn]] = None

# Response models (what API returns)
class TodoItem(BaseModel):
    id: int
    text: str
    done: bool
    reminderDate: Optional[str] = ""
    reminderTime: Optional[str] = ""

class TodoBlock(BaseModel):
    id: str = Field(..., alias="id")   # Mongo _id string
    title: str
    items: List[TodoItem]

# ================= TIMETABLE MODELS =================

# ================= TIMETABLE MODELS =================
from typing import Dict, List, Optional
from pydantic import BaseModel

class SlotIn(BaseModel):
    slot_id: Optional[str] = None
    title: str
    start: str
    end: str
    category: Optional[str] = "General"

class WeeklyTemplateIn(BaseModel):
    mode: str  # "constant" or "weekday"
    constant: List[SlotIn]
    monday: List[SlotIn]
    tuesday: List[SlotIn]
    wednesday: List[SlotIn]
    thursday: List[SlotIn]
    friday: List[SlotIn]
    saturday: List[SlotIn]
    sunday: List[SlotIn]

class MarkCompleteIn(BaseModel):
    task_id: str
    date: str  # YYYY-MM-DD
