# Cache Stability Study: 2026-04-03

> If you read only one supporting doc in this repo, read this one.

Raw data: [results/cache-stability-study-2026-04-03.json](../results/cache-stability-study-2026-04-03.json)
Methodology: [docs/methodology.md](methodology.md)

This is the strongest benchmark in the repo. It checks whether repeated requests actually stay cheaper, whether that still holds after a short delay, and whether a provider reports cache use even when the request was changed on purpose.

That delay check matters because a cache that only helps on back-to-back requests is much less useful in a real app.

All cost figures here are estimates from published pricing and API usage fields. They are not invoice exports.

## At A Glance

| Model | Prompt group | immediate billing hits | delayed billing hits | miss reported hits | What to take from this |
| --- | --- | ---: | ---: | ---: | --- |
| `command-a-03-2025` | large repeated prompt (`size_large`) | `0/6` | `0/2` | `0/4` | no useful public prompt-cache signal |
| `command-a-03-2025` | long retained chat history (`messages_history_long`) | `0/6` | `0/2` | `0/4` | same result |
| `command-r7b-12-2024` | large repeated prompt (`size_large`) | `0/6` | `0/2` | `4/4` | API cache counters existed, but they did not behave like a billing discount |
| `command-r7b-12-2024` | long retained chat history (`messages_history_long`) | `0/6` | `0/2` | `4/4` | same problem |
| `gpt-5.4-mini` | large repeated prompt (`size_large`) | `6/6` | `2/2` | `0/4` | repeated requests stayed cheaper |
| `gpt-5.4-mini` | long retained chat history (`messages_history_long`) | `6/6` | `1/2` | `0/4` | mostly stable, one delayed miss |
| `gpt-5.4` | large repeated prompt (`size_large`) | `6/6` | `2/2` | `0/4` | repeated requests stayed cheaper |
| `gpt-5.4` | long retained chat history (`messages_history_long`) | `6/6` | `2/2` | `0/4` | repeated requests stayed cheaper |

The main point is straightforward: Command A stayed flat, OpenAI got cheaper, and R7B's cache counters were not something you could safely build a billing model around.

## What Was Actually Run

Two prompt groups:

- `size_large`: a large repeated stable prompt
- `messages_history_long`: a longer retained multi-turn conversation

For each model and prompt group:

- `1` cold request
- `6` immediate warm repeats
- `4` intentional misses
- `2` delayed warm repeats after `20s`

Definitions:

- `reported cache hit` means `cached_tokens > 0`
- `billing-visible hit` means the request cost was meaningfully lower than the cold request

That second definition matters because `command-r7b-12-2024` could report `cached_tokens` even when billing did not move.

## Cost View

### Large Repeated Prompt

| Model | cold cost | warm median | delayed warm median |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.087580` | `$0.087580` | `$0.087580` |
| `command-r7b-12-2024` | `$0.001314` | `$0.001314` | `$0.001314` |
| `gpt-5.4-mini` | `$0.011293` | `$0.001444` | `$0.001444` |
| `gpt-5.4` | `$0.037645` | `$0.004237` | `$0.004237` |

For this prompt shape, the economic story is blunt. Command A kept charging the same amount. OpenAI stayed much cheaper after the first request. R7B stayed cheap, but this table does not show a public cache discount you could treat as reliable for budgeting.

### Longer Multi-Turn Conversation

| Model | cold cost | warm median | delayed warm median |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.004727` | `$0.004727` | `$0.004727` |
| `command-r7b-12-2024` | `$0.000071` | `$0.000071` | `$0.000071` |
| `gpt-5.4-mini` | `$0.001513` | `$0.000303` | `$0.000908` |
| `gpt-5.4` | `$0.005043` | `$0.001010` | `$0.001010` |

This is closer to a normal chat app. The conclusion still held. Command A stayed flat. `gpt-5.4` stayed cheaper across the repeated runs. `gpt-5.4-mini` still looked good overall, but one delayed repeat missed cache.

## What To Do With This

If your project expects later turns to get cheaper because a stable prefix keeps repeating, this study argues against **Cohere Command A on the tested public API path**.

If you only care about low base cost, R7B may still be acceptable. Just do not treat its `cached_tokens` field as a trustworthy signal of a real billing discount.

## A Note On Latency

Latency was not the clean story here.

Examples:

- `command-a-03-2025`, `size_large`: warm immediate latency ranged from `6.000s` to `10.156s` with no cost change
- `gpt-5.4`, `size_large`: warm immediate latency ranged from `0.805s` to `0.983s` while cost stayed consistently lower

So the right use of this study is cost planning, not latency promises.

## Limits

- single-day benchmark
- public APIs only
- only a `20s` delay check
- not a full TTL study
- not a model-quality comparison
