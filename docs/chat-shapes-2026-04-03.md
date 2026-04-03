# Chat Shapes Summary: 2026-04-03

This file answers three narrower questions:

1. Does prompt size matter?
2. Do natural prompts behave differently from synthetic token lists?
3. Does multi-turn `messages` history show caching?

Raw data: [results/chat-shapes-2026-04-03.json](../results/chat-shapes-2026-04-03.json)

Methodology and glossary: [docs/methodology.md](methodology.md)

## How to read one row

Example:

`command-r7b-12-2024` + `size_large_exact_1` -> `35003 | 35532 | 14512`

This means:

- Cohere reported `35003` billable input tokens
- Cohere reported `35532` total processed input tokens
- Cohere reported `14512` cached tokens

It does **not** mean "35532 tokens were repeated and only 35003 were billed because 14512 were discounted."

Why not:

- `35532 - 35003 = 529`
- not `14512`

That mismatch is one of the main reasons this repo treats `cached_tokens` as unclear telemetry rather than a clean public cache contract.

## Prompt sizes

### `command-a-03-2025`

| Scenario | billed input | raw input | cached tokens |
| --- | ---: | ---: | ---: |
| `size_small_exact_1` | 1753 | 2282 | 0 |
| `size_medium_exact_1` | 14003 | 14532 | 0 |
| `size_large_exact_1` | 35003 | 35532 | 0 |
| `size_small_miss_1` | 1757 | 2286 | 0 |
| `size_medium_miss_1` | 14007 | 14536 | 0 |
| `size_large_miss_1` | 35007 | 35536 | 0 |

Result: no cache signal across small, medium, or large unique prefixes.

### `command-a-reasoning-08-2025`

| Scenario | billed input | raw input | cached tokens |
| --- | ---: | ---: | ---: |
| `size_small_exact_1` | 1753 | 3173 | 0 |
| `size_medium_exact_1` | 14003 | 15423 | 0 |
| `size_large_exact_1` | 35003 | 36423 | 0 |
| `size_small_miss_1` | 1757 | 3177 | 0 |
| `size_medium_miss_1` | 14007 | 15427 | 0 |
| `size_large_miss_1` | 35007 | 36427 | 0 |

Result: same conclusion as Command A.

### `command-r7b-12-2024`

| Scenario | billed input | raw input | cached tokens |
| --- | ---: | ---: | ---: |
| `size_small_exact_1` | 1753 | 2282 | 512 |
| `size_small_exact_2` | 1753 | 2282 | 2272 |
| `size_small_miss_1` | 1757 | 2286 | 512 |
| `size_medium_exact_1` | 14003 | 14532 | 512 |
| `size_medium_exact_2` | 14003 | 14532 | 14528 |
| `size_medium_miss_1` | 14007 | 14536 | 512 |
| `size_large_exact_1` | 35003 | 35532 | 14512 |
| `size_large_exact_2` | 35003 | 35532 | 2272 |
| `size_large_miss_1` | 35007 | 35536 | 512 |

Result: `cached_tokens` exists, but it changes unpredictably across exact repeats and does not show a clean billing effect.

## Natural-language prefix

These prompts used prose paragraphs instead of repeated token lists.

| Model | Scenario | billed input | raw input | cached tokens |
| --- | --- | ---: | ---: | ---: |
| `command-a-03-2025` | `natural_prefix_exact_1` | 2498 | 3027 | 0 |
| `command-a-03-2025` | `natural_prefix_exact_2` | 2498 | 3027 | 0 |
| `command-a-03-2025` | `natural_prefix_miss_1` | 2505 | 3034 | 0 |
| `command-a-reasoning-08-2025` | `natural_prefix_exact_1` | 2498 | 3918 | 0 |
| `command-a-reasoning-08-2025` | `natural_prefix_exact_2` | 2498 | 3918 | 0 |
| `command-a-reasoning-08-2025` | `natural_prefix_miss_1` | 2505 | 3925 | 0 |
| `command-r7b-12-2024` | `natural_prefix_exact_1` | 2498 | 3027 | 512 |
| `command-r7b-12-2024` | `natural_prefix_exact_2` | 2498 | 3027 | 3024 |
| `command-r7b-12-2024` | `natural_prefix_miss_1` | 2505 | 3034 | 512 |

Result:

- natural prompts did not unlock cache behavior on the two Command A models
- `r7b` again showed unstable `cached_tokens` values on exact repeats without a billed-input drop

## Multi-turn `messages` history

These prompts used a normal conversation history with alternating user and assistant turns.

| Model | Scenario | billed input | raw input | cached tokens |
| --- | --- | ---: | ---: | ---: |
| `command-a-03-2025` | `messages_history_exact_1` | 939 | 1532 | 0 |
| `command-a-03-2025` | `messages_history_exact_2` | 939 | 1532 | 0 |
| `command-a-03-2025` | `messages_history_miss_1` | 946 | 1539 | 0 |
| `command-a-reasoning-08-2025` | `messages_history_exact_1` | 939 | 2511 | 0 |
| `command-a-reasoning-08-2025` | `messages_history_exact_2` | 939 | 2511 | 0 |
| `command-a-reasoning-08-2025` | `messages_history_miss_1` | 946 | 2518 | 0 |
| `command-r7b-12-2024` | `messages_history_exact_1` | 939 | 1532 | 512 |
| `command-r7b-12-2024` | `messages_history_exact_2` | 939 | 1532 | 1520 |
| `command-r7b-12-2024` | `messages_history_miss_1` | 946 | 1539 | 512 |

Result:

- normal multi-turn history still showed no cache signal on the two Command A models
- `r7b` still looked inconsistent rather than productized

## Safe conclusion

- Yes, prompt size was tested.
- Yes, natural-language prompts were tested.
- Yes, multi-turn `messages` history was tested.
- The two Command A models still showed no usable prompt-cache signal.
- `command-r7b-12-2024` exposed `cached_tokens`, but the values were unstable and not enough to treat as reliable public prompt caching.
