import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import get_settings

security = HTTPBearer(auto_error=False)

settings = get_settings()
logger = logging.getLogger(__name__)

_firebase_app = None


def _get_firebase_app():
    """Initialize Firebase Admin SDK lazily."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    try:
        import firebase_admin
        from firebase_admin import credentials

        if not settings.firebase_project_id or not settings.firebase_private_key:
            logger.warning("Firebase credentials not configured in environment variables")
            return None

        cred_dict = {
            "type": "service_account",
            "project_id": settings.firebase_project_id,
            "private_key_id": settings.firebase_private_key_id,
            "private_key": settings.firebase_private_key.replace("\\n", "\n"),
            "client_email": settings.firebase_client_email,
            "client_id": settings.firebase_client_id,
            "auth_uri": settings.firebase_auth_uri,
            "token_uri": settings.firebase_token_uri,
        }
        cred = credentials.Certificate(cred_dict)
        _firebase_app = firebase_admin.initialize_app(cred)
        return _firebase_app
    except Exception as e:
        logger.warning(f"Failed to initialize Firebase: {e}")
        return None


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Extract user_id from Firebase ID token.

    In development without Firebase configured, returns a mock user_id
    only if ALLOW_DEV_AUTH=true is set in the environment.
    """
    app = _get_firebase_app()

    if app is None:
        if not settings.allow_dev_auth:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service not configured. Set Firebase credentials in environment variables.",
            )
        logger.warning("ALLOW_DEV_AUTH is enabled — returning mock user 'dev-user-001'. Do NOT use in production.")
        return "dev-user-001"

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = credentials.credentials
    try:
        from firebase_admin import auth
        decoded = auth.verify_id_token(token)
        return decoded["uid"]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
