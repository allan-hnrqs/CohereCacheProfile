#### Cohere Cache Profile
<sub>────────────────────────────</sub>

This repo benchmarks whether repeated prompt reuse gets cheaper on the public API. In these tests, OpenAI did; Cohere Command A did not. The practical consequence is that Cohere Command A looks like a weak fit for repeat-heavy workloads whose economics depend on prompt caching, such as coding agents, long-history chat, and some RAG flows. This is not a general model comparison; it does not judge embeddings, rerank quality, retrieval quality, or private deployment options.

#### Main Result
<sub>────────────────────</sub>

1. `command-a-03-2025` stayed flat on the tested public API path. Repeating the same large prefix did not make requests cheaper, and the same held for the longer retained-history chat shape.
2. `command-r7b-12-2024` stayed very cheap, but the low price looked like base model pricing rather than a reliable public cache discount. The API returned cache counters, but those counters did not line up with billing in a way that looked safe to build around.
3. OpenAI behaved differently. Repeated requests usually did get cheaper, often by a lot. Latency moved around enough that cost was the more useful signal.
4. If your cost model depends on prompt caching working predictably, this repo is evidence against **Cohere Command A on the public API**.

#### Cost Snapshots
<sub>────────────────────</sub>

Two prompt shapes mattered most: a large repeated prompt, where the same large prefix is sent every turn, and a longer multi-turn conversation, where retained `messages` history is sent again on later turns. The `50 turns` column below is a projection using `cold turn cost + (49 * repeated turn cost)`. All dollar figures are estimates from published pricing and API usage fields, not invoice exports.

Large repeated prompt. Source: [docs/openai-vs-cohere-latency-cost-2026-04-03.md](docs/openai-vs-cohere-latency-cost-2026-04-03.md)

<table align="center" width="92%">
  <thead>
    <tr>
      <th align="left">Model</th>
      <th align="right">cold turn</th>
      <th align="right">repeated turn</th>
      <th align="right">50 turns</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>command-a-03-2025</code></td>
      <td align="right"><code>$0.087575</code></td>
      <td align="right"><code>$0.087575</code></td>
      <td align="right"><code>$4.378750</code></td>
    </tr>
    <tr>
      <td><code>command-r7b-12-2024</code></td>
      <td align="right"><code>$0.001313</code></td>
      <td align="right"><code>$0.001313</code></td>
      <td align="right"><code>$0.065650</code></td>
    </tr>
    <tr>
      <td><code>gpt-5.4-mini</code></td>
      <td align="right"><code>$0.011292</code></td>
      <td align="right"><code>$0.001442</code></td>
      <td align="right"><code>$0.081950</code></td>
    </tr>
    <tr>
      <td><code>gpt-5.4</code></td>
      <td align="right"><code>$0.037640</code></td>
      <td align="right"><code>$0.004232</code></td>
      <td align="right"><code>$0.245008</code></td>
    </tr>
  </tbody>
</table>

This is the clearest economic signal in the repo. Command A stays flat. OpenAI drops sharply after the cold turn. R7B stays cheap, but not because this repo found a public cache feature you could safely budget around.

Longer multi-turn conversation. Source: [docs/stability-study-2026-04-03.md](docs/stability-study-2026-04-03.md)

<table align="center" width="92%">
  <thead>
    <tr>
      <th align="left">Model</th>
      <th align="right">cold turn</th>
      <th align="right">repeated turn</th>
      <th align="right">50 turns</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>command-a-03-2025</code></td>
      <td align="right"><code>$0.004727</code></td>
      <td align="right"><code>$0.004727</code></td>
      <td align="right"><code>$0.236350</code></td>
    </tr>
    <tr>
      <td><code>command-r7b-12-2024</code></td>
      <td align="right"><code>$0.000071</code></td>
      <td align="right"><code>$0.000071</code></td>
      <td align="right"><code>$0.003550</code></td>
    </tr>
    <tr>
      <td><code>gpt-5.4-mini</code></td>
      <td align="right"><code>$0.001513</code></td>
      <td align="right"><code>$0.000303</code></td>
      <td align="right"><code>$0.016360</code></td>
    </tr>
    <tr>
      <td><code>gpt-5.4</code></td>
      <td align="right"><code>$0.005043</code></td>
      <td align="right"><code>$0.001010</code></td>
      <td align="right"><code>$0.054533</code></td>
    </tr>
  </tbody>
</table>

This is closer to a normal chat app, and the conclusion still holds. Command A stayed flat. OpenAI got materially cheaper once the repeated history became reusable.

#### How To Use This Repo
<sub>────────────────────</sub>

1. Use this repo as evidence against Cohere Command A public API when your architecture expects later turns to get cheaper because the prefix repeats, your chatbot carries a lot of retained history, or your agent resends a large stable prompt every turn.
2. Do not use it to conclude that Cohere is bad in general. The repo does not test private deployments, Model Vault, embeddings, rerank, or overall model quality. It also does not prove that Cohere has no internal caching. It only shows that on the tested public API path, Command A did not show useful prompt-cache savings.
3. `command-r7b-12-2024` may still be worth testing if you mostly care about very low base cost and do not need predictable cache savings or trustworthy cache counters from the API. That is a cost recommendation only.

#### Read This Next
<sub>────────────────────</sub>

1. [docs/stability-study-2026-04-03.md](docs/stability-study-2026-04-03.md): strongest supporting evidence.
2. [docs/openai-vs-cohere-latency-cost-2026-04-03.md](docs/openai-vs-cohere-latency-cost-2026-04-03.md): broader sweep across more prompt shapes.
3. [docs/chat-shapes-2026-04-03.md](docs/chat-shapes-2026-04-03.md): best place to inspect Cohere's returned cache counters directly.
4. [docs/methodology.md](docs/methodology.md): benchmark design and limits.

Background note: [docs/findings-2026-04-03.md](docs/findings-2026-04-03.md) is the earliest repetitive-prefix probe and should not be read as the main decision document.

Raw result files: [cache-stability-study-2026-04-03.json](results/cache-stability-study-2026-04-03.json), [openai-vs-cohere-latency-cost-2026-04-03.json](results/openai-vs-cohere-latency-cost-2026-04-03.json), [chat-shapes-2026-04-03.json](results/chat-shapes-2026-04-03.json).

#### Running The Scripts
<sub>────────────────────</sub>

Set `COHERE_API_KEY` and `OPENAI_API_KEY`, then run:

```powershell
python scripts/profile_chat_shapes.py
python scripts/profile_chat_cache.py
python scripts/smoke_nonchat_cache.py
python scripts/compare_openai_cohere_latency_cost.py
python scripts/cache_stability_study.py
```

Each script writes JSON into `results/`.
