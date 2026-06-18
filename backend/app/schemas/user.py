# backend/app/schemas/user.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ─────────────────────────────────────────────────────────────
# UserCreate — Used when a new user registers
# ─────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    """Schema for user registration request body."""
    
    email: EmailStr = Field(
        description="User's email address", 
        examples=["john@example.com"]
    )
    password: str = Field(
        min_length=8, 
        max_length=72, 
        description="Plain text password — hashed before storage",
        examples=["SecurePass123"]
    )
    full_name: Optional[str] = Field(
        default=None, 
        max_length=255, 
        description="User's full name"
    )


# ─────────────────────────────────────────────────────────────
# UserLogin — Used when an existing user logs in
# ─────────────────────────────────────────────────────────────
class UserLogin(BaseModel):
    """Schema for user login request body."""
    
    email: EmailStr
    password: str


# ─────────────────────────────────────────────────────────────
# UserResponse — What we send BACK to the client
# ─────────────────────────────────────────────────────────────
class UserResponse(BaseModel):
    """Schema for user data sent back to the client."""
    
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        # Allows Pydantic to read data directly from database ORM attributes
        from_attributes = True
