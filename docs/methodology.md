# Methodology

This file explains how the repo's benchmarks were run and how to interpret them.

## What The Repo Is Testing

The repo is testing a narrow product question:

- if an app keeps resending stable context across turns, does the provider expose a useful public prompt-cache effect?

The repo is **not** testing:

- invoice-level billing reconciliation
- overall model quality
- embeddings or rerank quality
- private deployment options

## Benchmark Families

### 1. Chat Shapes

Files:

- [scripts/profile_chat_shapes.py](../scripts/profile_chat_shapes.py)
- [docs/chat-shapes-2026-04-03.md](chat-shapes-2026-04-03.md)

Purpose:

- test different Cohere prompt shapes
- inspect `cached_tokens`
- check whether prompt size, natural prose, or `messages` history changes the story

This is the clearest single Cohere-focused experiment in the repo.

### 2. Broad Cross-Provider Comparison

Files:

- [scripts/compare_openai_cohere_latency_cost.py](../scripts/compare_openai_cohere_latency_cost.py)
- [docs/openai-vs-cohere-latency-cost-2026-04-03.md](openai-vs-cohere-latency-cost-2026-04-03.md)

Purpose:

- compare Cohere and OpenAI on several prompt shapes
- estimate cost and latency
- get a first-pass view of whether repeated prompts become cheaper

This is the source of truth for the **large repeated prompt** summary in the README.

### 3. Stability Follow-Up

Files:

- [scripts/cache_stability_study.py](../scripts/cache_stability_study.py)
- [docs/stability-study-2026-04-03.md](stability-study-2026-04-03.md)

Purpose:

- rerun the key prompt shapes with more repeats
- check whether warm hits stay stable
- check whether short-delay reuse still works

This is the strongest evidence in the repo and the source of truth for the README's **longer multi-turn conversation** summary.

### 4. Historical Probe

Files:

- [scripts/profile_chat_cache.py](../scripts/profile_chat_cache.py)
- [docs/findings-2026-04-03.md](findings-2026-04-03.md)

Purpose:

- early repetitive-prefix probe

Use this as historical context, not as the main decision source.

## Key Terms

- `cold request`: the first exact request for a prompt family
- `warm request`: a repeated request using the same prompt family
- `miss`: a request where the earliest prefix was changed on purpose, so it should not reuse the same cache entry
- `reported cache hit`: provider says `cached_tokens > 0`
- `billing-visible hit`: request cost is meaningfully lower than the cold request

Why that last distinction matters:

- Cohere `command-r7b-12-2024` can report `cached_tokens` even when billing does not change

## Core Design Choices

Across the repo, the benchmark tries to keep output-side noise small:

- short outputs
- low temperature
- fixed seed where supported

Cost figures in the repo are estimated from:

- published provider pricing
- token usage fields returned by the APIs

They are not invoice exports.

The important prompt families are:

- **large repeated prompt**: big stable prefix repeated every turn
- **messages history**: retained multi-turn conversation

The stability study used:

- `1` cold request
- `6` immediate warm repeats
- `4` misses
- `2` delayed warm repeats after `20s`

## How To Read The Raw Files

The raw files do **not** all share one schema.

Comparison-style files use scenario names like:

- `*_exact_1`
- `*_exact_2`
- `*_exact_3`
- `*_miss_*`

The stability-study raw file uses phases instead:

- `cold`
- `warm_immediate`
- `miss_immediate`
- `warm_delayed`

Provider token fields also differ:

- Cohere uses `billed_input_tokens`, `raw_input_tokens`, and `cached_tokens`
- OpenAI uses `input_tokens`, `cached_tokens`, and `output_tokens`

## Limits

- all tests were on public API paths
- this repo does not test private deployments or Model Vault
- latency was noisier than cost
- the stability study only checked a `20s` delay
- non-chat endpoints were only smoke-tested
- this is good enough to reject obvious prompt-caching behavior, not to map every backend detail
- cost estimates are based on pricing docs and response usage, not invoice reconciliation

## Safe Reading

The safest high-level interpretation is:

1. Cohere `command-a-03-2025` did not show a useful public prompt-cache effect in the tested public chat API path.
2. Cohere `command-r7b-12-2024` reported cache telemetry, but that telemetry did not behave like a clean billing signal.
3. OpenAI showed real billing-visible savings on repeated prompts, especially in the repeat-heavy stability follow-up.
4. This repo does not support treating Cohere's tested public API path as offering a clear Anthropic/OpenAI-style public prompt-cache contract.
