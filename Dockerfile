ARG python_version=3.12

FROM alpine:3.19.1 as uv

RUN apk add --no-cache curl
RUN curl --location --silent "https://github.com/astral-sh/uv/releases/download/0.1.24/uv-x86_64-unknown-linux-musl.tar.gz" | gunzip | tar x
RUN install uv-x86_64-unknown-linux-musl/uv /


FROM python:$python_version as test

ENV UV_CACHE_DIR=/var/cache/uv
COPY --from=uv /uv /bin/uv

COPY requirements.txt dev-requirements.txt ./
RUN --mount=type=cache,target=/var/cache/uv \
	uv pip sync --system requirements.txt dev-requirements.txt
COPY pyproject.toml .
COPY src/ ./src/
COPY tests/ ./tests/
RUN --mount=type=cache,target=/var/cache/uv \
	uv pip install --system .
CMD ["python", "-m", "pytest"]


FROM python:$python_version as bot

ENV UV_CACHE_DIR=/var/cache/uv
COPY --from=uv /uv /bin/uv

# Ensure running user can write to log file
RUN touch apod.log
RUN chmod 666 apod.log

COPY requirements.txt ./
RUN --mount=type=cache,target=/var/cache/uv \
	uv pip sync --system requirements.txt


COPY pyproject.toml ./
COPY src/ ./src/
RUN --mount=type=cache,target=/var/cache/uv \
	uv pip install --system .

CMD ["ananas", "config/ananas.cfg"]
