FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
ENV QT_QPA_PLATFORM=offscreen
# Stream G: Swiss Ephemeris .se1 files path for PyJHora
# Populated at runtime from gs://madhav-ephemeris/se1/ (or COPY ephe/ /app/ephe/)
ENV SWE_EPHE_PATH=/app/ephe
RUN mkdir -p /app/ephe
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
