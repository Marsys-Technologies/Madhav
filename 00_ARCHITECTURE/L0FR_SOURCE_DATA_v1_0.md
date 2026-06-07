---
artifact: L0FR_SOURCE_DATA_v1_0.md
canonical_id: L0FR_SOURCE_DATA
version: 1.0
status: CURRENT
authored_by: Cowork 2026-06-07
---

# L0 Foundation Rebuild — Source Data

All URLs, version IDs, edition references, and configuration values the swarm needs. The swarm does NOT need to ask native anything.

## Swiss Ephemeris .se1 files

**Source:** Astrodienst public archive `https://www.astro.com/ftp/swisseph/ephe/`

**Required files** (download all):
- Planets 1800-2399: `sepl_18.se1`
- Planets -1300 to -300 BCE: `seplm132.se1`, `seplm84.se1` (for historical edge cases)
- Moon 1800-2399: `semo_18.se1`
- Moon historical: `semom84.se1`
- Asteroids 1800-2399: `seas_18.se1`
- Asteroids historical: `seasm84.se1`
- Fixed stars: `sefstars.txt`
- Leap seconds: `seleapsec.txt`
- Asteroid names: `seasnam.txt`

**Download command** (for Stream A):
```bash
mkdir -p /tmp/se1
cd /tmp/se1
BASE_URL="https://www.astro.com/ftp/swisseph/ephe"
for f in sepl_18.se1 seplm132.se1 seplm84.se1 semo_18.se1 semom84.se1 seas_18.se1 seasm84.se1 sefstars.txt seleapsec.txt seasnam.txt; do
  curl -sSL -o "$f" "$BASE_URL/$f" && echo "$f: OK" || echo "$f: FAIL"
done
sha256sum *.se1 *.txt > MANIFEST.sha256
```

**GCS upload** (Stream A):
```bash
gsutil mb -p madhav-astrology -l asia-south1 gs://madhav-ephemeris/ 2>&1 || true
gsutil -m cp /tmp/se1/* gs://madhav-ephemeris/se1/
```

**Bundle pattern** (orchestrator + python-sidecar + pyhora-sidecar Dockerfiles):
```dockerfile
RUN gsutil -m cp gs://madhav-ephemeris/se1/* /app/ephe/ 2>/dev/null || true
# OR for build-time bundling (if gsutil not in build context):
COPY ephe/ /app/ephe/
ENV SWE_EPHE_PATH=/app/ephe
```

In Python:
```python
import swisseph as swe
swe.set_ephe_path('/app/ephe')
```

## Classical text editions — 15 texts

For each text: edition, source URL (Internet Archive when public domain), and manual-upload-required flag.

### Tier 1 (full ingestion, ~8,000 verses combined)

| # | Text | Edition | Source URL | Manual Upload? |
|---|---|---|---|---|
| 1 | Brihat Parashara Hora Shastra | R. Santhanam, Ranjan Publications | `https://archive.org/details/brihat-parashara-hora-shastra-english-by-santhanam` | NO (public domain) |
| 2 | Phaladeepika | S.S. Sareen | `https://archive.org/details/phaladeepika-sareen` | NO (public domain) |
| 3 | Jataka Parijata | G.S. Kapoor | `https://archive.org/details/jataka-parijata-kapoor` | NO |
| 4 | Uttara Kalamrita | R. Santhanam | `https://archive.org/details/uttara-kalamrita-santhanam` | NO |
| 5 | Brihat Jataka (Varahamihira) | B. Suryanarain Rao | `https://archive.org/details/varahamihira-brihat-jataka-suryanarain-rao` | NO |
| 6 | Saravali (Kalyana Varma) | R. Santhanam | `https://archive.org/details/saravali-kalyana-varma-santhanam` | NO |
| 7 | Hora Sara (Prithuyasas) | J.N. Bhasin | `https://archive.org/details/hora-sara-bhasin` | NO (if available; else flag) |
| 8 | Jaimini Sūtram | Sanjay Rath, Sagittarius Publications | **MANUAL UPLOAD** — Sanjay Rath publications not on Internet Archive | YES |

### Tier 2 (full ingestion, ~4,000 verses combined)

