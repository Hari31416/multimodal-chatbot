"""Utility functions for handling file and image data encoding, compression, and conversion to/from pandas DataFrames."""

import io
import base64
import gzip
import pandas as pd
from typing import Optional, Union
from PIL import Image

from app.utils import create_simple_logger

logger = create_simple_logger(__name__)


def decode_base64_to_bytes(data: str) -> bytes:
    """Decode a base64 encoded string to bytes."""
    try:
        return base64.b64decode(data)
    except Exception as e:
        logger.error(f"Failed to decode base64 data: {e}")
        raise


def encode_bytes_to_base64(data: bytes) -> str:
    """Encode bytes to a base64 encoded string."""
    try:
        return base64.b64encode(data).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to encode data to base64: {e}")
        raise


def decompress_gzip(data: bytes) -> bytes:
    """Decompress gzip compressed bytes."""
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to decompress gzip data: {e}")
        raise


def compress_gzip(data: bytes) -> bytes:
    """Compress bytes using gzip."""
    try:
        out = io.BytesIO()
        with gzip.GzipFile(fileobj=out, mode="wb") as f:
            f.write(data)
        return out.getvalue()
    except Exception as e:
        logger.error(f"Failed to compress data with gzip: {e}")
        raise


def convert_to_raw_bytes(data: Union[str, bytes], encoding: Optional[str]) -> bytes:
    """Convert input data to raw bytes based on the specified encoding.

    Args:
        data (Union[str, bytes]): Input data, either as a string or bytes.
        encoding (Optional[str]): Encoding type, e.g., 'base64'.

    Returns:
        bytes: Converted raw bytes.
    """
    if isinstance(data, bytes):
        logger.debug("Data is already in bytes format.")
        return data
    elif isinstance(data, str):
        if encoding == "base64":
            return decode_base64_to_bytes(data)
        else:
            logger.error(f"Unsupported encoding: {encoding}")
            raise ValueError(f"Unsupported encoding: {encoding}")
    else:
        logger.error("Data must be of type str or bytes")
        raise TypeError("Data must be of type str or bytes")


def compress_data(data: bytes, compression: Optional[str]) -> bytes:
    """Compress data based on the specified compression type.

    Args:
        data (bytes): Input raw bytes.
        compression (Optional[str]): Compression type, e.g., 'gzip'.

    Returns:
        bytes: Compressed data.
    """
    if compression == "gzip":
        return compress_gzip(data)
    elif compression is None:
        return data
    else:
        logger.error(f"Unsupported compression: {compression}")
        raise ValueError(f"Unsupported compression: {compression}")


class FileHandlerBase:
    """Base class for handling special files like CSV, Parquet, and Images."""

    def __init__(
        self,
        data: Union[str, bytes, pd.DataFrame, Image.Image],
        encoding: Optional[str] = "base64",
        compression: Optional[str] = "gzip",
        **kwargs,
    ):
        self.data = data
        self.encoding = encoding
        self.compression = compression
        self.supported_file_types = ["csv", "parquet", "image"]

    def is_supported_file_type(self, file_type: str) -> bool:
        """Check if the file type is supported."""
        return file_type in self.supported_file_types

    def get_python_friendly_format(self):
        """Get a Python-friendly representation of the file format."""
        raise NotImplementedError("Subclasses should implement this method.")

    def get_base64_representation(self):
        """Get the base64 representation of the file data."""
        raise NotImplementedError("Subclasses should implement this method.")

    def get_raw_bytes(self):
        """Get the raw bytes of the file data."""
        raise NotImplementedError("Subclasses should implement this method.")


def convert_df_to_csv_bytes(df: pd.DataFrame, **kwargs) -> bytes:
    """Convert a pandas DataFrame to CSV bytes."""
    try:
        buffer = io.StringIO()
        df.to_csv(buffer, **kwargs)
        return buffer.getvalue().encode("utf-8")
    except Exception as e:
        logger.error(f"Failed to convert DataFrame to CSV bytes: {e}")
        raise


def convert_df_to_parquet_bytes(df: pd.DataFrame, **kwargs) -> bytes:
    """Convert a pandas DataFrame to Parquet bytes."""
    try:
        buffer = io.BytesIO()
        df.to_parquet(buffer, **kwargs)
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Failed to convert DataFrame to Parquet bytes: {e}")
        raise


