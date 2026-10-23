FROM python:3.13-bookworm

ARG POETRY_VERSION=2.1.3

ENV PYTHONUNBUFFERED=1

# /.local and /.cache are used for caching by pip/poetry
# We change .venv permissions so it doesn't get created as root during the volume mount.
RUN mkdir /.local /.cache /app /app/.venv  \
    && chown 1000:1000 /.local /.cache /app /app/.venv

RUN pip install poetry==${POETRY_VERSION}

USER 1000

WORKDIR /app
