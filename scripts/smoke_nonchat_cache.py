import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date


def post_json(url: str, api_key: str, payload: dict) -> tuple[int, dict, float]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            body = json.loads(response.read().decode("utf-8"))
            status = response.status
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode("utf-8"))
        status = exc.code
    elapsed = time.perf_counter() - start
    return status, body, elapsed


def build_unique_text(count: int) -> str:
    return " ".join(f"uniq{i:05d}" for i in range(count))


def embed_runs(api_key: str) -> list[dict]:
    url = "https://api.cohere.com/v2/embed"
    exact_text = build_unique_text(800)
    miss_text = "MISS-01 " + exact_text
    payloads = [
        {
            "name": "embed_exact_1",
            "payload": {
                "model": "embed-v4.0",
                "input_type": "search_document",
                "texts": [exact_text],
                "embedding_types": ["float"],
                "output_dimension": 256,
            },
        },
        {
            "name": "embed_exact_2",
            "payload": {
                "model": "embed-v4.0",
                "input_type": "search_document",
                "texts": [exact_text],
                "embedding_types": ["float"],
                "output_dimension": 256,
            },
        },
        {
            "name": "embed_miss_1",
            "payload": {
                "model": "embed-v4.0",
                "input_type": "search_document",
                "texts": [miss_text],
                "embedding_types": ["float"],
                "output_dimension": 256,
            },
        },
    ]
    rows = []
    for item in payloads:
        status, body, elapsed = post_json(url, api_key, item["payload"])
        meta = body.get("meta") or {}
        rows.append(
            {
                "endpoint": "embed",
                "scenario": item["name"],
                "status": status,
                "elapsed_s": round(elapsed, 3),
                "meta": meta,
                "id": body.get("id"),
            }
        )
    return rows


def rerank_runs(api_key: str) -> list[dict]:
    url = "https://api.cohere.com/v2/rerank"
    exact_doc = build_unique_text(700)
    miss_doc = "MISS-01 " + exact_doc
    docs_exact = [exact_doc, "short control document", "another short control document"]
    docs_miss = [miss_doc, "short control document", "another short control document"]
    payloads = [
        {
            "name": "rerank_exact_1",
            "payload": {
                "model": "rerank-v3.5",
                "query": "Which document contains the long synthetic token list?",
                "documents": docs_exact,
                "top_n": 2,
            },
        },
        {
            "name": "rerank_exact_2",
            "payload": {
                "model": "rerank-v3.5",
                "query": "Which document contains the long synthetic token list?",
                "documents": docs_exact,
                "top_n": 2,
            },
        },
        {
            "name": "rerank_miss_1",
            "payload": {
                "model": "rerank-v3.5",
                "query": "Which document contains the long synthetic token list?",
                "documents": docs_miss,
                "top_n": 2,
            },
        },
    ]
    rows = []
    for item in payloads:
        status, body, elapsed = post_json(url, api_key, item["payload"])
        meta = body.get("meta") or {}
        rows.append(
            {
                "endpoint": "rerank",
                "scenario": item["name"],
                "status": status,
                "elapsed_s": round(elapsed, 3),
                "meta": meta,
                "id": body.get("id"),
            }
        )
    return rows


def main() -> int:
    api_key = os.environ.get("COHERE_API_KEY")
    if not api_key:
        raise SystemExit("COHERE_API_KEY is not set")

    rows = embed_runs(api_key) + rerank_runs(api_key)
    output = f"results/nonchat-cache-smoke-{date.today().isoformat()}.json"
    os.makedirs("results", exist_ok=True)
    with open(output, "w", encoding="utf-8") as handle:
        json.dump({"run_date": str(date.today()), "rows": rows}, handle, indent=2)
        handle.write("\n")

    print(json.dumps(rows, indent=2))
    print(f"\nWrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
