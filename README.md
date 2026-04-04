# Cohere Cache Profile

This repo tests whether Cohere's public API exposes usable prompt caching, and compares that behavior to OpenAI.

## Executive Summary

If you only need the main result:

- **Cost:** OpenAI showed real cost reductions on repeated prompts. Cohere `command-a-03-2025` did not.
- **Cheap exception:** Cohere `command-r7b-12-2024` stayed inexpensive, but the repo does not show a clean public cache discount behind that price.
- **Latency:** in this sample, latency was noisy and not a dependable win on either provider. Cost was the much stronger signal.
- **Scaling:** for long-running agents with a large repeated prefix, the cost gap becomes material very quickly.
- **Stability follow-up:** the stronger repeat study kept the Command A conclusion intact and showed that the earlier weak `gpt-5.4` long-history result was probably just under-sampled.

How this summary is measured:

- `cold turn` = first exact request for that prompt shape
- `warm repeated turn` = median of the warm exact repeats used by that benchmark
- projections assume the same prompt shape repeats: `cold turn cost + (N - 1) * warm repeated turn cost`

### Large Repeated Prompt

Measured prompt shape:

- OpenAI repeated input: `15026` input tokens
- Cohere repeated input: `35018` billed input tokens

Important: those token counts are provider-specific accounting, not a fair cross-provider token match. The cost numbers are the comparable part.

Cold turn vs warm repeated turn:

| Model | cold turn cost | warm repeated turn cost | observed change |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.087575` | `$0.087575` | `0.0%` |
| `command-r7b-12-2024` | `$0.001313` | `$0.001313` | `0.0%` |
| `gpt-5.4-mini` | `$0.011292` | `$0.001442` | `87.2% cheaper` |
| `gpt-5.4` | `$0.037640` | `$0.004232` | `88.8% cheaper` |

Evidence:

- [results/openai-vs-cohere-latency-cost-2026-04-03.json](results/openai-vs-cohere-latency-cost-2026-04-03.json)
- [Large repeated prompt analysis](docs/openai-vs-cohere-latency-cost-2026-04-03.md#large-repeated-prompt)
- [Methodology](docs/methodology.md#openai-comparison-design)

### Longer Multi-Turn Conversation

Measured prompt shape:

- OpenAI repeated input: `1985` input tokens
- Cohere repeated input: `1885` billed input tokens

This used a retained `messages` history with alternating user and assistant turns.

These numbers come from the follow-up stability study rather than the earlier 2-repeat comparison.

| Model | cold turn cost | warm repeated turn cost | observed change |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.004727` | `$0.004727` | `0.0%` |
| `command-r7b-12-2024` | `$0.000071` | `$0.000071` | `0.0%` |
| `gpt-5.4-mini` | `$0.001513` | `$0.000303` | `80.0% cheaper` |
| `gpt-5.4` | `$0.005043` | `$0.001010` | `80.0% cheaper` |

Evidence:

