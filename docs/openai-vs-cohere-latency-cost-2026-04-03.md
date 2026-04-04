# OpenAI vs Cohere: Latency and Cost

Raw data: [results/openai-vs-cohere-latency-cost-2026-04-03.json](../results/openai-vs-cohere-latency-cost-2026-04-03.json)

Methodology: [docs/methodology.md](methodology.md)

Stability follow-up: [docs/stability-study-2026-04-03.md](stability-study-2026-04-03.md)

Official references:

- OpenAI prompt caching guide: <https://developers.openai.com/api/docs/guides/prompt-caching>
- OpenAI pricing: <https://openai.com/api/pricing/>
- Cohere Command A pricing: <https://docs.cohere.com/docs/command-a>
- Cohere Command R7B pricing: <https://docs.cohere.com/v2/docs/command-r7b>

## Baseline

This document uses a simpler and more reliable baseline than the earlier draft:

- `exact_1` = cold request
- `exact_2` and `exact_3` = warm repeated requests
- warm values in the tables below are the median of `exact_2` and `exact_3`

The miss cases are still recorded, but they are supporting evidence, not the main baseline.

## Prompt groups

- `size_large`
  - OpenAI input: `15026` tokens
  - Cohere billed input: `35018` tokens
- `natural_prefix`
  - OpenAI input: `2381` tokens
  - Cohere billed input: `2513` tokens
- `messages_history`
  - OpenAI input: `1024` tokens
  - Cohere billed input: `954` tokens
- `messages_history_long`
  - OpenAI input: `1985` tokens
  - Cohere billed input: `1885` tokens

Those token counts come from each provider's own usage accounting. They are useful for reproducing the tests, but the cost numbers are the better cross-provider comparison.

## Main result

Cost moved in a meaningful way on OpenAI and did not move in a meaningful way on Cohere Command A.

Latency did not give a stable, dependable story.

Important: this file is the broader first-pass comparison. For the stronger follow-up on repeated warm-hit stability, especially the long-history case, read [docs/stability-study-2026-04-03.md](stability-study-2026-04-03.md).

## Large repeated prompt

| Model | cold latency | warm repeated latency | cold cost | warm repeated cost | cached tokens on warm |
| --- | ---: | ---: | ---: | ---: | ---: |
| `command-a-03-2025` | `6.011s` | `9.306s` | `$0.087575` | `$0.087575` | `0` |
| `command-r7b-12-2024` | `1.619s` | `1.153s` | `$0.001313` | `$0.001313` | mixed: `35536`, `512` |
| `gpt-5.4-mini` | `0.702s` | `0.780s` | `$0.011292` | `$0.001442` | `14592` |
| `gpt-5.4` | `1.745s` | `6.062s` | `$0.037640` | `$0.004232` | `14848` |

Reading:

- `gpt-5.4-mini` got about `87.2%` cheaper after the first turn.
- `gpt-5.4` got about `88.8%` cheaper after the first turn.
- `command-a-03-2025` showed no cost change at all.
- `command-r7b-12-2024` stayed cheap, but that was base model pricing, not a clean cache discount.

## Natural-language prefix

| Model | cold latency | warm repeated latency | cold cost | warm repeated cost | cached tokens on warm |
| --- | ---: | ---: | ---: | ---: | ---: |
| `command-a-03-2025` | `1.822s` | `2.062s` | `$0.006302` | `$0.006302` | `0` |
| `command-r7b-12-2024` | `0.258s` | `0.239s` | `$0.000094` | `$0.000094` | mixed: `528`, `3040` |
| `gpt-5.4-mini` | `0.937s` | `0.676s` | `$0.001808` | `$0.000599` | `1792` |
| `gpt-5.4` | `1.931s` | `2.070s` | `$0.006027` | `$0.001131` | `2176` |

Reading:

- `gpt-5.4-mini` got about `66.9%` cheaper after the first turn.
- `gpt-5.4` got about `81.2%` cheaper after the first turn.
- `command-a-03-2025` still showed no cost movement.

## Multi-turn `messages` history

### Shorter history

| Model | cold latency | warm repeated latency | cold cost | warm repeated cost | cached tokens on warm |
| --- | ---: | ---: | ---: | ---: | ---: |
| `command-a-03-2025` | `1.173s` | `2.582s` | `$0.002395` | `$0.002395` | `0` |
| `command-r7b-12-2024` | `0.223s` | `0.186s` | `$0.000036` | `$0.000036` | mixed: `528`, `1536` |
| `gpt-5.4-mini` | `0.710s` | `0.629s` | `$0.000790` | `$0.000790` | `0` |
| `gpt-5.4` | `1.817s` | `1.929s` | `$0.002635` | `$0.002635` | `0` |

Reading:

- this shorter history did not show a usable cost effect on OpenAI or Cohere
- the OpenAI warm rows also stayed at `cached_tokens = 0`
- this means the documented `1024`-token threshold was not enough by itself to guarantee a visible cache hit in this benchmark

### Longer history

| Model | cold latency | warm repeated latency | cold cost | warm repeated cost | cached tokens on warm |
| --- | ---: | ---: | ---: | ---: | ---: |
| `command-a-03-2025` | `0.652s` | `2.250s` | `$0.004722` | `$0.004722` | `0` |
| `command-r7b-12-2024` | `0.253s` | `0.234s` | `$0.000071` | `$0.000071` | `2528` |
| `gpt-5.4-mini` | `0.789s` | `0.860s` | `$0.001511` | `$0.000302` | `1792` |
| `gpt-5.4` | `0.903s` | `1.335s` | `$0.005038` | `$0.003022` | mixed: `0`, `1792` |

Reading:

- `gpt-5.4-mini` got about `80.0%` cheaper after the first turn.
- `gpt-5.4` got about `40.0%` cheaper after the first turn.
- `command-a-03-2025` still stayed flat.

## Scaling projections

These projections use:

`cold turn cost + (N - 1) * warm repeated turn cost`

### Large repeated prompt

| Model | 10 turns | 50 turns |
| --- | ---: | ---: |
| `command-a-03-2025` | `$0.875750` | `$4.378750` |
| `command-r7b-12-2024` | `$0.013130` | `$0.065650` |
| `gpt-5.4-mini` | `$0.024270` | `$0.081950` |
| `gpt-5.4` | `$0.075728` | `$0.245008` |

### Longer multi-turn conversation

| Model | 10 turns | 50 turns |
| --- | ---: | ---: |
| `command-a-03-2025` | `$0.047220` | `$0.236100` |
| `command-r7b-12-2024` | `$0.000710` | `$0.003550` |
| `gpt-5.4-mini` | `$0.004229` | `$0.016309` |
| `gpt-5.4` | `$0.032236` | `$0.153116` |

## Safe conclusion

- OpenAI showed real cost savings on repeated prompts once the prompt shape was cache-friendly.
- Cohere `command-a-03-2025` did not show a usable public prompt-cache signal in any tested case.
- Cohere `command-r7b-12-2024` did report `cached_tokens`, but the billing behavior still did not look like a clear public cache contract.
- Latency was too noisy to treat as a dependable benefit from caching in this sample.

## What this does not prove

- It does not prove that Cohere has no internal caching.
- It does not prove exact production latency numbers.
- It does not compare model quality or capability.
- It does not cover Model Vault or private deployment options.

It does show that, on the tested public API paths, OpenAI's prompt caching behaves like a real cost feature, while Cohere Command A does not.
