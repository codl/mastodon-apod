ARG python_version=3.10
FROM python:$python_version as common

WORKDIR /app

COPY ci-requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip/http \
    pip install -r ci-requirements.txt

FROM common as test

COPY requirements.txt dev-requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip/http \
    pip-sync requirements.txt dev-requirements.txt
COPY apod.py tests/ ./
CMD ["python", "-m", "pytest"]

FROM common as bot

# Ensure running user can write to log file
RUN touch apod.log
RUN chmod 666 apod.log

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip/http \
    pip-sync requirements.txt

COPY apod.py ./
RUN python -m py_compile apod.py

CMD ["ananas", "config/ananas.cfg"]