| # | Text | Edition | Source URL | Manual Upload? |
|---|---|---|---|---|
| 9 | Sarvartha Chintamani | J.N. Bhasin | `https://archive.org/details/sarvartha-chintamani-bhasin` | NO (verify) |
| 10 | Tajaka Neelakanthi | Sanjay Rath | **MANUAL UPLOAD** | YES |
| 11 | Brihat Samhita | M. Ramakrishna Bhat (2 vols) | `https://archive.org/details/brihat-samhita-bhat-vol-1` + vol-2 | NO |

### Tier 3 (selective extracts)

| # | Text | Edition | Source URL | Manual Upload? |
|---|---|---|---|---|
| 12 | Yavana Jataka | David Pingree, Harvard Oriental Series | **MANUAL UPLOAD** — academic edition | YES |
| 13 | Bhrigu Samhita | Selective extracts | **MANUAL UPLOAD** — multiple sources, native chooses extracts | YES |
| 14 | Muhurta Chintamani | G.C. Sharma | `https://archive.org/details/muhurta-chintamani-sharma` | NO (verify) |
| 15 | Lal Kitab | B.M. Goel | `https://archive.org/details/lal-kitab-goel` | NO |

### Stream C protocol for manual uploads

When Stream C reaches a manual-upload-required text, it MUST NOT block the autonomous wave:
1. Skip the text; log to `/tmp/l0fr_manual_upload_pending.txt` with required edition + filename
2. Continue with next text
3. At Stream C completion, emit list of pending manual uploads to Smṛti for native action (post-seal)
4. The 8 auto-downloadable texts alone exceed the AC floor of 6,000 chunks; manual-upload texts can land post-seal as a delta

## Vertex AI models

| Use | Model ID | API |
|---|---|---|
| Bulk extraction (sūtravali pass 1) | `gemini-2.5-flash` | Vertex AI |
| Quality validation (sūtravali pass 2) | `gemini-2.5-flash` | Vertex AI |
| Lower-cost work | `gemini-2.5-flash-lite` | Vertex AI |
| Vimarśaka reviewers | `gemini-2.5-pro` | Vertex AI |
| Embeddings | `text-multilingual-embedding-002` | Vertex AI |
| Intent classifier | `gemini-2.5-flash-lite` | Vertex AI |

**Vertex AI auth:** orchestrator runs as `brahma-swarm-bot@madhav-astrology.iam.gserviceaccount.com` (per memory `brahma-pipeline-orchestrator`). Service account already has `aiplatform.user` role.

**Project:** `madhav-astrology`. **Region:** `asia-south1` for Vertex AI inference.

## MCP OAuth 2.0 specification

**Spec reference:** Model Context Protocol authorization spec at `https://modelcontextprotocol.io/specification/server/authorization`

**Required endpoints** for ChatGPT MCP support:
- `POST /mcp/oauth/authorize` — initiates OAuth flow; redirects to Firebase auth
- `POST /mcp/oauth/token` — exchanges authorization code for access token; supports `grant_type=authorization_code` AND `grant_type=client_credentials`
- `POST /mcp/oauth/refresh` — refreshes access token
- `GET /mcp/.well-known/oauth-authorization-server` — OAuth discovery metadata
- `GET /mcp/.well-known/openid-configuration` — for ChatGPT discovery

**Token lifetime:** access_token 1 hour; refresh_token 30 days.

**Scopes:** `mcp:tools mcp:resources mcp:prompts` (no audience tier scopes).

**Underlying identity:** Firebase Authentication (existing). The OAuth layer is a protocol bridge — Firebase is the authority.

**ChatGPT configuration** (operator action post-seal):
1. ChatGPT Settings → Connectors → Add custom MCP server
2. URL: `https://madhav.marsys.in/mcp`
3. OAuth provider: custom; authorization endpoint as above
4. Test: invoke a tool; expect 200 with result

## PyHora / PyJHora

**Source:** `https://github.com/naturalstupid/PyJHora`

**Install** (in python-sidecar / pyhora-sidecar Dockerfile):
```dockerfile
RUN pip install pyjhora
# OR if not on PyPI:
RUN pip install git+https://github.com/naturalstupid/PyJHora.git@main
```

