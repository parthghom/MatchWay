from fastapi import Header, HTTPException
from supabase import create_client, Client
import os

class AuthUser:
    def __init__(self, id, email):
        self.id = id
        self.email = email

def verify_token(token):
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")

    if not url or not key:
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("SUPABASE_URL="):
                        url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("SUPABASE_SERVICE_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass

    if not url or not key:
        raise RuntimeError("Supabase credentials missing for auth")

    client: Client = create_client(url, key)
    try:
        res = client.auth.get_user(token)
        user = res.user
        return AuthUser(user.id, user.email)
    except Exception as e:
        raise Exception(f"Invalid token: {str(e)}")

verifier = verify_token

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not signed in")

    token = authorization[7:]
    try:
        return verifier(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Not signed in")
