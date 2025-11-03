from fastapi import APIRouter, HTTPException
import httpx, os
from urllib.parse import urlencode
from dotenv import load_dotenv
from datetime import timedelta
from authent import users_collection, create_access_token  # Import from your authent.py
from fastapi.responses import RedirectResponse

load_dotenv()

router = APIRouter(prefix="/auth/google", tags=["Google Auth"])

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")


# @router.get("/")
# async def google_login():
#     google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
#     params = {
#         "client_id": CLIENT_ID,
#         "response_type": "code",
#         "redirect_uri": REDIRECT_URI,
#         "scope": "openid email profile",
#         "access_type": "offline",
#         "prompt": "consent",
#     }
#     return {"auth_url": f"{google_auth_url}?{urlencode(params)}"}
from fastapi.responses import RedirectResponse

@router.get("/")
async def google_login():
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"{google_auth_url}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def google_callback(code: str):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        token_res = await client.post(token_url, data=data)
        token_res.raise_for_status()
        tokens = token_res.json()

        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        user_res = await client.get(user_info_url, headers=headers)
        user_res.raise_for_status()
        user_info = user_res.json()

    # ========== Handle MongoDB User ==========
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email from Google account")

    existing_user = await users_collection.find_one({"email": email})

    if not existing_user:
        # Create a new user document
        new_user = {
            "name": user_info.get("name"),
            "email": email,
            "password": None,  # no password since it's Google
            "auth_provider": "google",
            "otp": None,
            "otpExpires": None,
        }
        await users_collection.insert_one(new_user)
    else:
        new_user = existing_user

    # Create JWT token
    token = create_access_token(
        subject=email,
        expires_delta=timedelta(minutes=60)
    )

    # Return same structure as your normal login
    # return {
    #     "message": "Login successful via Google",
    #     "token": token,
    #     "name": user_info.get("name"),
    #     "email": email,
    #     "picture": user_info.get("picture"),
    # }

    FRONTEND_URL = "http://localhost:3000"  # change to your frontend URL if deployed

    # Redirect user back to frontend with token as query parameter
    redirect_url = f"{FRONTEND_URL}/login-success?token={token}&name={user_info.get('name')}&email={email}"
    return RedirectResponse(url=redirect_url)

