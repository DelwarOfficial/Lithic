# AI Model Comparison & Cost Analysis

Lithic is provider-agnostic — it works with any LLM backend. This document compares popular models across **cost, context, capability, and Lithic's token reduction** to help you choose the best option for your workflow.

> **Pricing verified June 2026.** All rates in USD per 1M tokens. Providers change prices without notice — verify before committing.

---

## 📊 Master Pricing Table

| Model | Provider | Input $/1M | Output $/1M | Context | Cached Input |
|-------|----------|-----------|------------|---------|-------------|
| **DeepSeek V4 Flash** | DeepSeek | $0.14 | $0.28 | 1M | $0.003 |
| **DeepSeek V4 Pro** | DeepSeek | $0.44 | $0.87 | 1M | $0.004 |
| **Gemini 2.0 Flash-Lite** | Google | $0.10 | $0.40 | 1M | — |
| **Gemini 2.5 Flash** | Google | $0.30 | $2.50 | 1M | 50% batch |
| **Gemini 2.5 Pro** | Google | $1.25–2.50 | $10.00–15.00 | 1M | 50% batch |
| **GPT-4.1 Nano** | OpenAI | $0.10 | $0.40 | 1M | — |
| **GPT-4o Mini** | OpenAI | $0.15 | $0.60 | 128K | 50% batch |
| **GPT-4.1** | OpenAI | $2.00 | $8.00 | 1M | 50% batch |
| **GPT-5.4** | OpenAI | $2.50 | $10.00 | 1M | 50% batch |
| **Claude Haiku 4.5** | Anthropic | $1.00 | $5.00 | 200K | ~90% off |
| **Claude Sonnet 4.6** | Anthropic | $3.00 | $15.00 | 200K | ~90% off |
| **Claude Opus 4.8** | Anthropic | $5.00 | $25.00 | 1M | ~90% off |
| **Kimi K2.6** | Moonshot AI | $0.95 | $4.00 | 256K | $0.16 |
| **Kimi K2.5** | Moonshot AI | $0.60 | $3.00 | 256K | $0.10 |
| **GLM-5.2** | Zhipu AI | $1.40 | $4.40 | 200K | $0.26 |
| **GLM-5** | Zhipu AI | $1.00 | $3.20 | 200K | $0.20 |
| **GLM-4.7** | Zhipu AI | $0.60 | $2.20 | 205K | — |
| **GLM-4.7-Flash** | Zhipu AI | **Free** | **Free** | 203K | — |
| **Mistral Large 3** | Mistral | $0.50 | $1.50 | 128K | — |
| **Llama 4 Maverick** | Meta (via Groq) | $0.20 | $0.60 | 1M | — |

---

## 🪙 Budget Tier (Under $0.50/M input)

| Model | Cost/1M in/out | Best for |
|-------|---------------|----------|
| **DeepSeek V4 Flash** | $0.14 / $0.28 | General coding, high-volume |
| **Gemini 2.0 Flash-Lite** | $0.10 / $0.40 | Classification, simple tasks |
| **GPT-4.1 Nano** | $0.10 / $0.40 | Fast completions |
| **GPT-4o Mini** | $0.15 / $0.60 | General purpose |
| **Llama 4 Maverick** (Groq) | $0.20 / $0.60 | High-throughput |
| **GLM-4.7-Flash** | **Free / Free** | Zero-cost simple tasks |
| **Mistral Small 4** | $0.10 / $0.30 | EU data residency |

---

## ⚡ Mid-Range ($0.50–$3.00/M input)

| Model | Cost/1M in/out | Best for |
|-------|---------------|----------|
| **DeepSeek V4 Pro** | $0.44 / $0.87 | Frontier-adjacent quality |
| **Kimi K2.5** | $0.60 / $3.00 | Long-context, multilingual |
| **GLM-4.7** | $0.60 / $2.20 | Budget coding agent |
| **Kimi K2.6** | $0.95 / $4.00 | Agentic workflows |
| **Claude Haiku 4.5** | $1.00 / $5.00 | Fast, reliable |
| **Gemini 2.5 Flash** | $0.30 / $2.50 | Production workloads |
| **Gemini 2.5 Pro** | $1.25–2.50 / $10–15 | Long-doc reasoning |

---

## 🚀 Flagship ($3.00+/M input)

