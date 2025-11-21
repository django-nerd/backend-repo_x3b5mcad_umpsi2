"""
Database Schemas for the Social App

Each Pydantic model corresponds to a MongoDB collection. The collection name
is the lowercase of the class name (e.g., Post -> "post").
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, description="Unique handle")
    name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[HttpUrl] = Field(None, description="Profile image URL")
    bio: Optional[str] = Field(None, max_length=200, description="Short bio")

class Comment(BaseModel):
    post_id: str = Field(..., description="ID of the post being commented on")
    author_name: str = Field(..., min_length=1, max_length=60)
    text: str = Field(..., min_length=1, max_length=300)
    created_at: Optional[datetime] = None

class Post(BaseModel):
    author_name: str = Field(..., min_length=1, max_length=60)
    author_avatar_url: Optional[HttpUrl] = None
    image_url: HttpUrl = Field(..., description="URL to the image")
    caption: Optional[str] = Field(None, max_length=2200)
    likes: int = 0
    comments: List[dict] = Field(default_factory=list)
    created_at: Optional[datetime] = None
