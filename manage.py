#!/usr/bin/env python
"""Management commands: `python manage.py <command>` or the `poetry run <command>` shortcuts."""

from __future__ import annotations

import sys
from argparse import ArgumentParser
from logging import INFO, basicConfig
from pathlib import Path
from typing import Any, ClassVar

from dotenv import load_dotenv

from app.config.settings import DBSettings, Settings
from app.database.import_sqlalchemy_models import load_all_models
from app.utils import logging
from app.utils.di import add_to_di_container

logger = logging.getLogger(__name__)


class BaseCommand:
    name: ClassVar[str]
    description: ClassVar[str] = ""

    def add_arguments(self, parser: ArgumentParser) -> None:
        pass

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """The actual logic of the command. kwargs are the arguments added in add_arguments()."""
        raise NotImplementedError("subclasses of BaseCommand must provide a handle() method")


class CommandRunner:
    commands: list[type[BaseCommand]]
    description: str

    def __init__(self, commands: list[type[BaseCommand]], description: str):
        self.commands = commands
        self.description = description

    def execute(self, args: list[str]) -> None:
        parser = ArgumentParser(description=self.description)
        subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)
        for command_class in self.commands:
            command_name = getattr(command_class, "name", command_class.__name__.lower())
            subparser = subparsers.add_parser(command_name, description=command_class.description)
            command = command_class()
            command.add_arguments(subparser)
            subparser.set_defaults(func=command.handle)

        parsed_args = parser.parse_args(args)
        subcommand_args = vars(parsed_args).copy()
        subcommand_args.pop("command", None)
        subcommand_args.pop("func", None)
        parsed_args.func(**subcommand_args)


class RunServer(BaseCommand):
    name = "runserver"
    description = "run dev server"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("-p", "--port", dest="port", type=int, default=8000, help="port")
        parser.add_argument("-H", "--host", dest="host", type=str, default="127.0.0.1", help="host")

    def handle(self, port: int, host: str) -> None:
        import uvicorn

        uvicorn.run("app.main:app", reload=True, port=port, host=host)


class Test(BaseCommand):
    name = "test"
    description = "run tests"

    def handle(self) -> None:
        import pytest

        sys.exit(pytest.main(["tests", *sys.argv[2:]]))


class Typecheck(BaseCommand):
    name = "typecheck"
    description = "typecheck project"

    def handle(self) -> None:
        from mypy.api import run as run_mypy

        stdout, stderr, status = run_mypy(["."])
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)
        sys.exit(status)


class Lint(BaseCommand):
    name = "lint"
    description = "ruff check + black check"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--fix", action="store_true", help="fix what can be fixed and format")

    def handle(self, fix: bool = False) -> None:
        import subprocess

        ruff = ["ruff", "check", "."] + (["--fix"] if fix else [])
        black = ["black", "."] + ([] if fix else ["--check"])
        status = subprocess.run(ruff, check=False).returncode
        status |= subprocess.run(black, check=False).returncode
        sys.exit(status)


class MakeMigrations(BaseCommand):
    name = "makemigrations"
    description = "make migrations"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("name", type=str, help="name of migration")
        parser.add_argument("--empty", action="store_true", help="generate empty migration")

    def handle(self, name: str, empty: bool = False) -> None:
        import alembic.config

        if not empty:
            alembic_args = ["revision", "--autogenerate", "-m", name]
        else:
            alembic_args = ["revision", "-m", name]
        alembic.config.main(argv=alembic_args)


class Migrate(BaseCommand):
    name = "migrate"
    description = "run migrations"

    def handle(self) -> None:
        import alembic.config

        alembic.config.main(argv=["upgrade", "head"])


class Seed(BaseCommand):
    name = "seed"
    description = "create the demo user and demo listings (idempotent)"

    def handle(self) -> None:
        from app.seed import seed

        configure_settings()
        seed()


def configure_settings() -> None:
    basicConfig(level=INFO)

    env_path = Path(".env")
    load_dotenv(dotenv_path=env_path)

    settings = Settings()
    add_to_di_container(Settings, settings)
    add_to_di_container(DBSettings, settings)

    load_all_models()


def main(args: list[str]) -> None:
    CommandRunner(
        commands=[RunServer, Test, Typecheck, Lint, MakeMigrations, Migrate, Seed],
        description="Backend management commands",
    ).execute(args)


def poetry_start() -> None:
    """Launched with `poetry run start` at root level"""
    main(["runserver", *sys.argv[1:]])


def poetry_test() -> None:
    """Launched with `poetry run test` at root level"""
    main(["test"])


def poetry_typecheck() -> None:
    """Launched with `poetry run typecheck` at root level"""
    main(["typecheck", *sys.argv[1:]])


def poetry_lint() -> None:
    """Launched with `poetry run lint` at root level"""
    main(["lint", *sys.argv[1:]])


def poetry_makemigrations() -> None:
    """Launched with `poetry run makemigrations "<name>"` at root level"""
    main(["makemigrations", *sys.argv[1:]])


def poetry_migrate() -> None:
    """Launched with `poetry run migrate` at root level"""
    main(["migrate", *sys.argv[1:]])


def poetry_seed() -> None:
    """Launched with `poetry run seed` at root level"""
    main(["seed", *sys.argv[1:]])


if __name__ == "__main__":
    main(sys.argv[1:])
