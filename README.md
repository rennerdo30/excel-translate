# Excel Translate

Excel for Mac custom worksheet functions that translate cells using a model running locally in
[LM Studio](https://lmstudio.ai/).

```excel
=XLT.TRANSLATE(A2,"de")
=XLT.TRANSLATE(A2,"en","de")
=XLT.TRANSLATE_RANGE(A2:B10,"fr")
```

Documentation: **https://rennerdo30.github.io/excel-translate**

## What it is

An Office Add-in that registers two custom functions in the `XLT` namespace. Excel loads the add-in
from a small HTTPS host on `https://localhost:3000`, written with nothing but the Python standard
library. That host serves the add-in's static files and proxies translation requests to LM Studio's
OpenAI-compatible local API, using whichever model you have loaded.

## Why

- **Formula-first.** Translation is a cell function that fills down and recalculates like any other
  formula, instead of a button in a task pane.
- **Local.** Text goes to LM Studio on `localhost`. There is no cloud translation service, no account,
  and no API key to obtain.
- **Small.** No bundler, no TypeScript, no Python dependencies. Plain HTML/JS plus one stdlib server.
- **Any model.** Auto-detects the first model LM Studio reports, or pin one with `LM_STUDIO_MODEL`.

## Requirements

- macOS with Excel for Mac supporting the `CustomFunctionsRuntime` 1.1 requirement set
- LM Studio with its local server running and a model loaded
- Docker (default path) or Python 3.12+ to run the host directly
- `openssl` and `security` (both ship with macOS)

## Install

> No TLS certificate is included in this repository, by design. `certs/` is git-ignored and the server
> refuses to start until you generate your own key pair.

### 1. Generate a localhost certificate

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:2048 \
  -keyout certs/localhost-key.pem \
  -out certs/localhost.pem \
  -days 365 -nodes \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
chmod 600 certs/localhost-key.pem
```

### 2. Trust it

```bash
npm run mac:trust-cert
```

`scripts/trust-localhost-cert.sh` runs `security add-trusted-cert -d -r trustRoot -k
~/Library/Keychains/login.keychain-db certs/localhost.pem`. That marks your self-signed certificate as
a trusted root in your login keychain, which is what lets Excel open `https://localhost:3000`. Anything
holding that private key can then impersonate `localhost` for your user, so keep the key to yourself
and remove the trust entry when you are done:

```bash
security delete-certificate -c localhost "$HOME/Library/Keychains/login.keychain-db"
```

### 3. Start the add-in host

```bash
npm run docker:up     # docker compose up --build -d
# or
npm start             # python3 scripts/dev_server.py
```

```bash
curl -k https://localhost:3000/api/health
```

### 4. Start LM Studio's local server

Open the **Developer** tab in LM Studio, start the server, and load a chat/instruct model.

### 5. Sideload the manifest

```bash
npm run install-manifest
```

This copies `manifest.xml` to
`~/Library/Containers/com.microsoft.Excel/Data/Documents/wef/cell-translator-manifest.xml`.

### 6. Register the functions once

Restart Excel, open a workbook, go to **Home → Add-ins**, and launch **Cell Translator** once. That
first launch registers the custom functions for your Excel profile. Then try
`=XLT.TRANSLATE(A1,"de")`.

If you get `#NAME?`: quit Excel, `npm run excel:reset`, `npm run install-manifest`, reopen Excel, and
launch the add-in again. Full checklist in the
[troubleshooting guide](https://rennerdo30.github.io/excel-translate/guides/troubleshooting/).

## Usage

| Formula | Result |
| --- | --- |
| `=XLT.TRANSLATE(text, targetLanguage, [sourceLanguage])` | One translated string |
| `=XLT.TRANSLATE_RANGE(range, targetLanguage, [sourceLanguage])` | A spilled matrix the same shape as the input |

- `sourceLanguage` is optional; blank or `auto` lets the model detect it.
- Empty cells stay empty and are never sent to the model.
- Failures come back as readable `[translation failed: ...]` text rather than `#VALUE!`.
- The server makes **one model call per cell, sequentially**, so large ranges take a while.

## Configuration

All configuration is environment variables read by `scripts/dev_server.py`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `HOST` | `127.0.0.1` | Bind interface (`0.0.0.0` in `docker-compose.yml`) |
| `PORT` | `3000` | Listen port (also hard-coded in `manifest.xml` and `web/functions.json`) |
| `LM_STUDIO_BASE_URL` | `http://127.0.0.1:1234/v1` | LM Studio API base (`http://host.docker.internal:1234/v1` in Docker) |
| `LM_STUDIO_MODEL` | *(empty)* | Pin a model id; empty means auto-detect the first from `/v1/models` |
| `LM_STUDIO_API_TOKEN` | *(empty)* | Optional bearer token for LM Studio; only sent when non-empty. Export it in your shell — never commit a value |

Fixed in code: max 128 text values per `/api/translate` request, client-side chunks of 64,
`temperature` `0.1`, 120 s completion timeout, 30 s model-list timeout.

## HTTP API

- `GET /api/health` — reports the LM Studio base URL, resolved active model, and configured override.
  Returns 502 when LM Studio is unreachable.
- `POST /api/translate` — `{"sourceLanguage": "auto", "targetLanguage": "de", "texts": ["..."]}` →
  `{"translations": ["..."]}`.

The host has no authentication, rate limiting, or CORS restrictions. Keep it on loopback.

## npm scripts

| Script | Does |
| --- | --- |
| `start` | Runs the HTTPS host with Python |
| `install-manifest` | Sideloads `manifest.xml` into Excel |
| `docker:up` / `docker:down` / `docker:logs` | Manage the container |
| `docker:test` | Health check plus a sample translation call |
| `excel:reset` | Clears Excel's sideload and web caches (confirmation required) |
| `mac:trust-cert` | Trusts `certs/localhost.pem` in your login keychain |
| `docs:install` / `docs:dev` / `docs:build` / `docs:preview` | The documentation site in `docs/` |

## Project layout

```text
manifest.xml            Office Add-in manifest (XLT namespace, custom functions)
web/                    taskpane + custom function implementations and metadata
scripts/dev_server.py   HTTPS host and LM Studio translation proxy
scripts/*.sh            manifest sideload, cert trust, Excel cache reset, docker wrappers
Dockerfile              python:3.12-slim host image
docs/                   Astro Starlight documentation site
```

## Tech stack

- **Add-in:** Office.js custom functions, plain HTML/CSS/JavaScript, no build step
- **Host:** Python 3.12 standard library (`http.server`, `ssl`, `urllib`) over TLS
- **Translation backend:** LM Studio's OpenAI-compatible `/v1/chat/completions`
- **Container:** `python:3.12-slim` via Docker Compose
- **Docs:** Astro Starlight with the Galaxy theme, deployed to GitHub Pages

## Documentation

```bash
cd docs
npm install
npm run build
```

## References

- [Create custom functions in Excel](https://learn.microsoft.com/en-us/office/dev/add-ins/excel/custom-functions-overview)
- [Manually create JSON metadata for custom functions](https://learn.microsoft.com/en-us/office/dev/add-ins/excel/custom-functions-json)
- [Sideload Office Add-ins on Mac for testing](https://learn.microsoft.com/en-us/office/dev/add-ins/testing/sideload-an-office-add-in-on-mac)
- [LM Studio local server](https://lmstudio.ai/docs/developer/core/server)
- [LM Studio OpenAI-compatible endpoints](https://lmstudio.ai/docs/app/api/endpoints/openai)

## License

MIT — see [LICENSE](LICENSE).
