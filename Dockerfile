ARG python_version=3.9
FROM python:$python_version

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apod.py .
RUN python -m py_compile apod.py

CMD ["ananas", "config/ananas.cfg"]