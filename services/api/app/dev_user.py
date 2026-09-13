"""Development-only user identity.

Authentication is not implemented yet. To represent Goal ownership without
faking a production login system, a single development user is used. The
identity can be overridden per-request via the X-Dev-User-Id header for
development/testing only.

This module is the single seam where a real authentication/identity mechanism
will later plug in. Do not rely on it in production domain logic.
"""

from fastapi import Header

from app.config import get_settings

DEV_USER_HEADER = "X-Dev-User-Id"


def get_current_user_id(
    x_dev_user_id: str | None = Header(default=None, alias=DEV_USER_HEADER),
) -> str:
    """Return the identity for the current request.

    Uses the per-request header when provided, otherwise falls back to the
    configured development user. This is a development seam only.
    """
    if x_dev_user_id is not None and x_dev_user_id.strip():
        return x_dev_user_id.strip()
    return get_settings().dev_user_id