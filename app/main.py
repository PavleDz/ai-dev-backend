from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from app.app import setup_app
from app.config.settings import DBSettings, Settings
from app.utils.di import add_to_di_container
from app.utils.logging import set_up_logging

set_up_logging()

env_path = Path(".env")
load_dotenv(dotenv_path=env_path)

settings = Settings()
add_to_di_container(Settings, settings)
add_to_di_container(DBSettings, settings)

app = setup_app()
