#!/usr/bin/env bash

set -eou pipefail

poetry run migrate
exec poetry run fastapi run app/main.py
