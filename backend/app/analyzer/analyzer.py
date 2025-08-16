from dotenv import load_dotenv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import re
from typing import Dict, Any, Tuple

from backend.app.analyzer.python_iterpreters import LocalPythonExecutor
from backend.app.analyzer.plotting_utils import mpl_fig_to_data_uri
from backend.app.utils import create_simple_logger, set_publish_matplotlib_template
from backend.app.models import AnalysisResponseModalChatbot


load_dotenv()
set_publish_matplotlib_template()
logger = create_simple_logger(__name__)


def _try_parse_json_from_string(response: str) -> Dict[str, Any]:
    # first, try json.loads
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # if that fails, try to extract JSON using regex
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from string: {e}")
                raise ValueError("Invalid JSON format in response") from e
        else:
            logger.error("No JSON found in response string")
            raise ValueError("No valid JSON found in response string")


def _validate_response(response: str) -> AnalysisResponseModalChatbot:
    """
    Validate the response from the LLM to ensure it matches the expected schema.

    Parameters
    ----------
    response : str
        The response from the LLM.

    Returns
    -------
    AnalysisResponseModalChatbot
        The validated response object.
    """
    response_dict = _try_parse_json_from_string(response)
    try:
        return AnalysisResponseModalChatbot.model_validate(response_dict)
    except Exception as e:
        logger.error(f"Invalid response format: {e}")
        raise ValueError("Invalid response format from LLM") from e


def _is_artifact_mime_type(artifact: Any) -> bool:
    """
    Check if the artifact is a valid MIME type string.

    Parameters
    ----------
    artifact : Any
        The artifact to check.

    Returns
    -------
    bool
        True if the artifact is a valid MIME type string, False otherwise.
    """
    return isinstance(artifact, str) and artifact.startswith("data:image/")


async def handle_llm_response(response: str, df: pd.DataFrame) -> Tuple[str, str, bool]:
    """
    Process the LLM response to extract the relevant information.

    Parameters
    ----------
    response : str
        The response from the LLM.
    df : pd.DataFrame
        The DataFrame to be used for analysis.

    Returns
    -------
    str
        The processed response.
    """
    response = _validate_response(response)
    logger.info(f"Successfully validated response.")
    logger.debug(f"Response: {response}")
    explanation = response.explanation
    code = response.code
    plot = response.plot

    if not code.endswith("\nresult"):
        logger.warning("Code does not end with 'result', appending it.")
        code += "\nresult"

    local = LocalPythonExecutor(
        additional_functions={"mpl_fig_to_data_uri": mpl_fig_to_data_uri},
        additional_authorized_imports=["matplotlib.pyplot", "numpy", "pandas"],
    )
    local.send_variables({"df": df, "plt": plt, "np": np, "pd": pd})

    artifact, status_code = local.run_code(code)
    if status_code != 0:
        logger.error(f"Code execution failed.")
        return explanation, code

    artifact_is_mime_type = _is_artifact_mime_type(artifact)
    if plot == "plot_created":
        if artifact_is_mime_type:
            pass
        elif isinstance(artifact, plt.Figure):
            # If artifact is a matplotlib figure, convert it to a data URI
            logger.warning("Artifact is a matplotlib figure, converting to data URI.")
            artifact = mpl_fig_to_data_uri(artifact)
        else:
            logger.error("Artifact is not a valid plot or base64 image string.")
            raise ValueError("Artifact is not a valid plot or base64 image string.")

    elif plot == "no_plot":
        logger.info("No plot was created, returning the result as a string")

    return explanation, artifact, artifact_is_mime_type
