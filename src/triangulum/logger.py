import logging
from datetime import datetime

from rich.logging import RichHandler


def init_logger(
    log_level_file: str = "INFO", log_level_console: str = "INFO", plain: bool = False
) -> None:
    """
    Initialize the logger for Triangulum.
    """
    format = "%(asctime)s %(levelname)s %(name)s - %(message)s"
    formatter = logging.Formatter(format)

    logger = logging.getLogger()  # root
    logging.basicConfig(
        filename=datetime.now().strftime(".triangulum/logs/triangulum_%Y-%m-%d.log"),
        format=format,
        level=log_level_file,
    )

    if plain:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level_console)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    else:  # use rich logger
        console_handler = RichHandler(level=log_level_console)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.info(
        f"initialized  logger with log_level_file = '{log_level_file}', log_level_console = '{log_level_console}'"
    )
