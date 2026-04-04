### Methodology

This repo asks one narrow question:

**If an app keeps resending stable context across turns, does the provider expose a useful public prompt-cache effect?**

The repo does not try to settle invoice-level billing reconciliation, overall model quality, embeddings, rerank quality, or private deployment options.

#### The Four Docs

[docs/stability-study-2026-04-03.md](stability-study-2026-04-03.md) is the strongest evidence in the repo. It reruns the key prompt shapes with more repeats and a short delay.

[docs/openai-vs-cohere-latency-cost-2026-04-03.md](openai-vs-cohere-latency-cost-2026-04-03.md) is the wider sweep across prompt shapes. It is the source of the large repeated prompt summary in the README.

[docs/chat-shapes-2026-04-03.md](chat-shapes-2026-04-03.md) is where to inspect Cohere's returned cache counters directly across several prompt shapes.

[docs/findings-2026-04-03.md](findings-2026-04-03.md) is the earliest repetitive-prefix probe. Treat it as historical context only.

Related scripts:

1. [scripts/cache_stability_study.py](../scripts/cache_stability_study.py)
2. [scripts/compare_openai_cohere_latency_cost.py](../scripts/compare_openai_cohere_latency_cost.py)
3. [scripts/profile_chat_shapes.py](../scripts/profile_chat_shapes.py)
4. [scripts/profile_chat_cache.py](../scripts/profile_chat_cache.py)

#### Terms

A `cold request` is the first exact request for a prompt family. A `warm request` is a repeated request using the same prompt family. A `miss` is a request where the earliest prefix was changed on purpose, so it should not reuse the same cache entry.

A `reported cache hit` means the provider returned `cached_tokens > 0`. A `billing-visible hit` means the request cost was meaningfully lower than the cold request.

The reason to care about cold versus warm is straightforward: if warm requests do not get cheaper, repeated prompts are not saving you money.

That last distinction matters because `command-r7b-12-2024` could report `cached_tokens` even when billing did not change.

#### Benchmark Shape

Across the repo, the benchmark keeps output-side noise small with short outputs, low temperature, and a fixed seed where supported.

The two prompt families that mattered most were:

1. a **large repeated prompt**, meaning a big stable prefix repeated every turn
2. **messages history**, meaning a retained multi-turn conversation

The stability study used `1` cold request, `6` immediate warm repeats, `4` misses, and `2` delayed warm repeats after `20s`.

Those delayed repeats matter because a cache that only helps on back-to-back requests is much less useful in a real application.

All dollar figures in the repo are estimates from published provider pricing and the token usage fields returned by the APIs. They are not invoice exports.

#### Reading The Raw Files

The raw files do not all share one schema.

Comparison-style files use scenario names like `*_exact_1`, `*_exact_2`, `*_exact_3`, and `*_miss_*`.

The stability-study raw file uses phases instead: `cold`, `warm_immediate`, `miss_immediate`, and `warm_delayed`.

Provider token fields differ too:

1. Cohere uses `billed_input_tokens`, `raw_input_tokens`, and `cached_tokens`
2. OpenAI uses `input_tokens`, `cached_tokens`, and `output_tokens`

#### Limits

1. all tests were on public API paths
2. this repo does not test private deployments or Model Vault
3. latency was noisier than cost
4. the stability study only checked a `20s` delay
5. non-chat endpoints were only smoke-tested
6. this is good enough to reject obvious prompt-caching behavior, not to map every backend detail
7. cost estimates are based on pricing docs and response usage, not invoice reconciliation

#### Safest Reading

1. Cohere `command-a-03-2025` did not show a useful public prompt-cache effect in the tested public chat API path.
2. Cohere `command-r7b-12-2024` reported cache counters, but those counters did not behave like a clean billing signal.
3. OpenAI showed real billing-visible savings on repeated prompts, especially in the repeat-heavy stability follow-up.
4. This repo does not support treating Cohere's tested public API path as offering a clear Anthropic/OpenAI-style public prompt-cache contract.
