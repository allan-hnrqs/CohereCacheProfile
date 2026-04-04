# Cache Stability Study: 2026-04-03

Raw data: [results/cache-stability-study-2026-04-03.json](../results/cache-stability-study-2026-04-03.json)

Methodology: [docs/methodology.md](methodology.md)

This is the strongest benchmark in the repo.

It asks:

- do repeated warm requests stay cheaper?
- does that still hold after a short delay?
- does the provider report cache hits even when it should not?

Cost figures in this file are estimates from published pricing and API usage fields, not invoice exports.

## What Was Tested

Prompt groups:

- `size_large`: large repeated stable prompt
- `messages_history_long`: longer retained multi-turn conversation

Per model and prompt group:

- `1` cold request
- `6` immediate warm repeats
- `4` misses
- `2` delayed warm repeats after `20s`

Important definitions:

- `reported cache hit` = `cached_tokens > 0`
- `billing-visible hit` = request cost is meaningfully lower than the cold request

## Main Result

| Model | Prompt group | immediate billing hits | delayed billing hits | miss reported hits | Practical reading |
| --- | --- | ---: | ---: | ---: | --- |
| `command-a-03-2025` | `size_large` | `0/6` | `0/2` | `0/4` | no useful public prompt-cache signal |
| `command-a-03-2025` | `messages_history_long` | `0/6` | `0/2` | `0/4` | no useful public prompt-cache signal |
| `command-r7b-12-2024` | `size_large` | `0/6` | `0/2` | `4/4` | telemetry exists, but not as a billing signal |
| `command-r7b-12-2024` | `messages_history_long` | `0/6` | `0/2` | `4/4` | same problem |
| `gpt-5.4-mini` | `size_large` | `6/6` | `2/2` | `0/4` | stable billing-visible savings |
| `gpt-5.4-mini` | `messages_history_long` | `6/6` | `1/2` | `0/4` | mostly stable, one delayed miss |
| `gpt-5.4` | `size_large` | `6/6` | `2/2` | `0/4` | stable billing-visible savings |
| `gpt-5.4` | `messages_history_long` | `6/6` | `2/2` | `0/4` | stable billing-visible savings |

## Cost Tables

### Large Repeated Prompt

| Model | cold cost | warm median | delayed warm median |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.087580` | `$0.087580` | `$0.087580` |
| `command-r7b-12-2024` | `$0.001314` | `$0.001314` | `$0.001314` |
| `gpt-5.4-mini` | `$0.011293` | `$0.001444` | `$0.001444` |
| `gpt-5.4` | `$0.037645` | `$0.004237` | `$0.004237` |

Meaning:

- Cohere Command A stayed flat.
- OpenAI stayed much cheaper after the cold request.
- R7B stayed cheap, but not because this study found a trustworthy public cache discount.

### Longer Multi-Turn Conversation

| Model | cold cost | warm median | delayed warm median |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.004727` | `$0.004727` | `$0.004727` |
| `command-r7b-12-2024` | `$0.000071` | `$0.000071` | `$0.000071` |
| `gpt-5.4-mini` | `$0.001513` | `$0.000303` | `$0.000908` |
| `gpt-5.4` | `$0.005043` | `$0.001010` | `$0.001010` |

Meaning:

- Cohere Command A still stayed flat.
- `gpt-5.4` was much more stable than the earlier 2-repeat sample suggested.
- `gpt-5.4-mini` still looked good overall, but one delayed repeat missed cache.

## Why This Matters

If your project expects later turns to get cheaper because the prompt repeats:

- Cohere Command A looked like a poor fit on the tested public API path.
- OpenAI looked much safer.

If your project only cares about low base cost:

- R7B may still be acceptable.
- But do not treat its `cached_tokens` field as a trustworthy public cache contract.

## Latency

Latency was not the clean story here.

Examples:

- `command-a-03-2025`, `size_large`: warm immediate latency ranged from `6.000s` to `10.156s` with no cost change
- `gpt-5.4`, `size_large`: warm immediate latency ranged from `0.805s` to `0.983s` while cost stayed consistently lower

Use this study mainly for **cost** conclusions, not latency promises.

## Limits

- single-day benchmark
- public APIs only
- only a `20s` delay check
- not a full TTL study
- not a model-quality comparison
