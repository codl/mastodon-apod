ARG python_version=3.12.2

FROM python:$python_version as uv

ARG uv_version=0.1.29

RUN wget "https://github.com/astral-sh/uv/releases/download/$uv_version/uv-x86_64-unknown-linux-musl.tar.gz"
RUN wget "https://github.com/astral-sh/uv/releases/download/$uv_version/uv-x86_64-unknown-linux-musl.tar.gz.sha256"
RUN sha256sum --check uv-x86_64-unknown-linux-musl.tar.gz.sha256
RUN tar -xf uv-x86_64-unknown-linux-musl.tar.gz
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
CMD ["python", "-m", "pytest", "tests"]


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
