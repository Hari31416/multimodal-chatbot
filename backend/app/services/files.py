import pandas as pd
import base64


def load_csv(buffer) -> pd.DataFrame:
    return pd.read_csv(buffer)


def convert_bytes_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")
