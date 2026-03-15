"""User authentication module for claude-mpm.

Provides JWT-based user authentication with password hashing,
an in-memory file-backed user store, and FastAPI route handlers.

Public API:
    - models: User, UserCreate, UserLogin, UserResponse, Token, TokenData
    - security: verify_password, get_password_hash, create_access_token,
                create_refresh_token, decode_token
    - store: UserStore
    - dependencies: get_current_user, get_current_active_user
    - router: FastAPI APIRouter with /auth/* endpoints
"""

from claude_mpm.auth.user.dependencies import get_current_active_user, get_current_user
from claude_mpm.auth.user.models import (
    Token,
    TokenData,
    User,
    UserCreate,
    UserLogin,
    UserResponse,
)
from claude_mpm.auth.user.router import router
from claude_mpm.auth.user.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from claude_mpm.auth.user.store import UserStore

__all__ = [
    "Token",
    "TokenData",
    "User",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserStore",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_active_user",
    "get_current_user",
    "get_password_hash",
    "router",
    "verify_password",
]
