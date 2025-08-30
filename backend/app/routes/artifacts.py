from fastapi import APIRouter

from app.models.response_models import GetArtifactResponse
from app.utils import create_simple_logger

logger = create_simple_logger(__name__)

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/{artifact_id}", response_model=GetArtifactResponse)
async def get_artifact(
    artifact_id: str, message_id: str, session_id: str, user_id: str
):
    """Get an artifact by message ID and artifact ID."""
    logger.info(f"Fetching artifact {artifact_id} for message {message_id}")
    # Placeholder implementation
    # Artifact should be fetched from database/storage
    return GetArtifactResponse(
        RootModel={
            "artifactId": artifact_id,
            "type": "image",
            "data": "base64_encoded_image_data",
            "url": None,
            "description": "Sample image artifact",
            "timestamp": "2023-10-01T12:00:00Z",
            "width": 800,
            "height": 600,
            "format": "png",
            "thumbnail_data": "base64_encoded_thumbnail_data",
            "alt_text": "An example image",
        },
    )
