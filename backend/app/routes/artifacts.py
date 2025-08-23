from fastapi import APIRouter

from backend.app.model.response_models import GetArtifactResponse
from backend.app.utils import create_simple_logger

logger = create_simple_logger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/artifacts/{session_id}/{artifact_id}", response_model=GetArtifactResponse)
async def get_artifact(session_id: str, artifact_id: str):
    """Get an artifact by session ID and artifact ID."""
    logger.info(f"Fetching artifact {artifact_id} for session {session_id}")
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
