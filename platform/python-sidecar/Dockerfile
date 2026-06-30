FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ libgl1 libglib2.0-0 curl && rm -rf /var/lib/apt/lists/*
ENV QT_QPA_PLATFORM=offscreen

# Swiss Ephemeris data files — bundled from GCS (L0FR step 2)
RUN mkdir -p /app/ephe
RUN curl -sSL -o /app/ephe/sepl_18.se1 "https://storage.googleapis.com/madhav-ephemeris/se1/sepl_18.se1" 2>/dev/null || (echo "FATAL: ephemeris files failed to download"; exit 1)
RUN curl -sSL -o /app/ephe/semo_18.se1 "https://storage.googleapis.com/madhav-ephemeris/se1/semo_18.se1" 2>/dev/null || (echo "FATAL: ephemeris files failed to download"; exit 1)
RUN curl -sSL -o /app/ephe/seas_18.se1 "https://storage.googleapis.com/madhav-ephemeris/se1/seas_18.se1" 2>/dev/null || (echo "FATAL: ephemeris files failed to download"; exit 1)
RUN curl -sSL -o /app/ephe/sefstars.txt "https://storage.googleapis.com/madhav-ephemeris/se1/sefstars.txt" 2>/dev/null || (echo "FATAL: ephemeris files failed to download"; exit 1)
RUN curl -sSL -o /app/ephe/seleapsec.txt "https://storage.googleapis.com/madhav-ephemeris/se1/seleapsec.txt" 2>/dev/null || (echo "FATAL: ephemeris files failed to download"; exit 1)
ENV SWE_EPHE_PATH=/app/ephe
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
