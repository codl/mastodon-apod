ARG python_version=3.9
FROM python:$python_version

WORKDIR /app

# Ensure running user can write to log file
RUN touch apod.log
RUN chmod 666 apod.log

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apod.py .
RUN python -m py_compile apod.py

CMD ["ananas", "config/ananas.cfg"]
