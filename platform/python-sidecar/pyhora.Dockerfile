FROM python:3.11-slim
# PyHora (PyJHora) sidecar — L0FR Stream A (Step 3)
# Wraps PyJHora (Swiss Ephemeris Python binding) for Jyotish computation
# .se1 files bundled from GCS at build time; runtime path via SWE_EPHE_PATH

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ libgl1 libglib2.0-0 libx11-6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

ENV QT_QPA_PLATFORM=offscreen

# Install PyJHora + dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pyjhora || \
    pip install --no-cache-dir "git+https://github.com/naturalstupid/PyJHora.git@main"

# Swiss Ephemeris .se1 files — bundled from GCS at build time
RUN mkdir -p /app/ephe && \
    (command -v gsutil && gsutil -m cp gs://madhav-ephemeris/se1/*.se1 /app/ephe/ 2>/dev/null && \
     gsutil -m cp gs://madhav-ephemeris/se1/*.txt /app/ephe/ 2>/dev/null) || \
    echo "WARNING: gsutil not available — ephemeris not bundled; set SWE_EPHE_PATH at runtime"

ENV SWE_EPHE_PATH=/app/ephe

# PyHora reads SWE_EPHE_PATH for its swisseph backend
ENV PYJHORA_EPHE_PATH=/app/ephe

COPY . .
EXPOSE 8001
CMD ["uvicorn", "pyhora_server:app", "--host", "0.0.0.0", "--port", "8001"]
