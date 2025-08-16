import os

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
