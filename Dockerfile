# Use the official Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone the repo
RUN git clone https://github.com/zaidmukaddam/youtube-api-server.git .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose the port (Hugging Face expects 7860)
EXPOSE 7860

# Run the FastAPI server (assuming app is in `main.py`)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]