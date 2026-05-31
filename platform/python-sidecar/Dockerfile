FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*
ENV QT_QPA_PLATFORM=offscreen
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
