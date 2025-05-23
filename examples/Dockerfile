FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps for faiss
RUN apt-get update && apt-get install -y --no-install-recommends build-essential wget && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --upgrade pip \
    && pip install .[all]

CMD ["python", "-m", "greeum.cli", "--help"] 