# Cache Stability Study: 2026-04-03

Raw data: [results/cache-stability-study-2026-04-03.json](../results/cache-stability-study-2026-04-03.json)

Methodology: [docs/methodology.md](methodology.md)

This follow-up study answers the question the earlier benchmark could not:

- are the cache results stable across repeated warm requests?
- do they survive a short delay?
- do "cache hit" signals still appear on miss cases?

## Parameters

- prompt groups:
  - `size_large`
  - `messages_history_long`
- phases per model and prompt group:
  - `cold`: 1 request
  - `warm_immediate`: 6 exact repeats
  - `miss_immediate`: 4 mutated-prefix misses
  - `warm_delayed`: 2 exact repeats after a `20s` pause

Two hit definitions are used here:

- `reported cache hit`: provider says `cached_tokens > 0`
- `billing-visible hit`: request cost is at least `5%` lower than the cold request for the same prompt group

That distinction matters because Cohere `command-r7b-12-2024` reports `cached_tokens` even when billing does not change.

## Main result

| Model | Prompt group | immediate billing hits | delayed billing hits | miss reported hits | Reading |
| --- | --- | ---: | ---: | ---: | --- |
| `command-a-03-2025` | `size_large` | `0/6` | `0/2` | `0/4` | no prompt-cache signal |
| `command-a-03-2025` | `messages_history_long` | `0/6` | `0/2` | `0/4` | no prompt-cache signal |
| `command-r7b-12-2024` | `size_large` | `0/6` | `0/2` | `4/4` | reported hits without billing hits |
| `command-r7b-12-2024` | `messages_history_long` | `0/6` | `0/2` | `4/4` | reported hits without billing hits |
| `gpt-5.4-mini` | `size_large` | `6/6` | `2/2` | `0/4` | stable billing-visible cache hits |
| `gpt-5.4-mini` | `messages_history_long` | `6/6` | `1/2` | `0/4` | stable immediate hits, one delayed miss |
| `gpt-5.4` | `size_large` | `6/6` | `2/2` | `0/4` | stable billing-visible cache hits |
| `gpt-5.4` | `messages_history_long` | `6/6` | `2/2` | `0/4` | stable billing-visible cache hits |

## Cost behavior

### Large repeated prompt

| Model | cold cost | immediate warm median | delayed warm median |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.087580` | `$0.087580` | `$0.087580` |
| `command-r7b-12-2024` | `$0.001314` | `$0.001314` | `$0.001314` |
| `gpt-5.4-mini` | `$0.011293` | `$0.001444` | `$0.001444` |
| `gpt-5.4` | `$0.037645` | `$0.004237` | `$0.004237` |

Reading:

- `command-a-03-2025` stayed flat on every phase.
- `command-r7b-12-2024` also stayed flat on every phase, even though it reported cache hits.
- both OpenAI models stayed consistently cheap after the cold request.

### Longer multi-turn `messages` history

| Model | cold cost | immediate warm median | delayed warm median |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.004727` | `$0.004727` | `$0.004727` |
| `command-r7b-12-2024` | `$0.000071` | `$0.000071` | `$0.000071` |
| `gpt-5.4-mini` | `$0.001513` | `$0.000303` | `$0.000908` |
| `gpt-5.4` | `$0.005043` | `$0.001010` | `$0.001010` |

Reading:

- `gpt-5.4` was much more stable here than the earlier 2-repeat benchmark suggested.
- `gpt-5.4-mini` stayed stable on the 6 immediate repeats, but one of the 2 delayed repeats came back uncached.
- Cohere `command-a-03-2025` still showed no useful cache effect.

## Latency behavior

This study reinforces the earlier latency conclusion: cost is cleaner than latency.

Examples:

- `command-a-03-2025`, `size_large`, warm immediate latency ranged from `6.000s` to `10.156s` with no cost change.
- `gpt-5.4`, `size_large`, warm immediate latency ranged from `0.805s` to `0.983s` while cost stayed consistently cached.
- `command-r7b-12-2024`, `size_large`, warm immediate latency improved, but billing still did not.

So the stable signal is:

- OpenAI: repeated warm requests usually stayed cheaper
- Cohere Command A: repeated warm requests did not get cheaper
- Cohere R7B: reported cache telemetry stayed present, but still did not become a billing feature

## What changed from the earlier broad comparison

The earlier benchmark only had 2 warm repeats. That was enough to detect obvious behavior, but not enough to separate real instability from sampling noise.

The main update from this follow-up is:

- the earlier weak `gpt-5.4` result on `messages_history_long` was probably under-sampled
- in the stability study, `gpt-5.4` hit `6/6` immediate warm requests and `2/2` delayed warm requests on that same prompt shape

The Command A conclusion did not change.

## Safe conclusion

- Cohere `command-a-03-2025` still does not show a usable public prompt-cache signal.
- Cohere `command-r7b-12-2024` still shows `cached_tokens`, but the stability study strengthens the case that this is not a clean billing-visible prompt cache.
- OpenAI cache behavior looked stable on the large repeated prompt and mostly stable on the long-history prompt.
- A short-delay cache miss is still possible, at least on `gpt-5.4-mini` for the long-history prompt.

## Limits

- this is still a single-day benchmark on public APIs
- delayed testing only used a `20s` pause
- there is still no cache lifetime curve beyond that short delay
- this does not test provider-side routing regions or private deployments
