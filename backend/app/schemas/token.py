# backend/app/schemas/token.py

from pydantic import BaseModel


class Token(BaseModel):
    """
    Schema for the response of /auth/login.

    This is the JSON structure the client receives after
    successfully logging in.
    """

    access_token: str
    token_type: str = "bearer"
    # "bearer" is the standard value — it tells the client
    # HOW to send this token: Authorization: Bearer <token>


class TokenData(BaseModel):
    """
    Represents the data we expect to extract FROM a decoded token.
    Used internally by get_current_user — not exposed via any API response.
    """

    user_id: int | None = None
