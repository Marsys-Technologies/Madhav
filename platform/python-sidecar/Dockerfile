FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ libgl1 libglib2.0-0 curl && rm -rf /var/lib/apt/lists/*
ENV QT_QPA_PLATFORM=offscreen

# Swiss Ephemeris data files — bundled from GCS (L0FR step 2)
# F-012 fix: added size guards to detect corrupt/truncated downloads.
# Actual GCS sizes (gs://madhav-ephemeris/se1, measured 2026-07-02):
#   sepl_18.se1 = 484KB, semo_18.se1 = 1.24MB, seas_18.se1 = 218KB
# Thresholds set to 80% of actual to catch 403/truncation while matching real files.
# A 403/XML error body is <10KB and would silently corrupt the SE1 binary file.
RUN mkdir -p /app/ephe
RUN set -e; \
    GCS_BASE="https://storage.googleapis.com/madhav-ephemeris/se1"; \
    download_and_verify() { \
      local url="$1" dest="$2" min_bytes="$3"; \
      curl -sSL --fail -o "$dest" "$url" || { echo "FATAL: download failed: $url"; exit 1; }; \
      actual=$(stat -c%s "$dest" 2>/dev/null || stat -f%z "$dest"); \
      if [ "$actual" -lt "$min_bytes" ]; then \
        echo "FATAL: $dest is too small ($actual bytes < $min_bytes) — download corrupt or 403"; \
        exit 1; \
      fi; \
    }; \
    download_and_verify "$GCS_BASE/sepl_18.se1"   /app/ephe/sepl_18.se1   400000; \
    download_and_verify "$GCS_BASE/semo_18.se1"   /app/ephe/semo_18.se1  1048576; \
    download_and_verify "$GCS_BASE/seas_18.se1"   /app/ephe/seas_18.se1   180000; \
    download_and_verify "$GCS_BASE/sefstars.txt"  /app/ephe/sefstars.txt    1024; \
    download_and_verify "$GCS_BASE/seleapsec.txt" /app/ephe/seleapsec.txt   1024; \
    echo "All ephemeris files downloaded and size-verified."
ENV SWE_EPHE_PATH=/app/ephe
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Build context widened to ./platform (was ./platform/python-sidecar, see
# deploy.yml) so this image can also reach the sibling platform/scripts/temporal
# package. Fix for #2096: services/ka_graha_sancara/engine.py's live-compute
# path (PATH-B) locates `temporal.compute_transits` via a 4-parents-up walk
# from its own file, matching the real repo layout where python-sidecar/ sits
# one level below platform/scripts/. WORKDIR is nested one level deeper here
# (/app/python-sidecar, not /app) so that identical 4-parents-up arithmetic
# lands on /app/scripts/temporal inside the container too -- no engine.py
# change needed. main.py and platform/python-sidecar's own local scripts/
# folder land at /app/python-sidecar/... exactly as before, just under the
# new prefix; CMD's cwd (this WORKDIR) is unaffected either way.
WORKDIR /app/python-sidecar
COPY python-sidecar/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY python-sidecar/ .
COPY scripts/temporal/ /app/scripts/temporal/
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
