from pydantic import BaseModel, Field, EmailStr
from typing import Optional
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
