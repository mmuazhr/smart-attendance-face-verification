# Operations Runbook

PresenceGuard is designed for a localhost research/demo environment. This runbook keeps the normal workflow reproducible and makes the security boundary visible.

## First-time setup

```bash
uv sync --extra dev
cp .env.example .env
uv run presenceguard generate-key
uv run presenceguard download-models
uv run presenceguard init-db
```

Put the generated key and a high-entropy local admin token in `.env`. Keep the file outside version control. The models are also ignored; each downloaded file is checked against its recorded SHA-256 before installation.

## Run locally

```bash
uv run presenceguard serve
```

The default address is `http://127.0.0.1:8000`. Binding to a non-loopback address prints a warning and requires a deliberate deployment decision. Do not expose this reference application directly to the internet.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `PRESENCEGUARD_TEMPLATE_KEY` | AES-256-GCM template key | required |
| `PRESENCEGUARD_ADMIN_TOKEN` | Local admin boundary | required for admin routes |
| `PRESENCEGUARD_DATABASE_PATH` | SQLite database location | `data/private/presenceguard.db` |
| `PRESENCEGUARD_MATCH_THRESHOLD` | Stored verification threshold | `0.554712` |
| `PRESENCEGUARD_DUPLICATE_WINDOW_SECONDS` | Duplicate attendance window | `300` |
| `PRESENCEGUARD_MAXIMUM_UPLOAD_BYTES` | Per-image upload limit | `5000000` |

Thresholds are experimental configuration, not universal biometric defaults. Calibrate on representative development data and freeze the policy before evaluating held-out data.

## Logs

The CLI configures compact JSON logs on standard error. A normal request log contains a timestamp, level, event, request ID, HTTP method, route template, status, and duration. It deliberately omits request URLs, query strings, bodies, client IPs, participant IDs, image content, embeddings, and secrets.

Treat logs as operational metadata nevertheless. Do not paste them into public issues if they include local environment details. If a new log event is added, keep it fixed-schema and privacy-safe.

## Data lifecycle

1. Obtain explicit, revocable consent.
2. Capture only the minimum enrollment burst.
3. Process frames in memory and discard them after extraction.
4. Encrypt the template before persistence.
5. Restrict attendance reads to an authorized operator.
6. Delete the participant when the purpose ends; foreign-key cascade removes attendance events.
7. Rotate the key and re-enroll participants if compromise is suspected.

Automatic key rotation, backups, retention scheduling, and institutional identity are not implemented. Keep the database and key under separate access controls for any serious pilot.

## Verification and recovery

The health endpoint reports local processing and no image retention. If a model is missing or corrupt, use `presenceguard download-models` and verify the checksums in `models/README.md`. If the template key is lost, encrypted templates cannot be recovered; re-enrollment is the intended recovery path. If the admin token is lost, change the local `.env` value and restart the process.

## Pre-release checklist

- [ ] Confirm consent and lawful use for every evaluation subject.
- [ ] Confirm `.env`, model binaries, private data, databases, and attendance exports are ignored.
- [ ] Run the full test, lint, type, source-security, and dependency checks.
- [ ] Review threshold calibration and held-out evaluation manifests.
- [ ] Confirm loopback binding or a separately reviewed TLS/authentication boundary.
- [ ] State liveness, fairness, provenance, and population-size limitations in the release notes.
