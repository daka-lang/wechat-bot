FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir flask==2.3.0 requests==2.31.0

COPY app.py .

CMD ["python", "app.py"]
