FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/data /app/credentials

COPY src/ ./src/
COPY tests/ ./tests/
COPY tools/ ./tools/
COPY docs/ ./docs/

ENV PYTHONPATH=/app/src:/app

CMD ["python", "src/bot.py"]
