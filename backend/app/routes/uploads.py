from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import base64
import io
import pandas as pd
from PIL import Image

from app.models.response_models import CSVUploadResponse, ImageUploadResponse
from app.utils import create_simple_logger

logger = create_simple_logger(__name__)

router = APIRouter(prefix="/upload", tags=["uploads"])


def create_thumbnail(image: Image.Image, size=(128, 128)) -> Image.Image:
    """Create a thumbnail of the given image."""
    img_copy = image.copy()
    img_copy.thumbnail(size)
    return img_copy


@router.post("/csv", response_model=CSVUploadResponse)
async def upload_csv(
    file: UploadFile = File(..., description="CSV file to upload"),
    sessionId: str = Form(..., description="Session ID"),
    userId: Optional[str] = Form(
        None, description="Optional user ID associated with the session"
    ),
    messageId: Optional[str] = Form(
        None, description="Optional message ID to associate the artifact with"
    ),
    description: Optional[str] = Form(
        None, description="Optional description for the CSV file"
    ),
    delimiter: Optional[str] = Form(
        ",", description="Delimiter used in the CSV file, default is ','"
    ),
    header: Optional[bool] = Form(
        True, description="Whether the CSV file has a header row, default is True"
    ),
    encoding: Optional[str] = Form(
        "utf-8", description="Encoding of the CSV file, default is 'utf-8'"
    ),
):
    """Endpoint to upload a CSV file."""
    if file.content_type != "text/csv":
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a CSV file."
        )

    try:
        content = await file.read()
        df = pd.read_csv(
            io.StringIO(content.decode(encoding)),
            delimiter=delimiter,
            header=0 if header else None,
        )
        csv_data = base64.b64encode(content).decode("utf-8")

        response = CSVUploadResponse(
            sessionId=sessionId,
            userId=userId,
            data=csv_data,
            type="csv",
            description=f"CSV file with shape {df.shape}",
        )
        logger.info(
            f"Uploaded CSV with shape: {df.shape}, artifactId: {response.artifactId}, sessionId: {sessionId}"
        )
        return response
    except Exception as e:
        msg = f"Error processing CSV file: {str(e)}"
        logger.error(msg)
        raise HTTPException(status_code=500, detail=msg)


@router.post("/image", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    sessionId: str = Form(..., description="Session ID"),
    userId: Optional[str] = Form(
        None, description="Optional user ID associated with the session"
    ),
    messageId: Optional[str] = Form(
        None, description="Optional message ID to associate the artifact with"
    ),
    caption: Optional[str] = Form(
        None, description="Optional caption or description for the image"
    ),
    alt_text: Optional[str] = Form(None, description="Optional alt text for the image"),
):
    """Endpoint to upload an image file."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload an image file."
        )

    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        buffered = io.BytesIO()
        image.save(buffered, format=image.format)
        img_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

        thumbnail = create_thumbnail(image)
        thumb_buffered = io.BytesIO()
        thumbnail.save(thumb_buffered, format=image.format)
        thumb_data = base64.b64encode(thumb_buffered.getvalue()).decode("utf-8")

        response = ImageUploadResponse(
            sessionId=sessionId,
            userId=userId,
            data=img_data,
            type="image",
            description=caption or f"Image of size {image.size}",
            width=image.width,
            height=image.height,
            format=image.format,
            alt_text=alt_text or f"Uploaded image of size {image.size}",
            thumbnail_data=thumb_data,
        )
        logger.info(
            f"Uploaded image with size: {image.size}, artifactId: {response.artifactId}, sessionId: {sessionId}"
        )
        return response
    except Exception as e:
        msg = f"Error processing image file: {str(e)}"
        logger.error(msg)
        raise HTTPException(status_code=500, detail=msg)
