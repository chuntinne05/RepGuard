"""Exactly two synthetic transport probes; no corpus labels or quality tuning."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from dotenv import dotenv_values

from .prepare import OUT, ROOT, digest, write

MODELS = ("gemini-3.8-flash", "gemma-4-26b-a4b-it")


def main():
    key = dotenv_values(ROOT / ".env").get("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("Configured API credential unavailable")
    records = []
    for model in MODELS:
        path = OUT / "provider_probe" / (model + ".json")
        if path.exists():
            records.append(json.loads(path.read_text()))
            continue
        body = {"contents": [{"role": "user", "parts": [{"text":
                'Transport check only. Reply with exactly this JSON object and no other text: {"status":"ok"}'}]}],
                "generationConfig": {"temperature": 0, "maxOutputTokens": 4096}}
        record = {"model_requested": model, "created_utc": datetime.now(timezone.utc).isoformat(),
                  "request": body, "request_sha256": digest(body), "synthetic_only": True,
                  "generation_attempts": 1}
        start = time.monotonic()
        try:
            request = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
            with urllib.request.urlopen(request, timeout=90) as response:
                record["status"] = response.status
                record["response"] = json.load(response)
            candidates = record["response"].get("candidates", [])
            text = "".join(p.get("text", "") for p in candidates[0].get("content", {}).get("parts", [])
                           if not p.get("thought")) if candidates else ""
            try:
                record["valid"] = json.loads(text) == {"status": "ok"}
            except ValueError:
                record["valid"] = False
        except urllib.error.HTTPError as error:
            record.update(status=error.code, error_body=error.read().decode(errors="replace"), valid=False)
        except Exception as error:
            record.update(status="transport_unknown", error_type=type(error).__name__, valid=False)
        record["wall_seconds"] = time.monotonic() - start
        write(path, record)
        records.append(record)
        print(json.dumps({"model": model, "status": record["status"], "valid": record["valid"],
                          "wall_seconds": record["wall_seconds"],
                          "version": record.get("response", {}).get("modelVersion"),
                          "usage": record.get("response", {}).get("usageMetadata")}), flush=True)
    write(OUT / "provider_probe/summary.json", {"probes": len(records),
          "api_pathway_valid": all(r["valid"] for r in records),
          "automatic_generation_retries": 0})


if __name__ == "__main__":
    main()
