# Cohere Cache Profile

This repo tests one narrow question:

**If your app keeps resending stable context across turns, does Cohere's public API give you useful prompt-caching savings?**

It compares Cohere to OpenAI on that question.

It does **not** try to judge:

- overall model quality
- embeddings or rerank quality
- private deployment / Model Vault
- whether Cohere is a good provider in general

## Bottom Line

If your project depends on repeated prompt reuse to stay cheap, this repo is a warning against **Cohere Command A on the public API**.

- OpenAI showed real cost drops after the first turn.
- Cohere `command-a-03-2025` did not.
- Cohere `command-r7b-12-2024` stayed cheap, but mostly because the model itself is cheap, not because we found a trustworthy public cache discount.
- Latency was noisy. Cost was the useful signal.

## When You Should Care

These results matter if your app looks like one of these:

- a coding agent with a large system prompt, tools, and growing history
- a multi-turn assistant that keeps resending lots of retained history
- a RAG chat app that reuses big repeated instructions or document context
- any workflow where you expect later turns to get cheaper because the prefix is reused

If your project is choosing Cohere mainly for **rerank, embeddings, retrieval, or private deployment**, this repo is not the right benchmark.

## Quick Decision

| Your app | Practical reading |
| --- | --- |
| Repeats a large stable prompt every turn | Avoid Cohere Command A public API if cost depends on prompt caching |
| Keeps a long retained chat history | Same warning: Cohere Command A stayed flat in our tests |
| Only needs a very cheap small model | `command-r7b-12-2024` may be worth testing, but this repo does not judge model quality |
| Needs predictable cache savings or trustworthy cache telemetry | Do not rely on Cohere public API based on these results |
| Is being evaluated for rerank, embeddings, or private deployment | Out of scope for this repo |

## Key Numbers

Two prompt shapes mattered most:

- **Large repeated prompt:** a big stable prefix repeated every turn
- **Longer multi-turn conversation:** retained `messages` history reused across turns

The `50 turns` column below is a projection, not a directly observed 50-turn run.
It uses:

`cold turn cost + (49 * repeated turn cost)`

All dollar figures in this repo are estimated from published pricing and API usage fields. They are not invoice exports.

### Large Repeated Prompt

Source of truth: [docs/openai-vs-cohere-latency-cost-2026-04-03.md](docs/openai-vs-cohere-latency-cost-2026-04-03.md)

| Model | cold turn | repeated turn | 50 turns |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.087575` | `$0.087575` | `$4.378750` |
| `command-r7b-12-2024` | `$0.001313` | `$0.001313` | `$0.065650` |
| `gpt-5.4-mini` | `$0.011292` | `$0.001442` | `$0.081950` |
| `gpt-5.4` | `$0.037640` | `$0.004232` | `$0.245008` |

Project meaning:

- Cohere Command A kept charging full price.
- OpenAI got dramatically cheaper after the first turn.
- R7B stayed cheap, but not because we found a clean public cache feature.

### Longer Multi-Turn Conversation

Source of truth: [docs/stability-study-2026-04-03.md](docs/stability-study-2026-04-03.md)

| Model | cold turn | repeated turn | 50 turns |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.004727` | `$0.004727` | `$0.236350` |
| `command-r7b-12-2024` | `$0.000071` | `$0.000071` | `$0.003550` |
| `gpt-5.4-mini` | `$0.001513` | `$0.000303` | `$0.016360` |
| `gpt-5.4` | `$0.005043` | `$0.001010` | `$0.054533` |

Project meaning:

- Even on a more normal retained-history chat shape, Cohere Command A still stayed flat.
- OpenAI still got materially cheaper.
- OpenAI `gpt-5.4` still looked much cheaper on long retained histories in the stronger repeat-heavy study.

## What We Actually Proved

- **Cohere Command A:** no useful public prompt-cache signal in the tested public chat API path.
  - In the stability study, repeated requests did not get cheaper on either key prompt shape.
- **Cohere R7B:** `cached_tokens` exists, but it is not a trustworthy billing signal.
  - In the stability study it still reported cache hits even when we intentionally changed the prefix to avoid reusing the same cache entry.
- **OpenAI:** repeated warm requests usually stayed cheaper.
  - `gpt-5.4` got cheaper in every repeated run on both key prompt shapes in the stability study.
  - `gpt-5.4-mini` was also stable, except for one delayed miss on the long-history case.
- **Latency:** too noisy to use as the main decision signal.

## What This Means For A Real Project

Use this repo as evidence **against Cohere Command A public API** when:

- your architecture expects later turns to get cheaper because the prefix repeats
- your chatbot keeps a lot of retained history
- your agent resends a large stable prompt every turn
- your budget depends on repeat-prompt caching working predictably

This repo does **not** tell you to reject Cohere in general.

`command-r7b-12-2024` may still be worth testing if:

- you mainly care about very low base cost
- you do not need predictable cache savings
- you do not need trustworthy cache telemetry

That is a cost recommendation only. This repo does not claim that R7B is the right model for your task.

## What This Repo Does Not Prove

- It does not prove that Cohere has no internal caching.
- It does not compare overall model quality.
- It does not judge embeddings, rerank, or retrieval quality.
- It does not test private deployments, Model Vault, or non-public serving setups.
- It does not map full cache lifetime; the delay check was only `20s`.

## Read Next

Recommended order:

- [docs/stability-study-2026-04-03.md](docs/stability-study-2026-04-03.md): read this if your app keeps repeating stable context and you want the strongest evidence
- [docs/openai-vs-cohere-latency-cost-2026-04-03.md](docs/openai-vs-cohere-latency-cost-2026-04-03.md): read this if you want the broader sweep across more prompt shapes
- [docs/chat-shapes-2026-04-03.md](docs/chat-shapes-2026-04-03.md): read this if you want the clearest Cohere-only telemetry examples
- [docs/methodology.md](docs/methodology.md): read this if you want the exact benchmark design and limits

Historical note:

- [docs/findings-2026-04-03.md](docs/findings-2026-04-03.md) is the earliest repetitive-prefix probe. It is not the first thing to trust.

Raw data:

- [results/cache-stability-study-2026-04-03.json](results/cache-stability-study-2026-04-03.json)
- [results/openai-vs-cohere-latency-cost-2026-04-03.json](results/openai-vs-cohere-latency-cost-2026-04-03.json)
- [results/chat-shapes-2026-04-03.json](results/chat-shapes-2026-04-03.json)

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
