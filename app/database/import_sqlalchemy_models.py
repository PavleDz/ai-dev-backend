from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any


def load_all_models(
    directory: str | Path = "app",
    package: str = "app",
    models_folder: str = "models",
) -> list[dict[str, Any]]:
    """Import every `app/<domain>/models/*.py` so SQLAlchemy and alembic see every table.

    Models are never imported from a central place by hand: a new domain only needs a `models/`
    folder to be picked up here (by the app, by alembic autogenerate and by the tests).
    """
    result = []

    for root, dirs, _ in os.walk(directory):
        if models_folder in dirs:
            models_path = Path(root) / models_folder

            for file in models_path.iterdir():
                file_name = file.name
                if file_name.endswith(".py") and file_name != "__init__.py":
                    module_name = file_name[:-3]
                    relative = os.path.relpath(models_path, directory).replace(os.path.sep, ".")
                    full_module_name = f"{package}.{relative}.{module_name}"
                    mdl = importlib.import_module(full_module_name)

                    if "__all__" in mdl.__dict__:
                        names = mdl.__dict__["__all__"]
                    else:
                        names = [x for x in mdl.__dict__ if not x.startswith("_")]

                    result.append({k: getattr(mdl, k) for k in names})

    return result
