FROM python:3.11-slim

WORKDIR /app

# Install deploy dependencies (no Whisper/PyTorch — keeps image small)
COPY requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt

# Copy application code
COPY lyricflow/ lyricflow/
COPY tests/ tests/

# Create uploads directory
RUN mkdir -p lyricflow/static/uploads

EXPOSE 8000

CMD ["uvicorn", "lyricflow.main:app", "--host", "0.0.0.0", "--port", "8000"]
