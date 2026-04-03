# Methodology

This file explains exactly what the scripts do and how to read the results.

## Scope

The current repo contains four probe scripts:

- [scripts/profile_chat_shapes.py](../scripts/profile_chat_shapes.py)
- [scripts/profile_chat_cache.py](../scripts/profile_chat_cache.py)
- [scripts/smoke_nonchat_cache.py](../scripts/smoke_nonchat_cache.py)
- [scripts/compare_openai_cohere_latency_cost.py](../scripts/compare_openai_cohere_latency_cost.py)

The main teaching value is in `profile_chat_shapes.py`. That script is the clearest version of the experiment.
The newest comparison work is in `compare_openai_cohere_latency_cost.py`.

## Experiment design

For the chat-shape probes (`profile_chat_shapes.py` and `profile_chat_cache.py`):

- endpoint: `POST /v2/chat`
- output cap: `max_tokens=4`
- sampling controls: `temperature=0`, `seed=1`
- goal: keep output cost and randomness small so differences mostly come from the input side

Each shape-probe group has:

- `exact_1`: first request with a payload
- `exact_2`: second request with the same payload, sent immediately after
- `miss_1`: same basic scenario, but the earliest message is changed by prepending a marker such as `MISS-LARGE`

That design is sound for an exploratory cache probe because it asks the simplest useful question:

- does sending the exact same prompt again change billed input, latency, or `cached_tokens`?

It is not strong enough to prove subtle production behavior because the sample size is still small.

## OpenAI comparison design

The cross-provider comparison uses:

- Cohere `POST /v2/chat`
- OpenAI `POST /v1/responses`

OpenAI-specific settings:

- `prompt_cache_key` is kept stable within each scenario group
- `prompt_cache_retention` is set to `in_memory`
- each scenario group gets a fresh run marker inserted into the earliest content so `exact_1` is cold and `exact_2` / `exact_3` are warm repeats inside the same run
- output is kept short

That choice is deliberate. OpenAI's own docs recommend using `prompt_cache_key` consistently and note that prompt caching applies to prompts of 1024 tokens or more. The comparison is trying to give OpenAI a fair chance to show cache behavior, not to hide it behind routing randomness.

Each comparison group has:

- `exact_1`: cold request
- `exact_2`: warm repeat
- `exact_3`: second warm repeat
- `miss_1`, `miss_2`, `miss_3`: same overall shape, but with a changed earliest prefix

One important correction from the earlier draft:

- the shorter `messages_history` case measured `1024` OpenAI input tokens, not `1011`
- it still showed `cached_tokens = 0` on all repeats
- the longer `messages_history_long` case did show cache hits

So the safe lesson is not "1024 always caches." The safe lesson is that crossing the documented threshold was not enough by itself in this benchmark.

## Scenario types

### Size sweep

Uses unique token lists rather than repeated words. This avoids the strongest criticism of the earlier repetitive-prefix experiment.

Examples:

- `size_small_*`
- `size_medium_*`
- `size_large_*`

### Natural prefix

Uses readable multi-paragraph prose instead of token lists.

Important: this is more natural than synthetic token IDs, but it is still generated benchmark text, not real user traffic.

### Messages history

Uses a normal `messages` array with:

- one system message
- alternating user and assistant messages
- one final user message that asks for `OK`

This is the closest test in the repo to real chatbot history reuse.

### Earlier repetitive-prefix probe

Saved in [docs/findings-2026-04-03.md](findings-2026-04-03.md) and [results/chat-cache-2026-04-03.json](../results/chat-cache-2026-04-03.json).

This probe is still useful, but it should not be the first thing a reader trusts because highly repetitive prompts can trigger weird optimizer behavior.

## Meaning of the token fields

The result tables use three token numbers:

- `billed_input_tokens`
- `raw_input_tokens`
- `cached_tokens`

How to interpret them:

- `billed_input_tokens`: closest thing to "what Cohere says you pay for"
- `raw_input_tokens`: closest thing to "how many input tokens Cohere says the model processed"
- `cached_tokens`: Cohere's reported inference-cache hits

The reason this repo exists is that those three fields do not behave the way a new programmer would expect from public prompt caching.

## Example: why `cached_tokens` is confusing

From [results/chat-shapes-2026-04-03.json](../results/chat-shapes-2026-04-03.json), `command-r7b-12-2024`, `size_large_exact_1`:

- `billed_input_tokens = 35003`
- `raw_input_tokens = 35532`
- `cached_tokens = 14512`

If `cached_tokens` were a simple billing discount, the numbers would line up more cleanly. They do not:

- `35532 - 35003 = 529`
- not `14512`

That is why the docs describe `cached_tokens` as real telemetry but not a reliable billing indicator.

## What was methodologically sound

- exact and miss cases are clearly separated
- the same prompt is retried immediately for the cache-hit check
- the cross-provider comparison uses one cold request and two warm repeats, which is more stable than relying on a single retry
- a mutated earliest message is used for the miss check
- `temperature=0` and `seed=1` reduce generation noise
- low `max_tokens` reduces output-side cost noise
- both synthetic and more human-readable prompts were tested
- a real `messages` history was tested, not just a single system prefix

## What was methodologically weak

- only 2 exact repeats and 1 miss per group in the main shape test
- only 3 exact or miss requests per group in the cross-provider comparison
- no delayed retry to test cache lifetime
- no streaming test
- no Model Vault test
- no multi-region or multi-account comparison
- non-chat endpoints were only smoke-tested

Those are limitations, not fatal flaws. The current methodology is good enough to reject obvious prompt-caching behavior, but not good enough to fully map Cohere's backend.

## Best current reading

For a TA or new programmer, the safe interpretation is:

1. The Command A models did not show any usable prompt-cache signal in the tested chat scenarios.
2. `command-r7b-12-2024` did report `cached_tokens`, but the values were inconsistent and did not map cleanly to billed input.
3. Therefore, this repo does not support the claim that Cohere currently offers Anthropic-style public prompt caching on the tested public API path.
