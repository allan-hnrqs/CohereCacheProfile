# Cohere Cache Profile

This repo tests whether Cohere exposes usable prompt caching on the public API.

## What we tested

- different prompt sizes using unique token lists
- natural-language prefixes
- multi-turn `messages` history
- repetitive prefixes from the earlier probe
- small smoke checks for `v2/embed` and `v2/rerank`

Start here:

- simple summary: [docs/chat-shapes-2026-04-03.md](docs/chat-shapes-2026-04-03.md)
- earlier repetitive-prefix notes: [docs/findings-2026-04-03.md](docs/findings-2026-04-03.md)
- raw chat shape results: [results/chat-shapes-2026-04-03.json](results/chat-shapes-2026-04-03.json)
- raw earlier chat results: [results/chat-cache-2026-04-03.json](results/chat-cache-2026-04-03.json)
- raw non-chat smoke results: [results/nonchat-cache-smoke-2026-04-03.json](results/nonchat-cache-smoke-2026-04-03.json)

## Bottom line

- `command-a-03-2025`: no cache signal in any tested chat case
  - examples: `size_large_exact_1` had `cached_tokens=0`; `natural_prefix_exact_1` had `cached_tokens=0`; `messages_history_exact_1` had `cached_tokens=0`
  - source: [docs/chat-shapes-2026-04-03.md](docs/chat-shapes-2026-04-03.md)
- `command-a-reasoning-08-2025`: same result
  - examples: `size_large_exact_1` had `cached_tokens=0`; `natural_prefix_exact_1` had `cached_tokens=0`; `messages_history_exact_1` had `cached_tokens=0`
  - source: [docs/chat-shapes-2026-04-03.md](docs/chat-shapes-2026-04-03.md)
- `command-r7b-12-2024`: `cached_tokens` is real, but not stable enough to treat as public prompt caching
  - example: `natural_prefix_exact_1` had `cached_tokens=512`, while `natural_prefix_exact_2` had `cached_tokens=3024`, and `natural_prefix_miss_1` went back to `512`
  - example: `messages_history_exact_1` had `cached_tokens=512`, while `messages_history_exact_2` had `cached_tokens=1520`, and `messages_history_miss_1` went back to `512`
  - billed input did not drop on exact repeats beyond the literal prompt-size difference
  - source: [docs/chat-shapes-2026-04-03.md](docs/chat-shapes-2026-04-03.md)
- `v2/embed` and `v2/rerank`: no cache telemetry showed up in live smoke tests
  - source: [results/nonchat-cache-smoke-2026-04-03.json](results/nonchat-cache-smoke-2026-04-03.json)

## Run

Set `COHERE_API_KEY`, then run:

```powershell
python scripts/profile_chat_shapes.py
python scripts/profile_chat_cache.py
python scripts/smoke_nonchat_cache.py
```

Each script writes JSON into `results/`.
