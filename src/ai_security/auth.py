import os
from typing import Optional, Any
from functools import wraps
from dotenv import load_dotenv
import jwt
from jwt import PyJWKClient
import streamlit as st
import requests

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")
AUTH0_CALLBACK_URL = os.getenv("AUTH0_CALLBACK_URL", "http://localhost:8501/callback")
AUTH0_ADMIN_ROLE = os.getenv("AUTH0_ADMIN_ROLE", "admin")
AUTH0_USER_ROLE = os.getenv("AUTH0_USER_ROLE", "user")

try:
    from auth0.authentication import GetToken

    AUTH0_SDK_AVAILABLE = True
except ImportError:
    AUTH0_SDK_AVAILABLE = False


class Auth0Manager:
    def __init__(self):
        self.domain = AUTH0_DOMAIN
        self.client_id = AUTH0_CLIENT_ID
        self.client_secret = AUTH0_CLIENT_SECRET
        self.audience = AUTH0_AUDIENCE
        self.callback_url = AUTH0_CALLBACK_URL
        self.admin_role = AUTH0_ADMIN_ROLE
        self.user_role = AUTH0_USER_ROLE

    def get_login_url(self) -> str:
        if not AUTH0_SDK_AVAILABLE:
            raise RuntimeError("Auth0 SDK not installed")
        from urllib.parse import urlencode
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.callback_url,
            "scope": "openid profile email",
            "audience": self.audience,
        }
        return f"https://{self.domain}/authorize?{urlencode(params)}"

    def get_logout_url(self) -> str:
        return (
            f"https://{self.domain}/v2/logout?"
            f"?client_id={self.client_id}"
            f"&returnTo=http://localhost:8501"
        )

    def get_token(self, code: str) -> dict:
        if not AUTH0_SDK_AVAILABLE:
            raise RuntimeError("Auth0 SDK not installed")
        get_token = GetToken(self.domain, self.client_id, self.client_secret)
        return get_token.authorization_code(
            code=code,
            redirect_uri=self.callback_url,
        )

    def get_user_info(self, access_token: str) -> dict:
        if not AUTH0_SDK_AVAILABLE:
            raise RuntimeError("Auth0 SDK not installed")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"https://{self.domain}/userinfo", headers=headers)
        response.raise_for_status()
        return response.json()

    def get_jwks(self) -> PyJWKClient:
        jwks_url = f"https://{self.domain}/.well-known/jwks.json"
        return PyJWKClient(jwks_url)

    def validate_token(self, token: str) -> Optional[dict]:
        try:
            jwks = self.get_jwks()
            signing_key = jwks.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=f"https://{self.domain}/",
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_user_roles(self, user_id: str, access_token: str) -> list:
        if not AUTH0_SDK_AVAILABLE:
            return []
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            response = requests.get(
                f"https://{self.domain}/api/v2/users/{user_id}/roles",
                headers=headers,
            )
            response.raise_for_status()
            roles = response.json()
            return [role.get("name") for role in roles]
        except Exception:
            return []

    def has_required_role(self, roles: list, required_role: str) -> bool:
        return required_role in roles


auth0_manager = Auth0Manager()


def get_user_role() -> Optional[str]:
    if "user_role" in st.session_state:
        return st.session_state.user_role
    return None


def is_authenticated() -> bool:
    return "user_info" in st.session_state and st.session_state.user_info is not None


def is_admin() -> bool:
    return st.session_state.get("user_role") == auth0_manager.admin_role


def require_role(required_role: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not is_authenticated():
                raise PermissionError("Authentication required")

            user_role = get_user_role()
            if (
                user_role != auth0_manager.admin_role
                and required_role != auth0_manager.user_role
            ):
                raise PermissionError(f"Role '{required_role}' required")

            if (
                required_role == auth0_manager.admin_role
                and user_role != auth0_manager.admin_role
            ):
                raise PermissionError("Admin role required")

            return func(*args, **kwargs)

        return wrapper

    return decorator


TOOL_ROLES = {
    "get_all_users": "user",
    "get_user": "user",
    "create_user": "admin",
    "update_user": "admin",
    "delete_user": "admin",
}


def validate_tool_access(tool_name: str) -> bool:
    if not is_authenticated():
        return False

    required_role = TOOL_ROLES.get(tool_name, "user")
    user_role = get_user_role()

    if required_role == "admin":
        return user_role == auth0_manager.admin_role

    return user_role in [auth0_manager.admin_role, auth0_manager.user_role]


def validate_tool_access_with_context(tool_name: str, user_role: Optional[str]) -> bool:
    """Validate tool access using provided user role context (non-Streamlit environments)."""
    if not user_role:
        return False

    required_role = TOOL_ROLES.get(tool_name, "user")

    if required_role == "admin":
        return user_role == auth0_manager.admin_role

    return user_role in [auth0_manager.admin_role, auth0_manager.user_role]
