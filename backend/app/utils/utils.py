from dotenv import load_dotenv
import logging
import os

load_dotenv()

END = "\033[0m"
BOLD = "\033[1m"
BROWN = "\033[0;33m"
ITALIC = "\033[3m"
LOG_LEVEL = os.getenv("LOG_LEVEL", "warning").upper()
MATPLOTLIB_COLOR_MODE = os.getenv("MATPLOTLIB_COLOR_MODE", "light").lower()


def set_logger_level_to_all_local(level: int) -> None:
    """Sets the level of all local loggers to the given level.

    Parameters
    ----------
    level : int, optional
        The level to set the loggers to, by default logging.DEBUG.
    """
    level_to_int_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    if isinstance(level, str):
        level = level_to_int_map[level.lower()]

    for _, logger in logging.Logger.manager.loggerDict.items():
        if isinstance(logger, logging.Logger):
            if hasattr(logger, "local"):
                logger.setLevel(level)


def create_simple_logger(
    logger_name: str, level: str = LOG_LEVEL, set_level_to_all_loggers: bool = False
) -> logging.Logger:
    """Creates a simple logger with the given name and level. The logger has a single handler that logs to the console.

    Parameters
    ----------
    logger_name : str
        Name of the logger.
    level : str or int
        Level of the logger. Can be a string or an integer. If a string, it should be one of the following: "debug", "info", "warning", "error", "critical". Default level is read from the environment variable LOG_LEVEL.

    Returns
    -------
    logging.Logger
        The logger object.
    """
    level_to_int_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    if isinstance(level, str):
        level = level_to_int_map[level.lower()]
    logger = logging.getLogger(logger_name)
    logger.local = True
    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # remove any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if set_level_to_all_loggers:
        set_logger_level_to_all_local(level)
    return logger


logger = create_simple_logger(__name__)


def set_publish_matplotlib_template(mode: str = MATPLOTLIB_COLOR_MODE) -> None:
    """Sets the matplotlib template for publication-ready plots."""
    import matplotlib.pyplot as plt

    text_color = "black" if mode == "light" else "white"
    background_color = "white" if mode == "light" else "black"
    grid_color = "#948b72" if mode == "light" else "#666666"

    plt.rcParams.update(
        {
            "font.size": 18,
            "axes.labelcolor": text_color,
            "axes.labelsize": 18,
            "axes.labelweight": "bold",
            "xtick.labelsize": 16,
            "ytick.labelsize": 16,
            "xtick.color": text_color,
            "ytick.color": text_color,
            "axes.grid": True,
            "axes.facecolor": background_color,
            "figure.facecolor": background_color,
            "figure.titlesize": 20,
            "figure.titleweight": "bold",
            "grid.color": grid_color,
            "grid.linewidth": 1,
            "grid.linestyle": "--",
            "axes.edgecolor": text_color,
            "axes.linewidth": 0.5,
            "text.color": text_color,
            "legend.framealpha": 0.8,
            "legend.edgecolor": text_color,
            "legend.facecolor": background_color,
            "legend.labelcolor": text_color,
        }
    )
    logger.info(f"Matplotlib template ready for publication {mode} mode.")
