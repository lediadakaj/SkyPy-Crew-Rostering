FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY skypy/ ./skypy/
COPY tests/ ./tests/
COPY app.py main.py pyproject.toml ./
COPY data/ ./data/

RUN useradd --create-home --shell /bin/bash skypy \
    && chown -R skypy:skypy /app
USER skypy

EXPOSE 5000

CMD ["sh", "-c", "python -m pytest && exec waitress-serve --listen=0.0.0.0:5000 app:app"]
