"""Firebase Auth / Google OIDC token verification middleware."""
import os
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer = HTTPBearer(auto_error=False)
FIREBASE_PROJECT = os.environ.get("GCP_PROJECT_ID", "")
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true" or os.getenv("FAIRLENS_DEV_MODE", "") == "true"


import time
import requests

TOKEN_CACHE = {}

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    """Verify Google OAuth2 Bearer token."""
    if credentials is None:
        # Allow unauthenticated in dev mode
        if DEV_MODE:
            return {"uid": "dev-user", "email": "dev@fairlens.dev", "role": "admin"}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    token = credentials.credentials
    
    if token == "dev-token":
        if DEV_MODE:
            return {"uid": "dev-user", "email": "dev@fairlens.dev", "role": "admin"}
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="dev-token only allowed in DEV_MODE")

    try:
        current_time = time.time()
        
        # Check cache
        if token in TOKEN_CACHE:
            entry = TOKEN_CACHE[token]
            if entry["exp"] > current_time:
                return entry["info"]
            else:
                del TOKEN_CACHE[token]
                
        # Validate using Google's tokeninfo endpoint
        resp = requests.get(f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={token}")
        
        # Also support ID tokens if frontend changes
        if resp.status_code != 200:
            resp = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}")
            
        if resp.status_code != 200:
            raise ValueError(resp.json().get("error_description", "Invalid token"))
            
        info = resp.json()
        
        # We need a user profile, so if the token doesn't contain email, fetch userinfo
        email = info.get("email")
        uid = info.get("sub")
        
        if not email:
            user_resp = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if user_resp.status_code == 200:
                user_info = user_resp.json()
                email = user_info.get("email", email)
                uid = user_info.get("sub", uid)
                
        user_data = {
            "uid": uid or "google-user",
            "email": email or "unknown@domain",
            "role": "admin" # Replace with actual DB role logic if needed
        }
        
        # Cache for 5 minutes
        exp = int(info.get("exp", current_time + 300))
        # Ensure we don't cache forever if 'exp' is missing, fallback to +5m
        cache_exp = min(exp, current_time + 300)
        
        TOKEN_CACHE[token] = {"info": user_data, "exp": cache_exp}
        
        return user_data
    except Exception as e:
        # In dev mode, accept any token
        if DEV_MODE:
            return {"uid": "dev-user", "email": "dev@fairlens.dev", "role": "admin"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e}",
        )


def require_role(allowed_roles: list[str]):
    """Dependency factory: enforces RBAC role check."""
    async def _check(user=Depends(verify_token)):
        # In dev mode, allow all
        if DEV_MODE:
            return user
        role = user.get("role", "viewer")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{role}' not permitted. Required: {allowed_roles}",
            )
        return user
    return _check
