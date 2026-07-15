"""
Upload Routes — File upload for menu images.

Endpoints:
  POST /upload/image → Upload an image file, returns URL
"""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.api.v1.deps import require_role
from app.models.user import User

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_SIZE_MB = 5


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("restaurant_admin")),
):
    """
    Upload a menu item image.
    Returns the relative URL path to use in image_url field.
    Max 5MB. Allowed: jpg, jpeg, png, webp, gif.
    """
    # Validate extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed. Use: jpg, png, webp, gif")

    # Read file content
    content = await file.read()

    # Validate size
    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large. Max {MAX_SIZE_MB}MB.")

    # Create uploads directory if needed
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Generate unique filename
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Save file
    with open(filepath, "wb") as f:
        f.write(content)

    # Return the URL path (served as static files)
    return {"url": f"/uploads/{filename}"}