| Model | Cost/1M in/out | Best for |
|-------|---------------|----------|
| **Claude Sonnet 4.6** | $3.00 / $15.00 | Balanced coding + reasoning |
| **Claude Opus 4.8** | $5.00 / $25.00 | Complex agentic tasks |
| **GPT-4.1** | $2.00 / $8.00 | General multimodal |
| **GPT-5.4** | $2.50 / $10.00 | Broad reasoning |
| **GLM-5.2** | $1.40 / $4.40 | Chinese-market frontier |

---

## 💰 Cost Impact: Lithic's Token Reduction

Lithic's compression and response shaping reduce token consumption significantly. Here's the **real cost per task** with and without Lithic:

### Example: Review a 100K-token diff

| Step | Without Lithic | With Lithic |
|------|---------------|-------------|
| Raw diff sent to LLM | 100K input tokens | — |
| After `compress_tool_output` | — | ~8K input tokens (92% reduction) |
| LLM reasoning output | ~2K output tokens | ~2K output tokens |
| After `_concise` shaping | — | ~1.5K output tokens (25% reduction) |

### Monthly cost comparison (10M input + 2M output tokens/month)

| Model | Raw cost/mo | With Lithic (est. 75% fewer input tokens) | Savings |
|-------|------------|------------------------------------------|---------|
| **DeepSeek V4 Flash** | $1.96 | **$0.73** | 63% |
| **Claude Sonnet 4.6** | $60.00 | **$18.00** | 70% |
| **GPT-4.1** | $36.00 | **$11.50** | 68% |
| **Claude Opus 4.8** | $100.00 | **$29.50** | 71% |
| **Kimi K2.6** | $17.50 | **$5.63** | 68% |
| **GLM-5** | $16.40 | **$5.30** | 68% |

*Assumes `compress_tool_output` on diffs/logs (80–92% reduction) + `_concise` shaping (15–25% reduction). Actual savings vary by workload.*

---

## 🔐 Provider Comparison Matrix

| Feature | OpenAI | Anthropic | Google | DeepSeek | Moonshot (Kimi) | Zhipu (GLM) |
|---------|--------|-----------|--------|----------|-----------------|-------------|
| **Open weights** | ❌ | ❌ | ❌ | ✅ | ✅ (K2) | ✅ |
| **Self-hostable** | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Vision** | ✅ | ✅ | ✅ | ❌ (V4) | ✅ | ✅ |
| **Function calling** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **JSON mode** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Prompt caching** | ✅ | ✅ (90%) | ✅ | ✅ (90%) | ✅ (83%) | ✅ |
| **Batch discount** | 50% | 50% | 50% | — | — | — |
| **Max context** | 1M | 1M | 1M | 1M | 256K | 205K |
| **EU data residency** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Free tier** | ❌ | ❌ | ✅ | ✅ (5M new users) | ❌ | ✅ (Flash) |

---

## 🎯 Which Model for Which Lithic Workflow?

| Workflow | Recommended model | Why |
|----------|------------------|-----|
| **`lithic index .`** (graph build) | DeepSeek V4 Flash / GLM-4.7-Flash | High-volume file processing, cost-sensitive |
| **`lithic ask "..."`** (codebase Q&A) | Claude Sonnet 4.6 / GPT-4.1 | Best code comprehension |
| **`lithic review`** (diff review) | DeepSeek V4 Flash / GPT-4o Mini | Fast, cheap for structured input |
| **`lithic commit`** (commit gen) | Any budget model | Simple formatting task |
| **`lithic explain "..."`** | Claude Haiku 4.5 / Gemini 2.5 Flash | Fast + cheap for focused queries |
| **Agentic loops** | Kimi K2.6 / Claude Sonnet 4.6 | Strong tool-use + long context |

---

## 📈 Price Trend (2024–2026)

The cost per million tokens has dropped **60–80% since early 2025**:

- **DeepSeek**: cut prices ~90% below OpenAI equivalents
- **Anthropic**: Opus price dropped from $15/M to $5/M (67%)
- **OpenAI**: GPT-4.1 Nano at $0.10/M — cheapest model ever
- **Google**: Flash-Lite at $0.10/M, matching open-source hosts
- **Zhipu**: Two free models (GLM-4.7-Flash, GLM-4.5-Flash)

---

## 🔗 Resources

- [OpenAI API Pricing](https://openai.com/api/pricing/)
- [Anthropic API Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Google Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [DeepSeek API Pricing](https://api-docs.deepseek.com/quick_start/pricing)
- [Moonshot Kimi Pricing](https://platform.kimi.ai/docs/pricing)
- [Zhipu GLM Pricing](https://z.ai/pricing)
- [AI Pricing Guru](https://www.aipricing.guru/pricing/) — independent tracker
