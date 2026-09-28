import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


root_dir = next((dir for dir in Path(__file__).resolve().parents if dir.joinpath('pyproject.toml').exists()), None)
