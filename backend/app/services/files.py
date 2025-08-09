import pandas as pd


def load_csv(buffer) -> pd.DataFrame:
    return pd.read_csv(buffer)
