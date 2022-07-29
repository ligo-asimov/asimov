from contextlib import contextmanager
from pathlib import Path
from asimov import logger
import os

@contextmanager
def set_directory(path: (Path, str)):
    """
    Change to a different directory for the duration of the context.

    Args:
        path (Path): The path to the cwd

    Yields:
        None
    """

    origin = Path().absolute()
    try:
        #print(f"{origin} → {path}")
        logger.info(f"Working temporarily in {path}")
        os.chdir(path)
        yield
    finally:
        #print(f"{path} → {origin}")
        os.chdir(origin)

