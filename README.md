# Cohere Cache Profile

> Short version: if your app only stays affordable because repeated prompt prefixes are supposed to get cheaper over time, these tests are a warning sign for Cohere Command A on the public API.

This repo looks at one narrow product question:

**When an app keeps resending stable context across turns, does the provider expose useful public prompt-caching savings?**

If later turns do not get cheaper, long-running chat and agent workflows can cost far more than expected.

It compares Cohere and OpenAI on that question. It is not a general quality review, and it does not try to judge embeddings, rerank, retrieval, or private deployment options.

## Start Here

If your app looks like one of these, this repo is relevant:

- a coding agent with a large system prompt, tool list, and growing chat history
- a multi-turn assistant that keeps sending retained history back every turn
- a RAG app that reuses large repeated instructions or document context
- any workflow where you expect later turns to get cheaper because the prefix is reused

If you are choosing Cohere mainly for rerank, embeddings, retrieval quality, or private deployment, this is the wrong benchmark.

## The Short Answer

- **Cohere `command-a-03-2025`:** no useful public prompt-cache savings showed up in the tested chat paths.
- **Cohere `command-r7b-12-2024`:** it stayed cheap, but the low cost looked like base model pricing, not a clear public cache discount you could budget around.
- **OpenAI:** repeated prompts usually did get cheaper, often by a lot.
- **Latency:** it moved around enough that cost was the better planning signal.

## If You Only Need A Decision

| Your app | What to take from this |
| --- | --- |
| Repeats a large stable prompt every turn | Avoid Cohere Command A public API if your cost model depends on prompt caching |
| Keeps a long retained chat history | Same warning: Command A stayed flat in the tested public API path |
| Only needs a very cheap small model | `command-r7b-12-2024` may still be worth testing, but this repo does not judge model quality |
| Needs predictable cache savings or trustworthy cache counters from the API | Do not rely on Cohere public API based on these results |
| Is being evaluated for rerank, embeddings, retrieval, or private deployment | Out of scope here |

## The Numbers That Matter

Two prompt shapes mattered most:

- **Large repeated prompt:** a big stable prefix repeated every turn
- **Longer multi-turn conversation:** retained `messages` history reused across turns

The `50 turns` column below is a projection using:

`cold turn cost + (49 * repeated turn cost)`

All dollar figures in this repo are estimates from published pricing and API usage fields. They are not invoice exports.

### Large Repeated Prompt

Source: [docs/openai-vs-cohere-latency-cost-2026-04-03.md](docs/openai-vs-cohere-latency-cost-2026-04-03.md)

| Model | cold turn | repeated turn | 50 turns |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.087575` | `$0.087575` | `$4.378750` |
| `command-r7b-12-2024` | `$0.001313` | `$0.001313` | `$0.065650` |
| `gpt-5.4-mini` | `$0.011292` | `$0.001442` | `$0.081950` |
| `gpt-5.4` | `$0.037640` | `$0.004232` | `$0.245008` |

This is the cleanest economic signal in the repo. Command A stays flat. OpenAI drops sharply after the cold turn. R7B stays cheap, but not because this repo found a public cache feature you could treat as reliable for budgeting.

### Longer Multi-Turn Conversation

Source: [docs/stability-study-2026-04-03.md](docs/stability-study-2026-04-03.md)

| Model | cold turn | repeated turn | 50 turns |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.004727` | `$0.004727` | `$0.236350` |
| `command-r7b-12-2024` | `$0.000071` | `$0.000071` | `$0.003550` |
| `gpt-5.4-mini` | `$0.001513` | `$0.000303` | `$0.016360` |
| `gpt-5.4` | `$0.005043` | `$0.001010` | `$0.054533` |

This is closer to a normal chat app. The conclusion still holds: Command A stayed flat, while OpenAI got materially cheaper once the repeated history became reusable.

## What This Supports

- **Against Cohere Command A public API** when your architecture expects later turns to get cheaper because the prefix repeats
- **Against treating R7B's cache counters returned by the API as a trustworthy billing signal**
- **In favor of testing OpenAI first** if repeat-prompt economics are central to the project

## What It Does Not Say

- It does **not** prove Cohere has no internal caching.
- It does **not** compare overall model quality.
- It does **not** judge embeddings, rerank, or retrieval quality.
- It does **not** test private deployments, Model Vault, or other non-public serving setups.
- It does **not** map full cache lifetime; the delay check here was only `20s`, which is enough to catch obvious short-lived reuse but not enough to describe long-term behavior.

## Practical Reading For A Real Project

Use this repo as evidence against **Cohere Command A on the public API** when:

- your agent resends a large stable prompt every turn
- your chatbot carries a lot of retained history
- your budget depends on repeat-prompt caching working predictably

This repo does **not** tell you to reject Cohere in general.

`command-r7b-12-2024` may still be worth testing if:

- you care mainly about very low base cost
- you do not need predictable cache savings
- you do not need trustworthy cache counters from the API

That is a cost recommendation only. It is not a claim that R7B is the right model for your task.

## Where To Read More

Recommended order:

1. [docs/stability-study-2026-04-03.md](docs/stability-study-2026-04-03.md)
   Best single supporting doc if your app repeats stable context and you want the strongest evidence.
2. [docs/openai-vs-cohere-latency-cost-2026-04-03.md](docs/openai-vs-cohere-latency-cost-2026-04-03.md)
   Broader sweep across more prompt shapes.
3. [docs/chat-shapes-2026-04-03.md](docs/chat-shapes-2026-04-03.md)
   Best Cohere-only examples of the cache counters returned by the API.
4. [docs/methodology.md](docs/methodology.md)
   Exact benchmark design, assumptions, and limits.

Historical note:

- [docs/findings-2026-04-03.md](docs/findings-2026-04-03.md) is the earliest repetitive-prefix probe. Treat it as background, not as the main decision document.

Raw data:

- [results/cache-stability-study-2026-04-03.json](results/cache-stability-study-2026-04-03.json)
- [results/openai-vs-cohere-latency-cost-2026-04-03.json](results/openai-vs-cohere-latency-cost-2026-04-03.json)
- [results/chat-shapes-2026-04-03.json](results/chat-shapes-2026-04-03.json)

## Run The Benchmarks

Set `COHERE_API_KEY` and `OPENAI_API_KEY`, then run:

```powershell
python scripts/profile_chat_shapes.py
python scripts/profile_chat_cache.py
python scripts/smoke_nonchat_cache.py
python scripts/compare_openai_cohere_latency_cost.py
python scripts/cache_stability_study.py
```

Each script writes JSON into `results/`.
