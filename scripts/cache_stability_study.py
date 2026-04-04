import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
import uuid
from datetime import date


COHERE_URL = "https://api.cohere.com/v2/chat"
OPENAI_URL = "https://api.openai.com/v1/responses"

DEFAULT_COHERE_MODELS = [
    "command-a-03-2025",
    "command-r7b-12-2024",
]

DEFAULT_OPENAI_MODELS = [
    "gpt-5.4-mini",
    "gpt-5.4",
]

COHERE_PRICING = {
    "command-a-03-2025": {"input_per_mtok": 2.5, "output_per_mtok": 10.0},
    "command-r7b-12-2024": {"input_per_mtok": 0.0375, "output_per_mtok": 0.15},
}

OPENAI_PRICING = {
    "gpt-5.4-mini": {
        "input_per_mtok": 0.75,
        "cached_input_per_mtok": 0.075,
        "output_per_mtok": 4.5,
    },
    "gpt-5.4": {
        "input_per_mtok": 2.5,
        "cached_input_per_mtok": 0.25,
        "output_per_mtok": 15.0,
    },
}


def build_unique_token_text(count: int) -> str:
    return " ".join(f"uniq{i:05d}" for i in range(count))


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
            "content": "Confirm the current plan in one short sentence, but only output OK for this benchmark.",
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


def scenario_bases() -> dict[str, list[dict]]:
    return {
        "size_large": [
            {"role": "system", "content": build_unique_token_text(5000)},
            {"role": "user", "content": "Return only OK."},
        ],
        "messages_history_long": build_history(16),
    }


def make_json_request(url: str, headers: dict, payload: dict) -> tuple[int, dict, float]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            body = json.loads(response.read().decode("utf-8"))
            status = response.status
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode("utf-8"))
        status = exc.code
    elapsed = time.perf_counter() - start
    return status, body, elapsed


def cohere_cost_estimate(model: str, billed_input: int | None, billed_output: int | None) -> float | None:
    if billed_input is None or billed_output is None:
        return None
    pricing = COHERE_PRICING[model]
    return round(
        billed_input / 1_000_000 * pricing["input_per_mtok"]
        + billed_output / 1_000_000 * pricing["output_per_mtok"],
        6,
    )


def openai_cost_estimate(model: str, input_tokens: int | None, cached_tokens: int | None, output_tokens: int | None) -> float | None:
    if input_tokens is None or cached_tokens is None or output_tokens is None:
        return None
    uncached_tokens = input_tokens - cached_tokens
    pricing = OPENAI_PRICING[model]
    return round(
        uncached_tokens / 1_000_000 * pricing["input_per_mtok"]
        + cached_tokens / 1_000_000 * pricing["cached_input_per_mtok"]
        + output_tokens / 1_000_000 * pricing["output_per_mtok"],
        6,
    )


def convert_openai_messages(messages: list[dict]) -> list[dict]:
    converted = []
    for message in messages:
        role = message["role"]
        content_type = "output_text" if role == "assistant" else "input_text"
        converted.append(
            {
                "role": role,
                "content": [{"type": content_type, "text": message["content"]}],
            }
        )
    return converted


def run_cohere_request(api_key: str, model: str, messages: list[dict]) -> tuple[dict, float, int]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 4,
        "temperature": 0,
        "seed": 1,
    }
    status, body, elapsed = make_json_request(COHERE_URL, headers, payload)
    usage = body.get("usage") or {}
    billed = usage.get("billed_units") or {}
    tokens = usage.get("tokens") or {}
    row = {
        "status": status,
        "elapsed_s": round(elapsed, 3),
        "usage": {
            "billed_input_tokens": billed.get("input_tokens"),
            "billed_output_tokens": billed.get("output_tokens"),
            "raw_input_tokens": tokens.get("input_tokens"),
            "raw_output_tokens": tokens.get("output_tokens"),
            "cached_tokens": usage.get("cached_tokens"),
        },
        "estimated_cost_usd": cohere_cost_estimate(
            model,
            billed.get("input_tokens"),
            billed.get("output_tokens"),
        ),
        "error": body if status != 200 else None,
    }
    return row, elapsed, status


