OpenAI vs Cohere: Broad Comparison
---

This file broadens the prompt shapes. It is useful when you want more than the single strongest result, but it is not the final word on the long-history case. For that, use [docs/stability-study-2026-04-03.md](stability-study-2026-04-03.md).

Raw data: [results/openai-vs-cohere-latency-cost-2026-04-03.json](../results/openai-vs-cohere-latency-cost-2026-04-03.json)
Methodology: [docs/methodology.md](methodology.md)

All cost figures here are estimates from published pricing and API usage fields. They are not invoice exports.

What This Adds
---

Compared with the stability study, this file adds:

- a natural-language prefix case
- a shorter `messages` history case
- the original first-pass long-history sample

It is still the source of truth for the README's large repeated prompt summary.

The Broad Pattern
---

OpenAI showed meaningful cost drops on repeated prompts. Cohere `command-a-03-2025` did not. Latency moved around enough that cost was easier to trust than response time.

The practical point is that a provider that stays flat on repeated prompt shapes is a worse fit for workloads that depend on prompt caching to control cost.

Prompt Shapes
---

Large Repeated Prompt
---

| Model | cold cost | warm cost | What to take from this |
| --- | ---: | ---: | --- |
| `command-a-03-2025` | `$0.087575` | `$0.087575` | no cost change |
| `command-r7b-12-2024` | `$0.001313` | `$0.001313` | cheap, but not a clean cache discount |
| `gpt-5.4-mini` | `$0.011292` | `$0.001442` | much cheaper after the first turn |
| `gpt-5.4` | `$0.037640` | `$0.004232` | much cheaper after the first turn |

This is the cleanest comparison in the file and the most important one for agent-style workloads with a large stable prefix.

Natural-Language Prefix
---

| Model | cold cost | warm cost | What to take from this |
| --- | ---: | ---: | --- |
| `command-a-03-2025` | `$0.006302` | `$0.006302` | no cost change |
| `command-r7b-12-2024` | `$0.000094` | `$0.000094` | cheap, but the API cache counters still did not explain the billing |
| `gpt-5.4-mini` | `$0.001808` | `$0.000599` | cheaper after the first turn |
| `gpt-5.4` | `$0.006027` | `$0.001131` | cheaper after the first turn |

This matters because it shows the pattern was not limited to synthetic token lists or obviously artificial prompts.

Shorter `messages` History
---

| Model | cold cost | warm cost | What to take from this |
| --- | ---: | ---: | --- |
| `command-a-03-2025` | `$0.002395` | `$0.002395` | no cost change |
| `command-r7b-12-2024` | `$0.000036` | `$0.000036` | cheap, but the API cache counters still did not explain the billing |
| `gpt-5.4-mini` | `$0.000790` | `$0.000790` | no visible cache effect in this sample |
| `gpt-5.4` | `$0.002635` | `$0.002635` | no visible cache effect in this sample |

This is the useful edge case. A shorter retained history did not automatically produce cache savings on OpenAI.

Longer `messages` History
---

This section is the original 2-repeat sample. It is useful as background, but not as the final word. For the current long-history summary, use [docs/stability-study-2026-04-03.md](stability-study-2026-04-03.md).

| Model | cold cost | warm cost | What to take from this |
| --- | ---: | ---: | --- |
| `command-a-03-2025` | `$0.004722` | `$0.004722` | no cost change |
| `command-r7b-12-2024` | `$0.000071` | `$0.000071` | cheap, but the API cache counters still did not explain the billing |
| `gpt-5.4-mini` | `$0.001511` | `$0.000302` | cheaper after the first turn |
| `gpt-5.4` | `$0.005038` | `$0.003022` | under-sampled here; see stability study |

Scaling
---

The cost projection used throughout this repo is:

`cold turn cost + (N - 1) * warm turn cost`

Large Repeated Prompt
---

| Model | 10 turns | 50 turns |
| --- | ---: | ---: |
| `command-a-03-2025` | `$0.875750` | `$4.378750` |
| `command-r7b-12-2024` | `$0.013130` | `$0.065650` |
| `gpt-5.4-mini` | `$0.024270` | `$0.081950` |
| `gpt-5.4` | `$0.075728` | `$0.245008` |

Longer Multi-Turn Conversation
---

This table is kept for completeness from the first-pass comparison. For the repo's current long-history projections, use the README or the stability study.

| Model | 10 turns | 50 turns |
| --- | ---: | ---: |
| `command-a-03-2025` | `$0.047220` | `$0.236100` |
| `command-r7b-12-2024` | `$0.000710` | `$0.003550` |
| `gpt-5.4-mini` | `$0.004229` | `$0.016309` |
| `gpt-5.4` | `$0.032236` | `$0.153116` |

How To Use This File
---

Use it for the broad picture across prompt shapes and for the large repeated prompt summary. Do not use it as the final source for the long-history conclusion; the stability study is stronger there.