class DataFrameHandler(FileHandlerBase):
    """Handler for pandas DataFrame files."""

    def __init__(
        self,
        data: Union[str, bytes, pd.DataFrame],
        file_format: str = "parquet",
        encoding: Optional[str] = "base64",
        compression: Optional[str] = "gzip",
        **kwargs,
    ):
        super().__init__(data, encoding, compression, **kwargs)
        if not self.is_supported_file_type(file_format):
            raise ValueError(f"Unsupported file type: {file_format}")
        self.kwargs = kwargs
        self.file_format = file_format

        if isinstance(data, pd.DataFrame):
            self.df = data
        else:
            raw_bytes = convert_to_raw_bytes(data, encoding)
            if compression == "gzip":
                raw_bytes = decompress_gzip(raw_bytes)
            elif compression is not None:
                raise ValueError(f"Unsupported compression: {compression}")

            if file_format == "csv":
                method_to_use = pd.read_csv
            elif file_format == "parquet":
                method_to_use = pd.read_parquet
            else:
                raise ValueError(f"Unsupported file format: {file_format}")

            self.df = method_to_use(io.BytesIO(raw_bytes), **kwargs)

    def get_python_friendly_format(self) -> pd.DataFrame:
        """Return the DataFrame."""
        return self.df

    def _convert_to_bytes(self) -> bytes:
        """Convert the DataFrame to bytes based on the specified file format."""
        if self.file_format == "csv":
            return convert_df_to_csv_bytes(self.df, **self.kwargs)
        elif self.file_format == "parquet":
            return convert_df_to_parquet_bytes(self.df, **self.kwargs)
        else:
            logger.error(f"Unsupported file format: {self.file_format}")
            raise ValueError(f"Unsupported file format: {self.file_format}")

    def get_base64_representation(self) -> str:
        """Get the base64 representation of the DataFrame."""
        raw_bytes = self._convert_to_bytes()
        compressed_bytes = compress_data(raw_bytes, self.compression)
        return encode_bytes_to_base64(compressed_bytes)

    def get_raw_bytes(self) -> bytes:
        """Get the raw bytes of the DataFrame."""
        raw_bytes = self._convert_to_bytes()
        raw_bytes = compress_data(raw_bytes, self.compression)
        return raw_bytes

    def _repr_html_(self):
        """HTML representation for Jupyter Notebooks."""
        return self.df._repr_html_()


class ImageHandler(FileHandlerBase):
    """Handler for image files."""

    def __init__(
        self,
        data: Union[str, bytes, Image.Image],
        encoding: Optional[str] = "base64",
        compression: Optional[str] = "gzip",
        image_format: str = "PNG",
        **kwargs,
    ):
        super().__init__(data, encoding, compression, **kwargs)
        self.image_format = image_format

        if isinstance(data, Image.Image):
            self.image = data
        else:
            raw_bytes = convert_to_raw_bytes(data, encoding)
            if compression == "gzip":
                raw_bytes = decompress_gzip(raw_bytes)
            elif compression is not None:
                raise ValueError(f"Unsupported compression: {compression}")

            try:
                self.image = Image.open(io.BytesIO(raw_bytes))
            except Exception as e:
                logger.error(f"Failed to open image: {e}")
                raise

    def get_python_friendly_format(self) -> Image.Image:
        """Return the PIL Image."""
        return self.image

    def get_base64_representation(self) -> str:
        """Get the base64 representation of the image."""
        buffer = io.BytesIO()
        self.image.save(buffer, format=self.image_format)
        raw_bytes = buffer.getvalue()
        return encode_bytes_to_base64(raw_bytes)

    def get_raw_bytes(self) -> bytes:
        """Get the raw bytes of the image."""
        buffer = io.BytesIO()
        self.image.save(buffer, format=self.image_format)
        raw_bytes = buffer.getvalue()
        raw_bytes = compress_data(raw_bytes, self.compression)
        return raw_bytes

    def get_thumbnail_bytes(self, size=(128, 128)) -> bytes:
        """Get the raw bytes of the thumbnail image."""
        thumbnail = self.image.copy()
        thumbnail.thumbnail(size)
        buffer = io.BytesIO()
        thumbnail.save(buffer, format=self.image_format)
        raw_bytes = buffer.getvalue()
        raw_bytes = compress_data(raw_bytes, self.compression)
        return raw_bytes

    def get_thumbnail_base64(self, size=(128, 128)) -> str:
        """Get the base64 representation of the thumbnail image."""
        thumbnail = self.image.copy()
        thumbnail.thumbnail(size)
        buffer = io.BytesIO()
        thumbnail.save(buffer, format=self.image_format)
        raw_bytes = buffer.getvalue()
        return encode_bytes_to_base64(raw_bytes)

    def _repr_html_(self):
        """HTML representation for Jupyter Notebooks."""
        base64_data = self.get_base64_representation()
        return f"<img src='data:image/png;base64,{base64_data}'/>"
