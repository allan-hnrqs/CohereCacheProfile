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


def build_unique_token_text(count: int) -> str:
    return " ".join(f"uniq{i:05d}" for i in range(count))


def build_natural_prefix(section_count: int) -> str:
    paragraphs = []
    for i in range(section_count):
        paragraphs.append(
            " ".join(
                [
                    f"Project Northwind section {i + 1} describes a customer support platform for regional logistics teams.",
                    f"The operations manager for district {i + 1} wants weekly backlog summaries, outage explanations, and staffing notes.",
                    f"Each report must mention order routing, refund handling, partner escalations, and warehouse cut-off rules for shift {i + 3}.",
                    f"The engineering note for section {i + 1} states that background jobs retry three times, but payment holds expire after {12 + i} hours.",
                    f"Analysts in Montreal, Denver, and Austin compare trends, note exceptions, and flag policy drift between enterprise and retail accounts.",
                ]
            )
        )
    return "\n\n".join(paragraphs)


def build_history(turns: int) -> list[dict]:
    messages = [
        {
            "role": "system",
            "content": (
                "You are helping maintain an internal planning assistant for a construction supplier. "
                "Keep prior commitments consistent unless the user explicitly changes them."
            ),
        }
    ]
    for i in range(turns):
        user_msg = (
            f"We are planning week {i + 1} for the Prairie division. "
            f"Truck set {i + 2} covers Regina, Saskatoon, and Moose Jaw. "
            f"Store managers asked for split deliveries, forklift support, and early invoices for project code P-{1400 + i}. "
            f"Note that the concrete crew prefers arrivals before {8 + (i % 3)} AM and drywall orders after lunch."
        )
        assistant_msg = (
            f"Recorded week {i + 1}: keep truck set {i + 2}, prioritize Regina first, "
            f"send forklift support to Saskatoon, and mark Moose Jaw invoices for project P-{1400 + i}. "
            f"I also noted the concrete arrival window and the drywall timing preference."
        )
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": assistant_msg})
    messages.append(
        {
            "role": "user",
            "content": (
                "Confirm the current plan in one short sentence, but only output OK for this benchmark."
            ),
        }
    )
    return messages


def mutate_first_content(messages: list[dict], marker: str) -> list[dict]:
    cloned = [dict(item) for item in messages]
    for item in cloned:
        if item["role"] in {"system", "user", "assistant"}:
            item["content"] = marker + "\n" + item["content"]
            break
    return cloned


def scenario_definitions() -> list[dict]:
    sizes = [("small", 250), ("medium", 2000), ("large", 5000)]
    scenarios = []

    for label, token_count in sizes:
        exact_messages = [
            {"role": "system", "content": build_unique_token_text(token_count)},
            {"role": "user", "content": "Return only OK."},
        ]
        miss_messages = mutate_first_content(exact_messages, f"MISS-{label.upper()}")
        scenarios.extend(
            [
                {
                    "name": f"size_{label}_exact_1",
                    "group": f"size_{label}",
                    "kind": "size_sweep",
                    "messages": exact_messages,
                },
                {
                    "name": f"size_{label}_exact_2",
                    "group": f"size_{label}",
                    "kind": "size_sweep",
                    "messages": exact_messages,
                },
                {
                    "name": f"size_{label}_miss_1",
                    "group": f"size_{label}",
                    "kind": "size_sweep",
                    "messages": miss_messages,
                },
            ]
        )

    natural_prefix = [
        {"role": "system", "content": build_natural_prefix(22)},
        {"role": "user", "content": "Return only OK."},
    ]
    scenarios.extend(
        [
            {
                "name": "natural_prefix_exact_1",
                "group": "natural_prefix",
                "kind": "natural_prefix",
                "messages": natural_prefix,
            },
            {
                "name": "natural_prefix_exact_2",
                "group": "natural_prefix",
                "kind": "natural_prefix",
                "messages": natural_prefix,
            },
            {
                "name": "natural_prefix_miss_1",
                "group": "natural_prefix",
                "kind": "natural_prefix",
                "messages": mutate_first_content(natural_prefix, "MISS-NATURAL-PREFIX"),
            },
        ]
    )

    natural_history = build_history(8)
    scenarios.extend(
        [
            {
                "name": "messages_history_exact_1",
                "group": "messages_history",
                "kind": "messages_history",
                "messages": natural_history,
            },
            {
                "name": "messages_history_exact_2",
                "group": "messages_history",
                "kind": "messages_history",
                "messages": natural_history,
            },
            {
                "name": "messages_history_miss_1",
                "group": "messages_history",
                "kind": "messages_history",
                "messages": mutate_first_content(natural_history, "MISS-MESSAGES-HISTORY"),
            },
        ]
    )
    return scenarios


def extract_text_reply(body: dict) -> str:
    content = (body.get("message") or {}).get("content") or []
    return " ".join(
        block.get("text", "") for block in content if block.get("type") == "text"
    ).strip()


def summarize(rows: list[dict]) -> dict:
    by_model = {}
    for row in rows:
        by_model.setdefault(row["model"], []).append(row)

    summary = {}
    for model, model_rows in by_model.items():
        per_group = {}
        for group in sorted({row["group"] for row in model_rows}):
            exact = [r for r in model_rows if r["group"] == group and "_exact_" in r["scenario"]]
            misses = [r for r in model_rows if r["group"] == group and "_miss_" in r["scenario"]]
            per_group[group] = {
                "exact_billed_input_tokens": sorted(
                    {r["usage"]["billed_input_tokens"] for r in exact}
                ),
                "miss_billed_input_tokens": sorted(
                    {r["usage"]["billed_input_tokens"] for r in misses}
                ),
                "exact_cached_tokens": sorted(
                    {r["usage"]["cached_tokens"] for r in exact}
                ),
                "miss_cached_tokens": sorted(
                    {r["usage"]["cached_tokens"] for r in misses}
                ),
                "exact_median_elapsed_s": round(
                    statistics.median(r["elapsed_s"] for r in exact), 3
                )
                if exact
                else None,
                "miss_median_elapsed_s": round(
                    statistics.median(r["elapsed_s"] for r in misses), 3
                )
                if misses
                else None,
            }
        summary[model] = per_group
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--max-tokens", type=int, default=4)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    api_key = os.environ.get("COHERE_API_KEY")
    if not api_key:
        raise SystemExit("COHERE_API_KEY is not set")

    rows = []
    for model in args.models:
        for scenario in scenario_definitions():
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
            rows.append(
                {
                    "model": model,
                    "scenario": scenario["name"],
                    "group": scenario["group"],
                    "kind": scenario["kind"],
                    "message_count": len(scenario["messages"]),
                    "elapsed_s": round(elapsed, 3),
                    "status": status,
                    "finish_reason": body.get("finish_reason"),
                    "reply_preview": extract_text_reply(body)[:120],
                    "usage": {
                        "billed_input_tokens": billed.get("input_tokens"),
                        "billed_output_tokens": billed.get("output_tokens"),
                        "raw_input_tokens": tokens.get("input_tokens"),
                        "raw_output_tokens": tokens.get("output_tokens"),
                        "cached_tokens": usage.get("cached_tokens"),
                    },
                    "messages": scenario["messages"],
                    "error": body if status != 200 else None,
                }
            )

    payload = {
        "run_date": str(date.today()),
        "api_url": API_URL,
        "models": args.models,
        "rows": rows,
        "summary": summarize(rows),
    }

    output = args.output or f"results/chat-shapes-{date.today().isoformat()}.json"
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")

    print(json.dumps(payload["summary"], indent=2))
    print(f"\nWrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
