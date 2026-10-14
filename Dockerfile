
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project package
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "hroneproject.app:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
