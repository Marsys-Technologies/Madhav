# Credentials Rotation Required

The following credentials stored in `platform/.env.local` were accessed during the 2026-06-30 robustness audit. They should be rotated immediately.

## Action items (manual — cannot be automated):

1. **PostgreSQL DB password** (`POSTGRES_PASSWORD` / `DATABASE_URL`) — rotate in Cloud SQL console
2. **Firebase Admin private key** — rotate in Firebase Console → Project Settings → Service Accounts
3. **Anthropic API key** (`sk-ant-api03-*`) — rotate at console.anthropic.com
4. **OpenAI API key** (`sk-proj-*`) — rotate at platform.openai.com
5. **Google Generative AI key** — rotate in GCP Console → APIs & Services → Credentials
6. **DeepSeek API key** — rotate at platform.deepseek.com
7. **NVIDIA NIM API key** — rotate at build.nvidia.com

## After rotation:

Store new credentials in GCP Secret Manager and use `gcloud secrets versions access` to inject them at dev time rather than in `.env.local`.

## Long-term fix:

Use `op run -- npm run dev` (1Password CLI) or `gcloud secrets run` to inject secrets as environment variables without storing them in files.
