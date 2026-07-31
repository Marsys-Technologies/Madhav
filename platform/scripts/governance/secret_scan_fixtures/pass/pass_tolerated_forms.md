# Seeded pass fixture — every form the scanner is allowed to forgive.

This file MUST NOT trip the scanner. Each block below is a real shape that the
2026-07-30 repo-wide widening surfaced and that was ruled a false positive.
If a future tightening breaks one of these, `--self-test` goes red here first,
before it goes red across the whole tree.

## 1. Local-development default credentials (weak placeholder, <= 16 chars)

    postgresql://postgres:postgres@localhost:5432/amjis_dev
    postgresql://amjis_app:localtest@127.0.0.1:5433/amjis
    PGPASSWORD=testpass
    POSTGRES_PASSWORD=localtest

## 2. GCP Secret Manager bootstrap references (an ID + version, not a value)

Prose form, backtick-wrapped, as it appears in governance docs:
`DB_PASSWORD=amjis-db-password:latest` and the pinned form
`DB_PASSWORD=amjis-db-password:2`.

## 3. gcloud flags naming a Secret Manager secret ID

    gcloud run deploy amjis-web --update-secrets=DB_PASSWORD=amjis-db-password:latest
    terraform apply -var-secret="amjis-db-password"

## 4. Test-only fake OAuth material (weak placeholder, <= 16 chars)

    client_secret: 'mcp_cs_xyz'

## 5. Documentation placeholders

    postgresql://amjis_app:<PASSWORD>@127.0.0.1:5433/amjis
    postgresql://amjis_app:***@127.0.0.1:5433/amjis
    DATABASE_PASSWORD=REPLACE_ME

## 6. Env indirection in every language this repo uses

    db_password = os.environ["DB_PASSWORD"]
    const pw = process.env.DB_PASSWORD
    PGPASSWORD="${PGPASSWORD:?}"
    password: ${{ secrets.DB_PASSWORD }}
