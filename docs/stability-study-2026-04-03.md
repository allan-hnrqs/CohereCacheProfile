**Cache Stability Study: 2026-04-03**
<table width="100%" cellpadding="0" cellspacing="0"><tr><td height="1" bgcolor="#d0d7de"></td></tr></table>

This is the strongest result in the repo. It tests whether repeated requests actually get cheaper, whether that still works after a short delay, and whether the provider reports cache use even when the request was changed on purpose. If later turns stay flat, prompt caching is not doing the job that makes repeat-heavy workloads cheaper.

Raw data: [results/cache-stability-study-2026-04-03.json](../results/cache-stability-study-2026-04-03.json)
Methodology: [docs/methodology.md](methodology.md)

All cost figures here are estimates from published pricing and API usage fields. They are not invoice exports.

**Main Result**
<table width="100%" cellpadding="0" cellspacing="0"><tr><td height="1" bgcolor="#d0d7de"></td></tr></table>

The result is simple. Command A stayed flat. OpenAI got cheaper. R7B returned cache counters, but those counters did not behave like something you could trust as a billing discount.

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

**What Was Run**
<table width="100%" cellpadding="0" cellspacing="0"><tr><td height="1" bgcolor="#d0d7de"></td></tr></table>

There were two prompt groups: `size_large`, a large repeated stable prompt, and `messages_history_long`, a longer retained multi-turn conversation.

For each model and prompt group, the benchmark ran:

1. `1` cold request
2. `6` immediate warm repeats
3. `4` intentional misses
4. `2` delayed warm repeats after `20s`

In this doc, a `reported cache hit` means `cached_tokens > 0`. A `billing-visible hit` means the request cost was meaningfully lower than the cold request. That distinction matters because `command-r7b-12-2024` could report `cached_tokens` even when billing did not change.

**Cost Snapshots**
<table width="100%" cellpadding="0" cellspacing="0"><tr><td height="1" bgcolor="#d0d7de"></td></tr></table>

Large repeated prompt.

| Model | cold cost | warm median | delayed warm median |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.087580` | `$0.087580` | `$0.087580` |
| `command-r7b-12-2024` | `$0.001314` | `$0.001314` | `$0.001314` |
| `gpt-5.4-mini` | `$0.011293` | `$0.001444` | `$0.001444` |
| `gpt-5.4` | `$0.037645` | `$0.004237` | `$0.004237` |

For this shape, Command A kept charging the same amount. OpenAI stayed much cheaper after the first request. R7B stayed cheap, but this table does not show a public cache discount you could safely budget around.

Longer multi-turn conversation.

| Model | cold cost | warm median | delayed warm median |
| --- | ---: | ---: | ---: |
| `command-a-03-2025` | `$0.004727` | `$0.004727` | `$0.004727` |
| `command-r7b-12-2024` | `$0.000071` | `$0.000071` | `$0.000071` |
| `gpt-5.4-mini` | `$0.001513` | `$0.000303` | `$0.000908` |
| `gpt-5.4` | `$0.005043` | `$0.001010` | `$0.001010` |

This is closer to a normal chat app, and the pattern still holds. Command A stayed flat. `gpt-5.4` stayed cheaper across the repeated runs. `gpt-5.4-mini` still looked good overall, but one delayed repeat missed cache.

**How To Read This**
<table width="100%" cellpadding="0" cellspacing="0"><tr><td height="1" bgcolor="#d0d7de"></td></tr></table>

If your project expects later turns to get cheaper because a stable prefix keeps repeating, this study argues against **Cohere Command A on the tested public API path**.

If you only care about low base cost, R7B may still be acceptable. Just do not treat its `cached_tokens` field as a trustworthy sign of a real billing discount.

Latency was not the clean story here. For example, `command-a-03-2025` on `size_large` ranged from `6.000s` to `10.156s` on warm immediate runs with no cost change, while `gpt-5.4` on the same shape ranged from `0.805s` to `0.983s` while cost stayed lower. Use this study for cost planning, not latency promises.

**Limits**
<table width="100%" cellpadding="0" cellspacing="0"><tr><td height="1" bgcolor="#d0d7de"></td></tr></table>

1. single-day benchmark
2. public APIs only
3. only a `20s` delay check
4. not a full TTL study
5. not a model-quality comparison
