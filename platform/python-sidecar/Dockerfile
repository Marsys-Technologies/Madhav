FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ libgl1 libglib2.0-0 curl && rm -rf /var/lib/apt/lists/*
ENV QT_QPA_PLATFORM=offscreen

# Swiss Ephemeris data files — bundled from GCS. Fail the build if any file is missing
# or zero-byte (do NOT '|| true' — a broken ephemeris ships a silently-wrong engine).
RUN set -euo pipefail; \
    mkdir -p /app/ephe; \
    for f in sepl_18.se1 semo_18.se1 seas_18.se1 sefstars.txt seleapsec.txt; do \
      curl -fSL -o "/app/ephe/$f" "https://storage.googleapis.com/madhav-ephemeris/se1/$f"; \
      test -s "/app/ephe/$f" || { echo "FATAL: /app/ephe/$f missing or empty"; exit 1; }; \
    done
ENV SWE_EPHE_PATH=/app/ephe

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
