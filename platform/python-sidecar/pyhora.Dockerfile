FROM python:3.11-slim

# L0FR Step 3 — PyHora/PyJHora sidecar with Swiss Ephemeris bundled
LABEL org.opencontainers.image.title="marsys-pyhora"
LABEL org.opencontainers.image.description="MARSYS-JIS PyJHora compute sidecar with Swiss Ephemeris"

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ libpq-dev curl git && rm -rf /var/lib/apt/lists/*

# Swiss Ephemeris data files — bundled from GCS
RUN mkdir -p /app/ephe
RUN curl -sSL -o /app/ephe/sepl_18.se1 "https://storage.googleapis.com/madhav-ephemeris/se1/sepl_18.se1" 2>/dev/null || true
RUN curl -sSL -o /app/ephe/semo_18.se1 "https://storage.googleapis.com/madhav-ephemeris/se1/semo_18.se1" 2>/dev/null || true
RUN curl -sSL -o /app/ephe/seas_18.se1 "https://storage.googleapis.com/madhav-ephemeris/se1/seas_18.se1" 2>/dev/null || true
RUN curl -sSL -o /app/ephe/sefstars.txt "https://storage.googleapis.com/madhav-ephemeris/se1/sefstars.txt" 2>/dev/null || true
RUN curl -sSL -o /app/ephe/seleapsec.txt "https://storage.googleapis.com/madhav-ephemeris/se1/seleapsec.txt" 2>/dev/null || true
ENV SWE_EPHE_PATH=/app/ephe

# PyJHora — Jyotish computation library with swisseph backend
RUN pip install --no-cache-dir pyjhora || \
    pip install --no-cache-dir git+https://github.com/naturalstupid/PyJHora.git@main

# Additional dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyjhora_adapter/ ./pyjhora_adapter/
COPY brahmagyan/ ./brahmagyan/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8001
CMD ["uvicorn", "pyjhora_adapter.main:app", "--host", "0.0.0.0", "--port", "8001"]