- [results/cache-stability-study-2026-04-03.json](results/cache-stability-study-2026-04-03.json)
- [Stability study analysis](docs/stability-study-2026-04-03.md#longer-multi-turn-messages-history)
- [Methodology](docs/methodology.md#stability-study-design)

### Latency

Caching was **not** a clean latency story in this sample.

Large repeated prompt, cold vs warm:

| Model | cold latency | warm repeated latency | reading |
| --- | ---: | ---: | --- |
| `command-a-03-2025` | `6.011s` | `9.306s` | worse |
| `command-r7b-12-2024` | `1.619s` | `1.153s` | better, but no cost change |
| `gpt-5.4-mini` | `0.702s` | `0.780s` | roughly flat |
| `gpt-5.4` | `1.745s` | `6.062s` | worse in this run |

So the practical takeaway is:

- treat **cost** as the reliable caching benefit
- do **not** budget around a latency improvement from these results alone

Evidence:

- [Latency tables](docs/openai-vs-cohere-latency-cost-2026-04-03.md#large-repeated-prompt)
- [Raw comparison results](results/openai-vs-cohere-latency-cost-2026-04-03.json)

### Cost Scaling

These projections use the measured formula:

`cold turn cost + (N - 1) * warm repeated turn cost`

Sources:

- large repeated prompt: broader cross-provider comparison
- longer multi-turn conversation: follow-up stability study

#### Large Repeated Prompt

| Model | 10 turns | 50 turns |
| --- | ---: | ---: |
| `command-a-03-2025` | `$0.875750` | `$4.378750` |
| `command-r7b-12-2024` | `$0.013130` | `$0.065650` |
| `gpt-5.4-mini` | `$0.024270` | `$0.081950` |
| `gpt-5.4` | `$0.075728` | `$0.245008` |

#### Longer Multi-Turn Conversation

| Model | 10 turns | 50 turns |
| --- | ---: | ---: |
| `command-a-03-2025` | `$0.047270` | `$0.236350` |
| `command-r7b-12-2024` | `$0.000710` | `$0.003550` |
| `gpt-5.4-mini` | `$0.004240` | `$0.016360` |
| `gpt-5.4` | `$0.014133` | `$0.054533` |

What this means:

- if your app keeps repeating a large stable prefix, **Command A scales almost linearly**
- OpenAI cost **bends downward** after the first turn because the repeated prefix is cached
- `command-r7b-12-2024` is still cheap, but that is because the model itself is cheap, not because the public cache story is clear
- on the long-history case, the stronger follow-up study makes `gpt-5.4` look much better than the original 2-repeat sample suggested

Evidence:

- [Stability study](docs/stability-study-2026-04-03.md)
- [Raw comparison results](results/openai-vs-cohere-latency-cost-2026-04-03.json)
- [Raw stability results](results/cache-stability-study-2026-04-03.json)

### Stability Follow-Up

Focused repeat study:

- `1` cold request
- `6` immediate warm repeats
- `4` misses
- `2` warm repeats after `20s`

What changed:

- `command-a-03-2025` still showed `0/6` immediate billing hits and `0/2` delayed billing hits on both key prompt shapes
- `gpt-5.4` large repeated prompt hit `6/6` immediate and `2/2` delayed warm requests
- `gpt-5.4` long retained history also hit `6/6` immediate and `2/2` delayed warm requests
- `gpt-5.4-mini` was also stable except for `1` delayed miss on the long-history case
- `command-r7b-12-2024` reported cache hits even on `4/4` miss cases, which makes the telemetry hard to trust as a public cache signal

This is the strongest answer in the repo to "did we repeat enough times to judge stability?":

- enough to reject obvious stability on Cohere Command A
- enough to show real short-run stability on OpenAI
- not enough to fully map TTL or region-dependent routing behavior

Evidence:

- [Stability study](docs/stability-study-2026-04-03.md)
- [Raw stability results](results/cache-stability-study-2026-04-03.json)
- [Methodology](docs/methodology.md#stability-study-design)

### Where Cohere Public API Is a Poor Fit

These are the places where Cohere public API looks weak **relative to providers with documented prompt caching**:

- long-running coding agents that resend large repo context every turn
- assistants with heavy system prompts, tool schemas, or retained history that stay mostly stable across turns
- workloads where you need prompt caching to lower cost predictably
- teaching, QA, or ops setups where cache telemetry needs to be easy to interpret
- systems where architecture or pricing depends on a provider-exposed cache contract

The most important nuance:

- `command-r7b-12-2024` may still be a valid choice if you only want a very cheap model
- it is **not** evidence that Cohere public prompt caching is working like OpenAI or Anthropic prompt caching

Evidence:

- [Command R7B examples](docs/chat-shapes-2026-04-03.md#prompt-sizes)
- [Why `cached_tokens` is confusing](docs/methodology.md#example-why-cached_tokens-is-confusing)

## Start Here

- methodology and glossary: [docs/methodology.md](docs/methodology.md)
- latency/cost comparison: [docs/openai-vs-cohere-latency-cost-2026-04-03.md](docs/openai-vs-cohere-latency-cost-2026-04-03.md)
- stability follow-up: [docs/stability-study-2026-04-03.md](docs/stability-study-2026-04-03.md)
- broader chat-shape summary: [docs/chat-shapes-2026-04-03.md](docs/chat-shapes-2026-04-03.md)
- earlier repetitive-prefix notes: [docs/findings-2026-04-03.md](docs/findings-2026-04-03.md)
- raw comparison results: [results/openai-vs-cohere-latency-cost-2026-04-03.json](results/openai-vs-cohere-latency-cost-2026-04-03.json)
- raw stability results: [results/cache-stability-study-2026-04-03.json](results/cache-stability-study-2026-04-03.json)
- raw chat-shape results: [results/chat-shapes-2026-04-03.json](results/chat-shapes-2026-04-03.json)
- raw earlier chat results: [results/chat-cache-2026-04-03.json](results/chat-cache-2026-04-03.json)
- raw non-chat smoke results: [results/nonchat-cache-smoke-2026-04-03.json](results/nonchat-cache-smoke-2026-04-03.json)

## How To Read The Results

Each scenario name follows this pattern:

- `*_exact_1`: first request with a specific payload
- `*_exact_2`: second request with the exact same payload, sent immediately after `exact_1`
- `*_exact_3`: third request with the exact same payload
- `*_miss_*`: same scenario shape, but the earliest content is changed

The key fields are:

- `billed_input_tokens`: what Cohere says counts as billable input
- `raw_input_tokens`: total input tokens Cohere says were processed
- `cached_tokens`: provider-reported cache hits

Important:

- on Cohere, `cached_tokens` does **not** map cleanly to billing
- on OpenAI, the main comparison uses cold `exact_1` versus warm `exact_2` and `exact_3`
- the miss cases are supporting evidence, not the main baseline

## Limits

- this is an exploratory benchmark, not a formal audit
- all runs were on public API paths, not private deployments or Model Vault
- latency was noisier than cost
- the stability study only checked a `20s` delay, not full cache lifetime
- `v2/embed` and `v2/rerank` were only smoke-tested
- the prompts are benchmark prompts, not real production traffic

## Run

Set `COHERE_API_KEY` and `OPENAI_API_KEY`, then run:

```powershell
python scripts/profile_chat_shapes.py
python scripts/profile_chat_cache.py
python scripts/smoke_nonchat_cache.py
python scripts/compare_openai_cohere_latency_cost.py
python scripts/cache_stability_study.py
```

Each script writes JSON into `results/`.
