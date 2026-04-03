import argparse
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import date


API_URL = "https://api.cohere.com/v2/chat"
DEFAULT_MODELS = [
    "command-a-03-2025",
    "command-a-reasoning-08-2025",
    "command-r7b-12-2024",
]


def build_large_prefix(repetitions: int) -> str:
    chunk = (
        "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu "
        "nu xi omicron pi rho sigma tau upsilon phi chi psi omega "
    )
    return "BEGIN LARGE PREFIX\n" + (chunk * repetitions) + "\nEND LARGE PREFIX"


def build_unique_prefix(count: int) -> str:
    tokens = [f"uniq{i:05d}" for i in range(count)]
    return "BEGIN UNIQUE PREFIX\n" + " ".join(tokens) + "\nEND UNIQUE PREFIX"


def scenarios() -> list[dict]:
    large = build_large_prefix(600)
    unique_large = build_unique_prefix(5000)
    return [
        {
            "name": "tiny_plain",
            "messages": [{"role": "user", "content": "Say OK."}],
        },
        {
            "name": "tiny_with_system",
            "messages": [
                {"role": "system", "content": "You are terse."},
                {"role": "user", "content": "Say OK."},
            ],
        },
        {
            "name": "large_exact_1",
            "messages": [
                {"role": "system", "content": large},
                {"role": "user", "content": "Return only the word OK."},
            ],
        },
        {
            "name": "large_exact_2",
            "messages": [
                {"role": "system", "content": large},
                {"role": "user", "content": "Return only the word OK."},
            ],
        },
        {
            "name": "large_miss_1",
            "messages": [
                {"role": "system", "content": "MISS-01\n" + large},
                {"role": "user", "content": "Return only the word OK."},
            ],
        },
        {
            "name": "large_miss_2",
            "messages": [
                {"role": "system", "content": "MISS-02\n" + large},
                {"role": "user", "content": "Return only the word OK."},
            ],
        },
        {
            "name": "unique_large_exact_1",
            "messages": [
                {"role": "system", "content": unique_large},
                {"role": "user", "content": "Return only the word OK."},
            ],
        },
        {
            "name": "unique_large_exact_2",
            "messages": [
                {"role": "system", "content": unique_large},
                {"role": "user", "content": "Return only the word OK."},
            ],
        },
        {
            "name": "unique_large_miss_1",
            "messages": [
                {"role": "system", "content": "MISS-01\n" + unique_large},
                {"role": "user", "content": "Return only the word OK."},
            ],
        },
        {
            "name": "unique_large_miss_2",
            "messages": [
                {"role": "system", "content": "MISS-02\n" + unique_large},
                {"role": "user", "content": "Return only the word OK."},
            ],
        },
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--max-tokens", type=int, default=4)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def ensure_api_key() -> str:
    api_key = os.environ.get("COHERE_API_KEY")
    if not api_key:
        raise SystemExit("COHERE_API_KEY is not set")
    return api_key


def make_request(api_key: str, payload: dict) -> tuple[int, dict, float]:
    req = urllib.request.Request(
        API_URL,
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


def extract_reply(body: dict) -> str:
    content = (body.get("message") or {}).get("content") or []
    parts = []
    for block in content:
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
    return " ".join(parts).strip()


def run_model(api_key: str, model: str, args: argparse.Namespace) -> list[dict]:
    rows = []
    for scenario in scenarios():
        payload = {
            "model": model,
            "messages": scenario["messages"],
            "max_tokens": args.max_tokens,
            "temperature": args.temperature,
            "seed": args.seed,
        }
        status, body, elapsed = make_request(api_key, payload)
        usage = body.get("usage") or {}
        billed = usage.get("billed_units") or {}
        tokens = usage.get("tokens") or {}
        row = {
            "model": model,
            "scenario": scenario["name"],
            "status": status,
            "elapsed_s": round(elapsed, 3),
            "finish_reason": body.get("finish_reason"),
            "reply_preview": extract_reply(body)[:120],
            "usage": {
                "billed_input_tokens": billed.get("input_tokens"),
                "billed_output_tokens": billed.get("output_tokens"),
                "raw_input_tokens": tokens.get("input_tokens"),
                "raw_output_tokens": tokens.get("output_tokens"),
                "cached_tokens": usage.get("cached_tokens"),
            },
        }
        if status != 200:
            row["error"] = body
        rows.append(row)
    return rows


def summarize(rows: list[dict]) -> dict:
    by_model: dict[str, list[dict]] = {}
    for row in rows:
        by_model.setdefault(row["model"], []).append(row)

    summary = {}
    for model, model_rows in by_model.items():
        exact = [r for r in model_rows if r["scenario"].startswith("large_exact")]
        misses = [r for r in model_rows if r["scenario"].startswith("large_miss")]
        summary[model] = {
            "tiny_cached_tokens": next(
                (
                    r["usage"]["cached_tokens"]
                    for r in model_rows
                    if r["scenario"] == "tiny_plain"
                ),
                None,
            ),
            "tiny_raw_minus_billed": next(
                (
                    (
                        (r["usage"]["raw_input_tokens"] or 0)
                        - (r["usage"]["billed_input_tokens"] or 0)
                    )
                    for r in model_rows
                    if r["scenario"] == "tiny_plain"
                ),
                None,
            ),
            "large_exact_cached_tokens": sorted(
                {r["usage"]["cached_tokens"] for r in exact}
            ),
            "large_miss_cached_tokens": sorted(
                {r["usage"]["cached_tokens"] for r in misses}
            ),
            "large_exact_billed_inputs": sorted(
                {r["usage"]["billed_input_tokens"] for r in exact}
            ),
            "large_miss_billed_inputs": sorted(
                {r["usage"]["billed_input_tokens"] for r in misses}
            ),
            "large_exact_median_elapsed_s": round(
                statistics.median(r["elapsed_s"] for r in exact), 3
            )
            if exact
            else None,
            "large_miss_median_elapsed_s": round(
                statistics.median(r["elapsed_s"] for r in misses), 3
            )
            if misses
            else None,
            "unique_large_exact_cached_tokens": sorted(
                {
                    r["usage"]["cached_tokens"]
                    for r in model_rows
                    if r["scenario"].startswith("unique_large_exact")
                }
            ),
            "unique_large_miss_cached_tokens": sorted(
                {
                    r["usage"]["cached_tokens"]
                    for r in model_rows
                    if r["scenario"].startswith("unique_large_miss")
                }
            ),
            "unique_large_exact_billed_inputs": sorted(
                {
                    r["usage"]["billed_input_tokens"]
                    for r in model_rows
                    if r["scenario"].startswith("unique_large_exact")
                }
            ),
            "unique_large_miss_billed_inputs": sorted(
                {
                    r["usage"]["billed_input_tokens"]
                    for r in model_rows
                    if r["scenario"].startswith("unique_large_miss")
                }
            ),
        }
    return summary


def main() -> int:
    args = parse_args()
    api_key = ensure_api_key()
    rows = []
    for model in args.models:
        rows.extend(run_model(api_key, model, args))

    payload = {
        "run_date": str(date.today()),
        "api_url": API_URL,
        "models": args.models,
        "rows": rows,
        "summary": summarize(rows),
    }

    output = args.output or f"results/chat-cache-{date.today().isoformat()}.json"
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")

    print(json.dumps(payload["summary"], indent=2))
    print(f"\nWrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
