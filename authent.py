from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from email.message import EmailMessage
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os, random, smtplib, jwt
from models import UserCreate, UserLogin, ForgotPassword, VerifyOTP, ResetPassword

load_dotenv()

router = APIRouter(prefix="/api", tags=["Authentication"])

MONGO_URI = os.getenv("MONGO_URI")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SECRET_KEY = os.getenv("JWT_SECRET", "replace_this_with_a_real_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

client = AsyncIOMotorClient(MONGO_URI)
db = client["test"]
users_collection = db["users"]

# ================= Helper Functions =================
async def send_email(to_email: str, subject: str, body: str):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg.set_content(body)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
    except Exception:
        raise HTTPException(status_code=500, detail="Email delivery failed")


def create_access_token(subject: str, expires_delta: timedelta | None = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ================= Routes =================
@router.post("/signup")
async def signup(user: UserCreate, background_tasks: BackgroundTasks):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_dict = user.dict()
    user_dict["otp"] = None
    user_dict["otpExpires"] = None
    await users_collection.insert_one(user_dict)

    background_tasks.add_task(
        send_email,
        user.email,
        "Welcome!",
        f"Hi {user.name}, signup successful. Your password: {user.password}"
    )
    return {"message": "User registered successfully"}


@router.post("/login")
async def login(data: UserLogin):
    user = await users_collection.find_one({"email": data.email})
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject=user["email"])
    return {"message": "Login successful", "token": token, "name": user.get("name", "")}


@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword, background_tasks: BackgroundTasks):
    user = await users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = str(random.randint(100000, 999999))
    otp_expires = datetime.utcnow() + timedelta(minutes=10)
    await users_collection.update_one(
        {"email": data.email},
        {"$set": {"otp": otp, "otpExpires": otp_expires}}
    )
    background_tasks.add_task(send_email, data.email, "Password Reset OTP", f"Your OTP is: {otp}")
    return {"message": "OTP sent"}


@router.post("/verify-otp")
async def verify_otp(data: VerifyOTP):
    user = await users_collection.find_one({"email": data.email, "otp": data.otp})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or OTP")
    if user["otpExpires"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Expired OTP")

    await users_collection.update_one({"email": data.email}, {"$set": {"otp": None, "otpExpires": None}})
    return {"message": "OTP verified"}


@router.post("/reset-password")
async def reset_password(data: ResetPassword):
    user = await users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await users_collection.update_one({"email": data.email}, {"$set": {"password": data.password}})
    return {"message": "Password reset successfully"}


@router.get("/protected")
async def protected_route(current_user=Depends(get_current_user)):
    return {"message": f"Hello {current_user.get('name', 'user')}, you accessed a protected route."}


@router.get("/health")
async def health_check():
    try:
        await db.command("ping")
        return {"status": "ok", "message": "Connected to MongoDB successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

