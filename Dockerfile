# syntax=docker/dockerfile:1.9
ARG python_version=3.12.6

FROM python:$python_version as build

ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/app

COPY --from=ghcr.io/astral-sh/uv:0.4.15 /uv /bin/uv

COPY pyproject.toml /_lock/
COPY uv.lock /_lock/

RUN --mount=type=cache,target=/root/.cache <<EOT
cd /_lock
uv sync \
    --frozen \
    --no-dev \
    --no-install-project
EOT

COPY pyproject.toml uv.lock /src/
COPY src /src/src
COPY tests /src/tests
RUN --mount=type=cache,target=/root/.cache \
    uv pip install \
        --python=$UV_PROJECT_ENVIRONMENT \
        --no-deps \
        /src


FROM build as test

ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/app

RUN --mount=type=cache,target=/root/.cache <<EOT
cd /_lock
uv sync \
    --frozen \
    --no-install-project \
    --extra test
EOT

RUN --mount=type=cache,target=/root/.cache <<EOT
cd /src
uv pip install \
    --python=$UV_PROJECT_ENVIRONMENT \
    --no-deps \
    .[test]
EOT

ENV PYTHONUNBUFFERED=1
WORKDIR /src

CMD ["/app/bin/python", "-m", "pytest"]


FROM python:$python_version as bot

COPY --from=build /app /app

ENV PATH=/app/bin:$PATH
ENV PYTHONUNBUFFERED=1

RUN umask 111 && touch apod.log

CMD ananas /config/ananas.cfg
