import os
import pandas as pd
from io import StringIO
from textwrap import dedent

prompt_type_to_file_name_map = {
    "simple_chat": "simple_chat_system_prompt.txt",
    "simple_chat_with_image": "simple_chat_with_image_system_prompt.txt",
    "data_analyzer": "analyzer_system_prompt.txt",
}


def get_prompt_file_path(prompt_type: str) -> str:
    """
    Get the file path for the specified prompt type.

    Parameters
    ----------
    prompt_type : str
        The type of prompt (e.g., "simple_chat", "data_analyzer").

    Returns
    -------
    str
        The file path to the prompt file.
    """
    if prompt_type not in prompt_type_to_file_name_map:
        raise ValueError(f"Unknown prompt type: {prompt_type}")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = prompt_type_to_file_name_map[prompt_type]
    return os.path.join(current_dir, file_name)


def load_prompt(prompt_type: str) -> str:
    """
    Load the prompt text from the specified file.

    Parameters
    ----------
    prompt_type : str
        The type of prompt to load (e.g., "simple_chat", "data_analyzer").

    Returns
    -------
    str
        The content of the prompt file.
    """
    file_path = get_prompt_file_path(prompt_type)

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found: {file_path}")


class Prompts:
    SIMPLE_CHAT = load_prompt("simple_chat")
    SIMPLE_CHAT_WITH_IMAGE = load_prompt("simple_chat_with_image")
    DATA_ANALYZER = load_prompt("data_analyzer")

    @staticmethod
    def format_system_prompt_for_analyzer(df: pd.DataFrame) -> str:
        """
        Format the prompt for data analysis with the given DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to analyze.

        Returns
        -------
        str
            The formatted prompt for data analysis.
        """
        info = "\n\n## Dataframe Information\nYou have access to a pandas DataFrame named `df`. It contains the dataset you need to analyze. The DataFrame has the following columns:\n\n"
        columns = df.columns.tolist()
        columns = ", ".join(columns)
        info += f"{columns}\n\n"

        buffer = StringIO()
        df.info(buf=buffer)
        info_ = buffer.getvalue()

        info += (
            f"A brief description of the DataFrame is provided below:\n\n{info_}\n\n"
        )

        head_info = df.head(min(5, len(df))).to_markdown(index=False, tablefmt="json")
        info += f"The first 5 rows of the DataFrame are as follows:\n\n{head_info}\n\n"

        info = dedent(info).strip()
        final_prompt = Prompts.DATA_ANALYZER + info
        return final_prompt
