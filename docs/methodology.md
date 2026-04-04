# Methodology

This repo keeps the question intentionally small:

**If an app keeps resending stable context across turns, does the provider expose a useful public prompt-cache effect?**

That means this repo is not trying to settle everything. It does not measure invoice-level billing reconciliation, overall model quality, embeddings, rerank quality, or private deployment options.

## Which File Does What

| File | Why it exists | Use it for |
| --- | --- | --- |
| [docs/stability-study-2026-04-03.md](stability-study-2026-04-03.md) | reruns the key prompt shapes with more repeats and short-delay reuse | strongest evidence in the repo |
| [docs/openai-vs-cohere-latency-cost-2026-04-03.md](openai-vs-cohere-latency-cost-2026-04-03.md) | wider sweep across prompt shapes | large repeated prompt summary and broader comparison |
| [docs/chat-shapes-2026-04-03.md](chat-shapes-2026-04-03.md) | Cohere-only cache-counter behavior across several prompt shapes | best place to inspect `cached_tokens` behavior directly |
| [docs/findings-2026-04-03.md](findings-2026-04-03.md) | earliest repetitive-prefix probe | historical context only |

Related scripts:

- [scripts/cache_stability_study.py](../scripts/cache_stability_study.py)
- [scripts/compare_openai_cohere_latency_cost.py](../scripts/compare_openai_cohere_latency_cost.py)
- [scripts/profile_chat_shapes.py](../scripts/profile_chat_shapes.py)
- [scripts/profile_chat_cache.py](../scripts/profile_chat_cache.py)

## Terms Used Across The Repo

- `cold request`: the first exact request for a prompt family
- `warm request`: a repeated request using the same prompt family
- `miss`: a request where the earliest prefix was changed on purpose, so it should not reuse the same cache entry
- `reported cache hit`: the provider returned `cached_tokens > 0`
- `billing-visible hit`: the request cost was meaningfully lower than the cold request

The reason to care about `cold` versus `warm` is simple: if warm requests do not get cheaper, repeated prompts are not saving you money.

That last distinction matters because `command-r7b-12-2024` could report `cached_tokens` even when billing did not change.

## How The Benchmarks Were Kept Simple

Across the repo, the benchmark tries to keep output-side noise small:

- short outputs
- low temperature
- fixed seed where supported

The important prompt families are:

- **large repeated prompt**: a big stable prefix repeated every turn
- **messages history**: retained multi-turn conversation

The stability study used:

- `1` cold request
- `6` immediate warm repeats
- `4` misses
- `2` delayed warm repeats after `20s`

Those delayed repeats matter because a cache that only helps on back-to-back requests is much less useful in a real application.

All dollar figures in the repo are estimates from:

- published provider pricing
- token usage fields returned by the APIs

They are not invoice exports.

## Reading The Raw Files

The raw files do not all share one schema.

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

Provider token fields differ too:

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

## Safest Way To Read The Results

1. Cohere `command-a-03-2025` did not show a useful public prompt-cache effect in the tested public chat API path.
2. Cohere `command-r7b-12-2024` reported cache counters, but those counters did not behave like a clean billing signal.
3. OpenAI showed real billing-visible savings on repeated prompts, especially in the repeat-heavy stability follow-up.
4. This repo does not support treating Cohere's tested public API path as offering a clear Anthropic/OpenAI-style public prompt-cache contract.
