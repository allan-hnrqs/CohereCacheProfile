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

COHERE_MODELS = [
    "command-a-03-2025",
    "command-r7b-12-2024",
]

OPENAI_MODELS = [
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


def scenario_groups(run_nonce: str) -> list[dict]:
    size_large = [
        {"role": "system", "content": build_unique_token_text(5000)},
        {"role": "user", "content": "Return only OK."},
    ]
    natural_prefix = [
        {"role": "system", "content": build_natural_prefix(22)},
        {"role": "user", "content": "Return only OK."},
    ]
    messages_history = build_history(8)
    messages_history_long = build_history(16)

    bases = [
        ("size_large", size_large),
        ("natural_prefix", natural_prefix),
        ("messages_history", messages_history),
        ("messages_history_long", messages_history_long),
    ]
    groups = []
    for group_name, exact_messages in bases:
        exact_payload = mutate_first_content(
            exact_messages, f"RUN-{run_nonce[:8]}:{group_name}:EXACT"
        )
        groups.extend(
            [
                {"group": group_name, "scenario": f"{group_name}_exact_1", "kind": "exact", "messages": exact_payload},
                {"group": group_name, "scenario": f"{group_name}_exact_2", "kind": "exact", "messages": exact_payload},
                {"group": group_name, "scenario": f"{group_name}_exact_3", "kind": "exact", "messages": exact_payload},
                {"group": group_name, "scenario": f"{group_name}_miss_1", "kind": "miss", "messages": mutate_first_content(exact_messages, f"RUN-{run_nonce[:8]}:{group_name}:MISS1")},
                {"group": group_name, "scenario": f"{group_name}_miss_2", "kind": "miss", "messages": mutate_first_content(exact_messages, f"RUN-{run_nonce[:8]}:{group_name}:MISS2")},
                {"group": group_name, "scenario": f"{group_name}_miss_3", "kind": "miss", "messages": mutate_first_content(exact_messages, f"RUN-{run_nonce[:8]}:{group_name}:MISS3")},
            ]
        )
    return groups


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
        if role == "assistant":
            content_type = "output_text"
        else:
            content_type = "input_text"
        converted.append(
            {
                "role": role,
                "content": [{"type": content_type, "text": message["content"]}],
            }
        )
    return converted


def run_cohere_model(api_key: str, model: str, scenarios: list[dict]) -> list[dict]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    rows = []
    for item in scenarios:
        payload = {
            "model": model,
            "messages": item["messages"],
            "max_tokens": 4,
            "temperature": 0,
            "seed": 1,
        }
        status, body, elapsed = make_json_request(COHERE_URL, headers, payload)
        usage = body.get("usage") or {}
        billed = usage.get("billed_units") or {}
        tokens = usage.get("tokens") or {}
        rows.append(
            {
                "provider": "cohere",
                "model": model,
                "group": item["group"],
                "scenario": item["scenario"],
                "kind": item["kind"],
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
        )
    return rows


def run_openai_model(api_key: str, model: str, run_nonce: str, scenarios: list[dict]) -> list[dict]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    rows = []
    group_cache_keys = {}
    miss_counters = {}
    for item in scenarios:
        if item["group"] not in group_cache_keys:
            group_cache_keys[item["group"]] = (
                f"ccp:{run_nonce[:8]}:{model}:{item['group']}"
            )
        if item["kind"] == "exact":
            prompt_cache_key = group_cache_keys[item["group"]]
        else:
            miss_counters[item["group"]] = miss_counters.get(item["group"], 0) + 1
            prompt_cache_key = f"{group_cache_keys[item['group']]}:m{miss_counters[item['group']]}"
        payload = {
            "model": model,
            "input": convert_openai_messages(item["messages"]),
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
        rows.append(
            {
                "provider": "openai",
                "model": model,
                "resolved_model": body.get("model"),
                "group": item["group"],
                "scenario": item["scenario"],
                "kind": item["kind"],
                "status": status,
                "elapsed_s": round(elapsed, 3),
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
        )
    return rows


def summarize(rows: list[dict]) -> dict:
    def median_or_none(values, digits):
        values = [value for value in values if value is not None]
        if not values:
            return None
        return round(statistics.median(values), digits)

    summary = {}
    grouped = {}
    for row in rows:
        grouped.setdefault((row["provider"], row["model"], row["group"]), []).append(row)

    for (provider, model, group), items in grouped.items():
        exact = [item for item in items if item["kind"] == "exact"]
        miss = [item for item in items if item["kind"] == "miss"]
        exact_cold = exact[:1]
        exact_after_warm = exact[1:]

        def usage_value(item: dict, key: str):
            return item["usage"].get(key)

        if provider == "openai":
            cache_key = "cached_tokens"
            input_key = "input_tokens"
        else:
            cache_key = "cached_tokens"
            input_key = "billed_input_tokens"

        summary.setdefault(provider, {}).setdefault(model, {})[group] = {
            "cold_exact_latency_s": exact_cold[0]["elapsed_s"] if exact_cold else None,
            "cold_exact_cost_usd": exact_cold[0]["estimated_cost_usd"] if exact_cold else None,
            "cold_exact_cached_tokens": usage_value(exact_cold[0], cache_key) if exact_cold else None,
            "cold_exact_input_tokens": usage_value(exact_cold[0], input_key) if exact_cold else None,
            "exact_after_warm_median_elapsed_s": median_or_none(
                [item["elapsed_s"] for item in exact_after_warm], 3
            ),
            "miss_median_elapsed_s": median_or_none(
                [item["elapsed_s"] for item in miss], 3
            ),
            "exact_after_warm_median_cost_usd": median_or_none(
                [item["estimated_cost_usd"] for item in exact_after_warm], 6
            ),
            "miss_median_cost_usd": median_or_none(
                [item["estimated_cost_usd"] for item in miss], 6
            ),
            "exact_after_warm_cached_tokens": [
                usage_value(item, cache_key) for item in exact_after_warm
            ],
            "miss_cached_tokens": [usage_value(item, cache_key) for item in miss],
            "exact_after_warm_input_tokens": [
                usage_value(item, input_key) for item in exact_after_warm
            ],
            "miss_input_tokens": [usage_value(item, input_key) for item in miss],
        }
    return summary


def main() -> int:
    cohere_key = os.environ.get("COHERE_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not cohere_key:
        raise SystemExit("COHERE_API_KEY is not set")
    if not openai_key:
        raise SystemExit("OPENAI_API_KEY is not set")

    rows = []
    run_nonce = uuid.uuid4().hex
    scenarios = scenario_groups(run_nonce)
    for model in COHERE_MODELS:
        rows.extend(run_cohere_model(cohere_key, model, scenarios))
    for model in OPENAI_MODELS:
        rows.extend(run_openai_model(openai_key, model, run_nonce, scenarios))

    payload = {
        "run_date": str(date.today()),
        "run_nonce": run_nonce,
        "cohere_models": COHERE_MODELS,
        "openai_models": OPENAI_MODELS,
        "rows": rows,
        "summary": summarize(rows),
    }

    output = f"results/openai-vs-cohere-latency-cost-{date.today().isoformat()}.json"
    os.makedirs("results", exist_ok=True)
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")

    print(json.dumps(payload["summary"], indent=2))
    print(f"\nWrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
