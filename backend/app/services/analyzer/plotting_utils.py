from typing import Optional, Literal
import matplotlib
import io
import base64

from app.utils import set_publish_matplotlib_template, create_simple_logger

set_publish_matplotlib_template()

logger = create_simple_logger(__name__)


def mpl_fig_to_data_uri(
    fig: Optional["matplotlib.figure.Figure"] = None,
    fmt: Literal["png", "jpg", "jpeg", "svg", "pdf"] = "png",
    dpi: int = 150,
    transparent: bool = False,
    bbox_inches: str = "tight",
    convert_to_data_uri: bool = True,
) -> str:
    """
    Convert a matplotlib Figure to a base64 string.

    Parameters
    ----------
    fig : matplotlib.figure.Figure | None
        Figure to serialize (defaults to current figure).
    fmt : png | jpg | jpeg | svg | pdf
        Output format.
    dpi : int
        Dots per inch (raster formats).
    transparent : bool
        Transparent background for raster formats.
    bbox_inches : str
        Passed to savefig for tight layout.
    convert_to_data_uri : bool
        If True, wraps the base64 string in a data: URI.

    Returns
    -------
    str
        Base64-encoded image string, optionally wrapped in a data: URI.
    """
    import matplotlib.pyplot as plt

    if fig is None:
        logger.debug(
            "mpl_fig_to_base64: No figure provided; using current figure via plt.gcf()."
        )
        fig = plt.gcf()
    else:
        logger.debug("mpl_fig_to_base64: Using provided figure id=%s", id(fig))

    try:
        n_axes = len(fig.axes)
    except Exception:  # pragma: no cover - defensive
        n_axes = -1
    if n_axes >= 0:
        logger.debug(
            "mpl_fig_to_base64: Figure id=%s has %d axes; fmt=%s dpi=%s transparent=%s bbox=%s size_in=(%.2f, %.2f)",
            id(fig),
            n_axes,
            fmt,
            dpi,
            transparent,
            bbox_inches,
            *fig.get_size_inches(),
        )

    fig.canvas.draw()
    buf = io.BytesIO()
    save_kwargs = dict(format=fmt)
    if fmt in ("png", "jpg", "jpeg"):
        save_kwargs.update(dpi=dpi, transparent=transparent, bbox_inches=bbox_inches)

    fig.savefig(buf, **save_kwargs)
    logger.debug(
        "mpl_fig_to_base64: Saved figure to buffer (fmt=%s, params=%s)",
        fmt,
        save_kwargs,
    )
    buf.seek(0)
    raw = buf.read()
    raw_len = len(raw)
    logger.debug("mpl_fig_to_base64: Raw image bytes length=%d", raw_len)
    b64: str = base64.b64encode(raw).decode("utf-8")
    buf.close()
    logger.info(
        "mpl_fig_to_base64: Encoded figure id=%s to base64 (chars=%d, fmt=%s)",
        id(fig),
        len(b64),
        fmt,
    )
    if not convert_to_data_uri:
        logger.debug(
            "mpl_fig_to_base64: Returning raw base64 string without data URI conversion."
        )
        return b64
    logger.debug(
        "mpl_fig_to_base64: Converting base64 to data URI (fmt=%s, chars=%d)",
        fmt,
        len(b64),
    )
    return to_data_uri(b64, fmt)


def mpl_axes_to_base64(ax: "matplotlib.axes.Axes", **kwargs) -> str:
    """
    Convert an Axes' parent Figure to base64.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes whose figure will be converted.
    kwargs :
        Forwarded to mpl_fig_to_base64.
    """
    logger.debug(
        "mpl_axes_to_base64: Converting axes id=%s (figure id=%s) with kwargs=%s",
        id(ax),
        id(ax.figure),
        kwargs,
    )
    return mpl_fig_to_data_uri(ax.figure, **kwargs)


_MIME_MAP: dict[str, str] = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "svg": "image/svg+xml",
    "pdf": "application/pdf",
}


def to_data_uri(b64: str, fmt: str = "png") -> str:
    """
    Wrap a base64 string in a data: URI.

    Parameters
    ----------
    b64 : str
        Base64 payload (no data: prefix).
    fmt : str
        Media format extension.
    """
    mime = _MIME_MAP.get(fmt.lower(), "application/octet-stream")
    preview = b64[:32] + ("..." if len(b64) > 32 else "")
    logger.debug(
        "to_data_uri: Building data URI (fmt=%s mime=%s base64_preview=%s total_chars=%d)",
        fmt,
        mime,
        preview,
        len(b64),
    )
    return f"data:{mime};base64,{b64}"
