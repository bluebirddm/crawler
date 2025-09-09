FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv first
RUN pip install uv

# Copy the entire project so that package metadata (e.g., README.md) is present
COPY . .

# Sync dependencies and install the project
RUN uv sync --frozen

# Install Playwright browser and dependencies
RUN uv run playwright install chromium
RUN uv run playwright install-deps chromium

ENV PYTHONPATH=/app
ENV PATH=/app/.venv/bin:$PATH

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
