# OpenAI vs Cohere: Broad Comparison

Raw data: [results/openai-vs-cohere-latency-cost-2026-04-03.json](../results/openai-vs-cohere-latency-cost-2026-04-03.json)

Methodology: [docs/methodology.md](methodology.md)

Use this document for the **broad first pass** across several prompt shapes.

If you care mainly about the strongest repeat-heavy evidence, read [docs/stability-study-2026-04-03.md](stability-study-2026-04-03.md) first.

Cost figures in this file are estimates from published pricing and API usage fields, not invoice exports.

## What This File Adds

Compared with the stability study, this file covers more prompt shapes:

- large repeated prompt
- natural-language prefix
- shorter `messages` history
- longer `messages` history

It is especially useful for:

- the large repeated prompt summary
- the natural-language prefix result
- the shorter-history edge case

## Core Result

OpenAI showed meaningful cost drops on repeated prompts.

Cohere `command-a-03-2025` did not.

Latency was noisy and much less useful than cost.

## Results By Prompt Shape

### Large Repeated Prompt

| Model | cold cost | warm cost | reading |
| --- | ---: | ---: | --- |
| `command-a-03-2025` | `$0.087575` | `$0.087575` | no cost change |
| `command-r7b-12-2024` | `$0.001313` | `$0.001313` | cheap, but not a clean cache discount |
| `gpt-5.4-mini` | `$0.011292` | `$0.001442` | much cheaper after the first turn |
| `gpt-5.4` | `$0.037640` | `$0.004232` | much cheaper after the first turn |

### Natural-Language Prefix

| Model | cold cost | warm cost | reading |
| --- | ---: | ---: | --- |
| `command-a-03-2025` | `$0.006302` | `$0.006302` | no cost change |
| `command-r7b-12-2024` | `$0.000094` | `$0.000094` | cheap, but telemetry still unclear |
| `gpt-5.4-mini` | `$0.001808` | `$0.000599` | cheaper after the first turn |
| `gpt-5.4` | `$0.006027` | `$0.001131` | cheaper after the first turn |

This matters because it shows the result was not limited to synthetic token lists.

### Shorter `messages` History

| Model | cold cost | warm cost | reading |
| --- | ---: | ---: | --- |
| `command-a-03-2025` | `$0.002395` | `$0.002395` | no cost change |
| `command-r7b-12-2024` | `$0.000036` | `$0.000036` | cheap, telemetry still unclear |
| `gpt-5.4-mini` | `$0.000790` | `$0.000790` | no visible cache effect in this sample |
| `gpt-5.4` | `$0.002635` | `$0.002635` | no visible cache effect in this sample |

This is the useful edge case: a shorter retained history did **not** automatically produce cache savings on OpenAI.

### Longer `messages` History

This section is retained as the original 2-repeat sample.

For the repo's current long-history summary, use [docs/stability-study-2026-04-03.md](stability-study-2026-04-03.md), which has more repeats and is the stronger source of truth.

| Model | cold cost | warm cost | reading |
| --- | ---: | ---: | --- |
| `command-a-03-2025` | `$0.004722` | `$0.004722` | no cost change |
| `command-r7b-12-2024` | `$0.000071` | `$0.000071` | cheap, telemetry still unclear |
| `gpt-5.4-mini` | `$0.001511` | `$0.000302` | cheaper after the first turn |
| `gpt-5.4` | `$0.005038` | `$0.003022` | under-sampled here; see stability study |

## Scaling

Formula:

`cold turn cost + (N - 1) * warm turn cost`

### Large Repeated Prompt

| Model | 10 turns | 50 turns |
| --- | ---: | ---: |
| `command-a-03-2025` | `$0.875750` | `$4.378750` |
| `command-r7b-12-2024` | `$0.013130` | `$0.065650` |
| `gpt-5.4-mini` | `$0.024270` | `$0.081950` |
| `gpt-5.4` | `$0.075728` | `$0.245008` |

### Longer Multi-Turn Conversation

This table is kept for completeness from the first-pass comparison.

For the repo's current long-history projections, use the README or [docs/stability-study-2026-04-03.md](stability-study-2026-04-03.md).

| Model | 10 turns | 50 turns |
| --- | ---: | ---: |
| `command-a-03-2025` | `$0.047220` | `$0.236100` |
| `command-r7b-12-2024` | `$0.000710` | `$0.003550` |
| `gpt-5.4-mini` | `$0.004229` | `$0.016309` |
| `gpt-5.4` | `$0.032236` | `$0.153116` |

## Safe Reading

- This file is the broad sweep, not the strongest stability evidence.
- It supports the main claim that Cohere Command A stayed flat while OpenAI usually got cheaper.
- For final long-history conclusions, prefer the stability study.
