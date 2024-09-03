ARG python_version=3.12.5

FROM python:$python_version as uv

ARG uv_version=0.4.2

RUN wget "https://github.com/astral-sh/uv/releases/download/$uv_version/uv-x86_64-unknown-linux-musl.tar.gz"
RUN wget "https://github.com/astral-sh/uv/releases/download/$uv_version/uv-x86_64-unknown-linux-musl.tar.gz.sha256"
RUN sha256sum --check uv-x86_64-unknown-linux-musl.tar.gz.sha256
RUN tar -xf uv-x86_64-unknown-linux-musl.tar.gz
RUN install uv-x86_64-unknown-linux-musl/uv /


FROM python:$python_version as test

ENV UV_CACHE_DIR=/var/cache/uv
COPY --from=uv /uv /bin/uv
RUN uv venv /venv
RUN . venv/bin/activate

COPY uv.lock pyproject.toml .
COPY src/ ./src/
COPY tests/ ./tests/
RUN --mount=type=cache,target=/var/cache/uv \
	uv sync --frozen
CMD ["python", "-m", "pytest", "tests"]


FROM python:$python_version as bot

ENV UV_CACHE_DIR=/var/cache/uv
COPY --from=uv /uv /bin/uv
RUN uv venv /venv
RUN . venv/bin/activate

ENV PATH=/venv/bin:$PATH

# Ensure running user can write to log file
RUN touch apod.log
RUN chmod 666 apod.log

COPY uv.lock pyproject.toml .
COPY src/ ./src/
RUN --mount=type=cache,target=/var/cache/uv \
	uv sync --no-dev --frozen

CMD ananas config/ananas.cfg
