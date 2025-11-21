import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Post, Comment

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers to convert Mongo docs

def serialize_doc(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    # Ensure nested comments IDs if any
    return doc

# Request models for likes and comments
class LikeRequest(BaseModel):
    increment: bool = True

class CreateCommentRequest(BaseModel):
    author_name: str
    text: str

# Routes
@app.get("/")
def read_root():
    return {"message": "Social API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

@app.get("/api/posts", response_model=List[dict])
def list_posts():
    posts = get_documents("post", {}, limit=50)
    posts = [serialize_doc(p) for p in posts]
    # Sort newest first by created_at if available
    posts.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return posts

@app.post("/api/posts", response_model=dict)
def create_post(post: Post):
    post_id = create_document("post", post)
    doc = db["post"].find_one({"_id": ObjectId(post_id)})
    return serialize_doc(doc)

@app.post("/api/posts/{post_id}/like", response_model=dict)
def like_post(post_id: str, payload: LikeRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        _id = ObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post id")

    inc = 1 if payload.increment else -1
    db["post"].update_one({"_id": _id}, {"$inc": {"likes": inc}})
    doc = db["post"].find_one({"_id": _id})
    if not doc:
        raise HTTPException(status_code=404, detail="Post not found")
    return serialize_doc(doc)

@app.post("/api/posts/{post_id}/comments", response_model=dict)
def add_comment(post_id: str, payload: CreateCommentRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        _id = ObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post id")

    comment = {"author_name": payload.author_name, "text": payload.text}
    db["post"].update_one({"_id": _id}, {"$push": {"comments": comment}})
    doc = db["post"].find_one({"_id": _id})
    if not doc:
        raise HTTPException(status_code=404, detail="Post not found")
    return serialize_doc(doc)

