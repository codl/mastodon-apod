ARG python_version=3.12.5

FROM python:$python_version as uv

ARG uv_version=0.4.4

RUN wget "https://github.com/astral-sh/uv/releases/download/$uv_version/uv-x86_64-unknown-linux-musl.tar.gz"
RUN wget "https://github.com/astral-sh/uv/releases/download/$uv_version/uv-x86_64-unknown-linux-musl.tar.gz.sha256"
RUN sha256sum --check uv-x86_64-unknown-linux-musl.tar.gz.sha256
RUN tar -xf uv-x86_64-unknown-linux-musl.tar.gz
RUN install uv-x86_64-unknown-linux-musl/uv /


FROM python:$python_version as test

RUN mkdir /app
WORKDIR /app

ENV PATH=/app/.venv/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

ENV UV_CACHE_DIR=/var/cache/uv
COPY --from=uv /uv /bin/uv
RUN uv venv

COPY uv.lock pyproject.toml .
COPY src/ ./src/
COPY tests/ ./tests/
RUN --mount=type=cache,target=/var/cache/uv \
	uv sync --all-extras --frozen
CMD ["python", "-m", "pytest"]


FROM python:$python_version as bot

RUN mkdir /app
WORKDIR /app

ENV PATH=/app/venv/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/app/venv/

ENV UV_CACHE_DIR=/var/cache/uv
COPY --from=uv /uv /bin/uv
RUN uv venv venv

# Ensure running user can write to log file
RUN touch apod.log
RUN chmod 666 apod.log

COPY uv.lock pyproject.toml .
COPY src/ ./src/
RUN --mount=type=cache,target=/var/cache/uv \
	uv sync --no-dev --frozen

CMD ananas config/ananas.cfg
