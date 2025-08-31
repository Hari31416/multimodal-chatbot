from fastapi import APIRouter, HTTPException

from app.models.response_models import GetArtifactResponse, DeleteArtifactResponse
from app.services.storage.redis_cache import redis_cache
from app.utils import create_simple_logger

logger = create_simple_logger(__name__)

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/{artifact_id}", response_model=GetArtifactResponse)
async def get_artifact(
    artifact_id: str, message_id: str, session_id: str, user_id: str
):
    """Get an artifact by message ID and artifact ID."""
    logger.info(f"Fetching artifact {artifact_id} for message {message_id}")

    try:
        artifact = redis_cache.get_artifact_with_full_ownership(
            artifact_id, message_id, session_id, user_id
        )

        if artifact is None:
            raise HTTPException(
                status_code=404,
                detail=f"Artifact {artifact_id} not found or access denied",
            )

        return GetArtifactResponse(RootModel=artifact)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch artifact {artifact_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch artifact")


@router.delete("/delete/{artifact_id}", response_model=DeleteArtifactResponse)
async def delete_artifact(
    artifact_id: str, message_id: str, session_id: str, user_id: str
):
    """Delete an artifact by artifact ID."""
    logger.info(f"Deleting artifact {artifact_id} for message {message_id}")

    try:
        deleted_count = redis_cache.delete_artifact_with_ownership(
            artifact_id, message_id, session_id, user_id
        )

        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Artifact {artifact_id} not found or access denied",
            )

        logger.info(f"Successfully deleted artifact {artifact_id}")
        return DeleteArtifactResponse(
            message=f"Artifact {artifact_id} deleted successfully."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete artifact {artifact_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete artifact")
