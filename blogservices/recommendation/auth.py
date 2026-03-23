import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

import logging
import os

logger = logging.getLogger('auth')
logger.setLevel(logging.INFO)

JWKS_URL = os.environ['JWKS_URL']
security = HTTPBearer()

cached_jwks = None

async def get_jwk():
    global cached_jwks
    if cached_jwks is None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(JWKS_URL)
                response.raise_for_status()
                jwks_data = response.json()

                cached_jwks = jwks_data['keys'][0]
                logger.info("JWK successfully retrieved and cached.")
        except httpx.RequestError as e:
            logger.error(f"Error connecting to JWKS server: {e}")
            raise HTTPException(status_code=503, detail="Auth server is currently unavailable")

    return cached_jwks

async def verify_jwt(token: str):
    jwk_key = await get_jwk()

    try:
        payload = jwt.decode(
            token,
            jwk_key,
            algorithms=["RS256"],
            audience=None,
            options={"verify_aud": False}
        )
        return payload
    except JWTError as e:
        logger.error(f"JWT Validation failed: {e}")
        raise HTTPException(status_code=403, detail="Invalid or expired token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = await verify_jwt(token)

    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(status_code=403, detail="Token does not contain user ID")

    return user_id