def run_openai_request(api_key: str, model: str, messages: list[dict], prompt_cache_key: str) -> tuple[dict, float, int]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "input": convert_openai_messages(messages),
        "max_output_tokens": 16,
        "temperature": 0,
        "prompt_cache_key": prompt_cache_key,
        "prompt_cache_retention": "in_memory",
        "text": {"format": {"type": "text"}, "verbosity": "low"},
        "reasoning": {"effort": "none"},
    }
    status, body, elapsed = make_json_request(OPENAI_URL, headers, payload)
    usage = body.get("usage") or {}
    input_details = usage.get("input_tokens_details") or {}
    output_details = usage.get("output_tokens_details") or {}
    row = {
        "status": status,
        "elapsed_s": round(elapsed, 3),
        "resolved_model": body.get("model"),
        "usage": {
            "input_tokens": usage.get("input_tokens"),
            "cached_tokens": input_details.get("cached_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "reasoning_tokens": output_details.get("reasoning_tokens"),
        },
        "estimated_cost_usd": openai_cost_estimate(
            model,
            usage.get("input_tokens"),
            input_details.get("cached_tokens"),
            usage.get("output_tokens"),
        ),
        "error": body if status != 200 else None,
    }
    return row, elapsed, status


def metric_keys(provider: str) -> tuple[str, str]:
    if provider == "openai":
        return "input_tokens", "cached_tokens"
    return "billed_input_tokens", "cached_tokens"


def billing_hit(cost: float | None, cold_cost: float | None) -> bool | None:
    if cost is None or cold_cost is None:
        return None
    if cold_cost == 0:
        return None
    return cost <= cold_cost * 0.95


def median_or_none(values: list[float | int | None], digits: int) -> float | None:
    cleaned = [value for value in values if value is not None]
    if not cleaned:
        return None
    return round(statistics.median(cleaned), digits)


def min_or_none(values: list[float | int | None], digits: int) -> float | None:
    cleaned = [value for value in values if value is not None]
    if not cleaned:
        return None
    return round(min(cleaned), digits)


def max_or_none(values: list[float | int | None], digits: int) -> float | None:
    cleaned = [value for value in values if value is not None]
    if not cleaned:
        return None
    return round(max(cleaned), digits)


def summarize_phase(rows: list[dict], cold_cost: float | None, provider: str) -> dict:
    input_key, cache_key = metric_keys(provider)
    costs = [row.get("estimated_cost_usd") for row in rows]
    latencies = [row.get("elapsed_s") for row in rows]
    cached = [row["usage"].get(cache_key) for row in rows]
    inputs = [row["usage"].get(input_key) for row in rows]
    reported_hits = [value is not None and value > 0 for value in cached]
    billing_hits = [billing_hit(cost, cold_cost) for cost in costs]
    billing_hits_clean = [value for value in billing_hits if value is not None]
    return {
        "count": len(rows),
        "median_elapsed_s": median_or_none(latencies, 3),
        "min_elapsed_s": min_or_none(latencies, 3),
        "max_elapsed_s": max_or_none(latencies, 3),
        "median_cost_usd": median_or_none(costs, 6),
        "min_cost_usd": min_or_none(costs, 6),
        "max_cost_usd": max_or_none(costs, 6),
        "median_input_tokens": median_or_none(inputs, 0),
        "median_cached_tokens": median_or_none(cached, 0),
        "reported_cache_hit_rate": round(sum(reported_hits) / len(reported_hits), 3) if reported_hits else None,
        "billing_hit_rate": round(sum(billing_hits_clean) / len(billing_hits_clean), 3) if billing_hits_clean else None,
        "reported_cache_hits": reported_hits,
        "billing_hits": billing_hits,
        "cached_tokens": cached,
        "costs_usd": costs,
        "elapsed_s": latencies,
    }


def summarize(rows: list[dict]) -> dict:
    summary = {}
    grouped = {}
    for row in rows:
        grouped.setdefault((row["provider"], row["model"], row["group"]), []).append(row)

    for (provider, model, group), items in grouped.items():
        phases = {}
        for item in items:
            phases.setdefault(item["phase"], []).append(item)
        cold_rows = phases.get("cold", [])
        cold_cost = cold_rows[0]["estimated_cost_usd"] if cold_rows else None
        cold_phase = summarize_phase(cold_rows, cold_cost, provider) if cold_rows else None
        summary.setdefault(provider, {}).setdefault(model, {})[group] = {
            "cold": cold_phase,
            "warm_immediate": summarize_phase(phases.get("warm_immediate", []), cold_cost, provider),
            "miss_immediate": summarize_phase(phases.get("miss_immediate", []), cold_cost, provider),
            "warm_delayed": summarize_phase(phases.get("warm_delayed", []), cold_cost, provider),
            "delay_seconds": phases.get("warm_delayed", [{}])[0].get("delay_seconds") if phases.get("warm_delayed") else None,
        }
    return summary


def run_cohere_model(
    api_key: str,
    model: str,
    bases: dict[str, list[dict]],
    run_nonce: str,
    immediate_repeats: int,
    miss_repeats: int,
    delayed_repeats: int,
    delay_seconds: int,
) -> list[dict]:
    rows = []
    for group, base_messages in bases.items():
        exact_messages = mutate_first_content(base_messages, f"RUN-{run_nonce[:8]}:{group}:EXACT")
        phases = [("cold", 1), ("warm_immediate", immediate_repeats), ("miss_immediate", miss_repeats)]
        for phase_name, count in phases:
            for attempt in range(1, count + 1):
                if phase_name == "miss_immediate":
                    messages = mutate_first_content(base_messages, f"RUN-{run_nonce[:8]}:{group}:MISS:{attempt}")
                else:
                    messages = exact_messages
                result, _, _ = run_cohere_request(api_key, model, messages)
                rows.append(
                    {
                        "provider": "cohere",
                        "model": model,
                        "group": group,
                        "phase": phase_name,
                        "attempt": attempt,
                        "delay_seconds": 0,
                        **result,
                    }
                )
        if delayed_repeats:
            time.sleep(delay_seconds)
            for attempt in range(1, delayed_repeats + 1):
                result, _, _ = run_cohere_request(api_key, model, exact_messages)
                rows.append(
                    {
                        "provider": "cohere",
                        "model": model,
                        "group": group,
                        "phase": "warm_delayed",
                        "attempt": attempt,
                        "delay_seconds": delay_seconds,
                        **result,
                    }
                )
    return rows


def run_openai_model(
    api_key: str,
    model: str,
    bases: dict[str, list[dict]],
    run_nonce: str,
    immediate_repeats: int,
    miss_repeats: int,
    delayed_repeats: int,
    delay_seconds: int,
) -> list[dict]:
    rows = []
    for group, base_messages in bases.items():
        exact_messages = mutate_first_content(base_messages, f"RUN-{run_nonce[:8]}:{group}:EXACT")
        exact_cache_key = f"css:{run_nonce[:8]}:{model}:{group}"
        phases = [("cold", 1), ("warm_immediate", immediate_repeats), ("miss_immediate", miss_repeats)]
        for phase_name, count in phases:
            for attempt in range(1, count + 1):
                if phase_name == "miss_immediate":
                    messages = mutate_first_content(base_messages, f"RUN-{run_nonce[:8]}:{group}:MISS:{attempt}")
                    prompt_cache_key = f"{exact_cache_key}:m{attempt}"
                else:
                    messages = exact_messages
                    prompt_cache_key = exact_cache_key
                result, _, _ = run_openai_request(api_key, model, messages, prompt_cache_key)
                rows.append(
                    {
                        "provider": "openai",
                        "model": model,
                        "group": group,
                        "phase": phase_name,
                        "attempt": attempt,
                        "delay_seconds": 0,
                        **result,
                    }
                )
        if delayed_repeats:
            time.sleep(delay_seconds)
            for attempt in range(1, delayed_repeats + 1):
                result, _, _ = run_openai_request(api_key, model, exact_messages, exact_cache_key)
                rows.append(
                    {
                        "provider": "openai",
                        "model": model,
                        "group": group,
                        "phase": "warm_delayed",
                        "attempt": attempt,
                        "delay_seconds": delay_seconds,
                        **result,
                    }
                )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a cache stability study across repeated and delayed prompts.")
    parser.add_argument("--immediate-repeats", type=int, default=6)
    parser.add_argument("--miss-repeats", type=int, default=4)
    parser.add_argument("--delayed-repeats", type=int, default=2)
    parser.add_argument("--delay-seconds", type=int, default=20)
    parser.add_argument("--cohere-models", nargs="*", default=DEFAULT_COHERE_MODELS)
    parser.add_argument("--openai-models", nargs="*", default=DEFAULT_OPENAI_MODELS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cohere_key = os.environ.get("COHERE_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not cohere_key:
        raise SystemExit("COHERE_API_KEY is not set")
    if not openai_key:
        raise SystemExit("OPENAI_API_KEY is not set")

    run_nonce = uuid.uuid4().hex
    bases = scenario_bases()
    rows = []

    for model in args.cohere_models:
        rows.extend(
            run_cohere_model(
                cohere_key,
                model,
                bases,
                run_nonce,
                args.immediate_repeats,
                args.miss_repeats,
                args.delayed_repeats,
                args.delay_seconds,
            )
        )

    for model in args.openai_models:
        rows.extend(
            run_openai_model(
                openai_key,
                model,
                bases,
                run_nonce,
                args.immediate_repeats,
                args.miss_repeats,
                args.delayed_repeats,
                args.delay_seconds,
            )
        )

    payload = {
        "run_date": str(date.today()),
        "run_nonce": run_nonce,
        "parameters": {
            "immediate_repeats": args.immediate_repeats,
            "miss_repeats": args.miss_repeats,
            "delayed_repeats": args.delayed_repeats,
            "delay_seconds": args.delay_seconds,
            "groups": list(bases.keys()),
            "cohere_models": args.cohere_models,
            "openai_models": args.openai_models,
        },
        "rows": rows,
        "summary": summarize(rows),
    }

    os.makedirs("results", exist_ok=True)
    output = f"results/cache-stability-study-{date.today().isoformat()}.json"
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")

    print(json.dumps(payload["summary"], indent=2))
    print(f"\nWrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
