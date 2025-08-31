from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import base64
import io
import pandas as pd
from PIL import Image

from app.models.response_models import CSVUploadResponse, ImageUploadResponse
from app.models.object_models import CSVArtifact, ImageArtifact
from app.services.storage import redis_cache, DataFrameHandler, ImageHandler
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
        file_handler = DataFrameHandler(df)
        csv_data = file_handler.get_base64_representation()
        # Create CSV artifact object
        csv_artifact = CSVArtifact(
            data=csv_data,
            type="csv",
            description=description or f"CSV file with shape {df.shape}",
            num_rows=df.shape[0],
            num_columns=df.shape[1],
            columns=list(df.columns),
        )

        # Save artifact to Redis
        redis_cache.save_artifact(csv_artifact)

        # Add to session's file artifact index
        try:
            redis_cache.add_file_artifact_to_session(
                session_id=sessionId,
                artifact_id=csv_artifact.artifactId,
                user_id=userId,
            )
        except ValueError as ve:
            logger.error(f"Session validation failed: {str(ve)}")
            raise HTTPException(status_code=403, detail=str(ve))

        response = CSVUploadResponse(
            data=csv_data,
            type="csv",
            description=description or f"CSV file with shape {df.shape}",
            num_rows=df.shape[0],
            num_columns=df.shape[1],
            artifactId=csv_artifact.artifactId,
        )

        # Add columns information to the response
        response.columns = list(df.columns)
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

        # Create Image artifact object
        image_artifact = ImageArtifact(
            data=img_data,
            type="image",
            description=caption or f"Image of size {image.size}",
            width=image.width,
            height=image.height,
            format=image.format,
            alt_text=alt_text or f"Uploaded image of size {image.size}",
            thumbnail_data=thumb_data,
        )

        # Save artifact to Redis
        redis_cache.save_artifact(image_artifact)

        # Add to session's file artifact index
        try:
            redis_cache.add_file_artifact_to_session(
                session_id=sessionId,
                artifact_id=image_artifact.artifactId,
                user_id=userId,
            )
        except ValueError as ve:
            logger.error(f"Session validation failed: {str(ve)}")
            raise HTTPException(status_code=403, detail=str(ve))

        response = ImageUploadResponse(
            data=img_data,
            type="image",
            description=caption or f"Image of size {image.size}",
            width=image.width,
            height=image.height,
            format=image.format,
            alt_text=alt_text or f"Uploaded image of size {image.size}",
            thumbnail_data=thumb_data,
            artifactId=image_artifact.artifactId,
        )
        logger.info(
            f"Uploaded image with size: {image.size}, artifactId: {response.artifactId}, sessionId: {sessionId}"
        )
        return response
    except Exception as e:
        msg = f"Error processing image file: {str(e)}"
        logger.error(msg)
        raise HTTPException(status_code=500, detail=msg)