**Configure ephemeris path:**
```python
from jhora.const import _SWE_DIR
import os
os.environ['SWE_EPHE_PATH'] = '/app/ephe'
# PyHora reads SWE_EPHE_PATH for its swisseph backend
```

**Smoke test:**
```python
from jhora import const
from jhora.panchanga import drik
# Native birth: 1984-02-05, 10:43 IST, Bhubaneswar (85.83°E, 20.27°N)
jd = drik.julian_day_number((1984, 2, 5), (10, 43, 0)) - 5.5/24  # UT
positions = drik.dasavarga_from_planet_positions(jd, place_as_tuple=(85.83, 20.27, 5.5))
# Expect Sun in Capricorn ~21°48' (matches Stream B's ephemeris)
```

## Tantric remedy source list (acceptable)

For Stream F's tantric careful-inclusion gate, the following Sanskrit sources are acceptable for sourcing tantric remedies. Tantric remedies NOT from these sources are auto-rejected:

| Source | Era | Why acceptable |
|---|---|---|
| Mantra Mahodadhi (Mahidhara) | 16th c. | Compendium; widely accepted classical |
| Mantra Mahārṇava | 17th c. | Authoritative tantric mantra compendium |
| Tantrasāra (Krishnananda Agamavagisha) | 16th c. | Vaiṣṇava tantric compendium |
| Śaktisaṅgama Tantra | 13th-15th c. | Śākta tradition; vetted |
| Dasamahavidya Sadhana (multiple compilers) | various | Individual goddess sadhanas; per-deity sourcing |
| BPHS upayas chapter | classical | Already in our corpus |
| Phaladeepika upayas chapter | classical | Already in our corpus |

Tantric remedies from late-syncretic compendiums (post-1800), modern compilations without classical traceback, or oral/palm-leaf-only sources WITHOUT verifiable Sanskrit attribution → reject; flag to `remedy_review_queue`.

## Cockpit smoke test instructions (Vimarśaka-Z)

For the end-to-end smoke at seal time:

```bash
# Native chart_id (already in prod):
CHART_ID="482012f1-710e-4a25-994a-93821f5871aa"

# Trigger global build via cockpit API:
curl -s -X POST https://madhav.marsys.in/api/cockpit/runs \
  -b "__session=$(cat /tmp/native_session_cookie)" \
  -H "Content-Type: application/json" \
  -d "{\"scope\":\"global\",\"action\":\"build\",\"plan\":[...all L0 brahmagyan asset_ids...]}" \
  | jq

# Wait for completion (poll every 30s, max 30 min):
while true; do
  STATE=$(psql_prod -At -c "SELECT state FROM build_runs WHERE chart_id IS NULL ORDER BY created_at DESC LIMIT 1")
  [ "$STATE" = "completed" ] && break
  [ "$STATE" = "failed" ] && { echo "FAILED"; exit 1; }
  sleep 30
done

# Verify L0 assets all lit:
psql_prod -c "SELECT asset_id, state FROM asset_throughput WHERE layer='brahmagyan'"
```

## Budget per stream (canonical)

| Stream | Tier-3 cap |
|---|---|
| A | $500 |
| B | $150 |
| C | $600 |
| D | $250 |
| E | $250 |
| F | $350 |
| G | $150 |
| **Per-stream max** | $5,000 absolute |
| **Total wave max** | $10,000 absolute |

Soft target: $90-150 across all streams.

## Native chart context (for spot-checks)

```yaml
chart_id: "482012f1-710e-4a25-994a-93821f5871aa"
subject_name: "Abhisek Mohanty"
birth_date: "1984-02-05"
birth_time_ist: "10:43:00"
birth_location:
  city: "Bhubaneswar"
  state: "Odisha"
  country: "India"
  lat: 20.2735
  lon: 85.8334
  tz_offset: +5.5
expected_sun_position: "Capricorn 21°48' (Lahiri)"
expected_moon_nakshatra: "Purva Bhadrapada Pada 1"
expected_tithi: "Shukla Tritiya"
expected_vara: "Ravivara"
```

Any astrological spot-check in Vimarśaka-A or Vimarśaka-Z uses these expected values.
