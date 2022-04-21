ARG python_version=3.10
FROM python:$python_version as common

RUN pip install -U --no-cache-dir pip pipenv

WORKDIR /app

# Ensure running user can write to log file
RUN touch apod.log
RUN chmod 666 apod.log

COPY Pipfile Pipfile.lock ./
RUN pipenv sync --system


FROM common as test

RUN pipenv sync -d --system
COPY apod.py tests/ ./
CMD ["python", "-m", "pytest"]


FROM common as bot

COPY apod.py ./
RUN python -m py_compile apod.py

CMD ["ananas", "config/ananas.cfg"]
