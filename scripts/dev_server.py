#!/usr/bin/env python3

import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = ROOT / "web"
CERT_PATH = ROOT / "certs" / "localhost.pem"
KEY_PATH = ROOT / "certs" / "localhost-key.pem"
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "3000"))
LM_STUDIO_BASE_URL = os.environ.get("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
LM_STUDIO_API_TOKEN = os.environ.get("LM_STUDIO_API_TOKEN", "").strip()
LM_STUDIO_MODEL = os.environ.get("LM_STUDIO_MODEL", "").strip()
LM_STUDIO_CHAT_URL = f"{LM_STUDIO_BASE_URL}/chat/completions"
LM_STUDIO_MODELS_URL = f"{LM_STUDIO_BASE_URL}/models"


class AddInHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self):
        if self.path == "/":
            self.path = "/taskpane.html"
            return super().do_GET()

        if self.path == "/api/health":
            try:
                active_model = self._get_lm_studio_model()
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "defaultProvider": "lm_studio",
                        "lmStudioBaseUrl": LM_STUDIO_BASE_URL,
                        "activeModel": active_model,
                        "configuredModel": LM_STUDIO_MODEL,
                        "message": "Excel add-in host is running.",
                    },
                )
            except RuntimeError as exc:
                self._send_json(
                    HTTPStatus.BAD_GATEWAY,
                    {
                        "ok": False,
                        "defaultProvider": "lm_studio",
                        "lmStudioBaseUrl": LM_STUDIO_BASE_URL,
                        "error": str(exc),
                    },
                )
            return

        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/translate":
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "Request body must be valid JSON."},
            )
            return

        source_language = str(payload.get("sourceLanguage", "")).strip()
        target_language = str(payload.get("targetLanguage", "")).strip()
        texts = payload.get("texts", [])

        if not target_language:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "A target language is required."})
            return

        if not isinstance(texts, list) or not texts:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "At least one text value is required."})
            return

        if len(texts) > 128:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "This proxy accepts at most 128 text values per request."},
            )
            return

        normalized = [str(value) for value in texts]

        try:
            translated_texts = self._translate_with_lm_studio(
                source_language=source_language or "auto",
                target_language=target_language,
                texts=normalized,
            )
        except RuntimeError as exc:
            self._send_json(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})
            return

        self._send_json(HTTPStatus.OK, {"translations": translated_texts})

    def log_message(self, format, *args):
        sys.stdout.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

    def _send_json(self, status_code, payload):
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _translate_with_lm_studio(self, source_language, target_language, texts):
        model = self._get_lm_studio_model()
        translated_texts = []

        for text in texts:
            prompt = self._build_translation_prompt(text, source_language, target_language)
            request = urllib.request.Request(
                LM_STUDIO_CHAT_URL,
                data=json.dumps(
                    {
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You are a translation engine. Translate the user's text exactly once. "
                                    "Return only the translated text with no commentary, no quotes, and no explanations. "
                                    "Be conservative with short or ambiguous text. Preserve proper nouns, personal names, "
                                    "brand names, product codes, numbers, URLs, email addresses, and identifiers exactly as written "
                                    "unless the user explicitly asks for transliteration or there is a very common standardized localized form."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.1,
                    }
                ).encode("utf-8"),
                headers=self._json_headers(),
                method="POST",
            )

            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                error_body = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"LM Studio translate request failed: HTTP {exc.code} {error_body}") from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(f"Could not reach LM Studio at {LM_STUDIO_BASE_URL}: {exc.reason}") from exc
            except json.JSONDecodeError as exc:
                raise RuntimeError("LM Studio returned an unexpected response.") from exc

            translated_text = (
                payload.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            translated_texts.append(str(translated_text).strip())

        return translated_texts

    def _get_lm_studio_model(self):
        if LM_STUDIO_MODEL:
            return LM_STUDIO_MODEL

        request = urllib.request.Request(
            LM_STUDIO_MODELS_URL,
            headers=self._json_headers(),
            method="GET",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LM Studio models request failed: HTTP {exc.code} {error_body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach LM Studio at {LM_STUDIO_BASE_URL}: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("LM Studio models endpoint returned an unexpected response.") from exc

        models = payload.get("data", [])
        if not isinstance(models, list) or not models:
            raise RuntimeError(
                "LM Studio did not return any available models. Start the LM Studio server and load a model first."
            )

        first_model = models[0]
        model_id = first_model.get("id")
        if not model_id:
            raise RuntimeError("LM Studio returned a model entry without an id.")

        return str(model_id)

    def _build_translation_prompt(self, text, source_language, target_language):
        source_label = source_language if source_language and source_language != "auto" else "auto-detected language"
        return (
            f"Translate the following text from {source_label} to {target_language}.\n"
            "Preserve meaning, tone, and formatting as much as possible.\n"
            "Keep names and identifiers unchanged.\n"
            "If the text mixes a normal phrase with a person or brand name, translate only the phrase.\n"
            "Do not transliterate names unless explicitly requested.\n"
            "Text:\n"
            f"{text}"
        )

    def _json_headers(self):
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        if LM_STUDIO_API_TOKEN:
            headers["Authorization"] = f"Bearer {LM_STUDIO_API_TOKEN}"
        return headers


def main():
    if not CERT_PATH.exists() or not KEY_PATH.exists():
        print("Missing HTTPS certificate files.")
        print(f"Expected: {CERT_PATH}")
        print(f"Expected: {KEY_PATH}")
        print("Create them first. See README.md for the openssl command.")
        raise SystemExit(1)

    server = ThreadingHTTPServer((HOST, PORT), AddInHandler)
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile=str(CERT_PATH), keyfile=str(KEY_PATH))
    server.socket = ssl_context.wrap_socket(server.socket, server_side=True)

    print(f"Serving Excel add-in at https://localhost:{PORT}/taskpane.html")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
