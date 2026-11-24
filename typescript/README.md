# Deep Agents

You can find the course at [Deep Agents](https://academy.langchain.com/courses/foundation-introduction-to-deepagents).

## Setup

### Prerequisites

- Node.js 24.15+
- [pnpm](https://pnpm.io/): [how to install](#installing-pnpm)
- Model authentication: use a direct provider API key (default), or a gateway-enabled LangSmith key as described below. For direct access, choose your favorite provider. The course defaults to Anthropic ([sign up for an Anthropic API key here](https://console.anthropic.com/))
- LangSmith API key: [how to get one](#getting-started-with-langsmith)
- Tavily API key (optional, for the Module 4 & 5 web-search labs): [get a free key](https://app.tavily.com)

### Installation

Clone the repository and move to the `typescript` directory:

```bash
git clone --depth 1 https://github.com/langchain-ai/lca-deepagents.git
cd lca-deepagents/typescript
```

Make a copy of `.env.example`:

```bash
cp .env.example .env
```

Choose one model authentication path. Direct provider keys remain the default: fill in LangSmith for tracing and the key for your chosen model in `.env`:

```bash
# LangSmith: tracing and observability
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_TRACING=true
LANGSMITH_AGENT_ID=lca-deepagents
LANGSMITH_AGENT_ENVIRONMENT=development
# Non-US region? Uncomment your endpoint (else your API key won't authenticate):
# LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com    # GCP EU
# LANGSMITH_ENDPOINT=https://apac.api.smith.langchain.com  # GCP APAC

# Model provider API keys: set the one you're using
ANTHROPIC_API_KEY=your-anthropic-api-key
# OPENAI_API_KEY=your-openai-api-key
# GOOGLE_API_KEY=your-google-api-key

# OpenRouter: optional, for trying free hosted open-source models (used in the Models lesson)
# Get a free key at https://openrouter.ai/keys
# OPENROUTER_API_KEY=sk-or-v1-...

# Tavily web search: for the research labs (Module 4 and the Module 5
# newsletter). Leave blank to run those labs without web search.
# Get a free key at https://app.tavily.com
TAVILY_API_KEY=
```

The shared model loader uses `dotenv.config({ override: true })`, so `.env` values take precedence over conflicting shell variables.

Set `LANGSMITH_AGENT_ID` to your LangSmith agent ID and keep `LANGSMITH_AGENT_ENVIRONMENT=development` for local lessons. Set both values together, and remove any legacy `LANGSMITH_PROJECT` setting from `.env` and your shell to avoid conflicting trace destinations.

### Optional: LangSmith LLM Gateway

If your workspace administrator has enabled [LLM Gateway](https://docs.langchain.com/langsmith/llm-gateway-direct-model-access) and configured access to your chosen provider and model, replace the model-provider key requirement for supported chat calls with:

```dotenv
LANGSMITH_GATEWAY=true
LANGSMITH_GATEWAY_API_KEY=your-gateway-enabled-langsmith-key
```

`LANGSMITH_GATEWAY_API_KEY` overrides `LANGSMITH_API_KEY` for gateway authentication; if unset or empty, the integrations fall back to `LANGSMITH_API_KEY`. Keep native model names and provider selections unchanged. `true` (also `1` or `yes`) selects the hosted gateway; `false` (also `0` or `no`) or an unset or empty flag keeps direct access. A custom gateway root URL is also accepted; integrations append their provider paths. Remove explicit provider base URLs when using this switch, since those override gateway routing.

Use the locked JavaScript integrations, not the Python version numbers: `@langchain/anthropic` 1.6.6 and `@langchain/openai` 1.8.5 support this switch.

Tracing is separate: use `LANGSMITH_TRACING=true` and a valid `LANGSMITH_API_KEY` to trace, or `LANGSMITH_TRACING=false` to turn tracing off. A dedicated gateway key does not enable tracing, and `LANGSMITH_ENDPOINT` configures LangSmith APIs, not the gateway URL.

This applies to the LangChain chat models used by the lessons, not OpenRouter, Ollama, raw provider SDKs, embeddings, or external tools. Keep Tavily and GitHub OAuth credentials for the labs that use them. The Module 5 remote agents need the same model settings in their own runtime. The Module 6 managed deployment has separate server-side model configuration; do not assume local gateway variables configure it.

You may export these settings in your shell instead of writing `.env`. Remove conflicting values from `.env` first: lesson loaders that use `override=True` / `override: true` prefer the file. Never commit credentials.

### Install dependencies

```bash
pnpm install
```

### Setup Verification

After completing the steps above, run the following to verify your environment:

```bash
cd typescript
pnpm tsx env_utils.ts
```

You should see masked values for each key in your `.env` file. Optional keys may show `<not set>`. The checker validates the default Anthropic chat model; if you change providers, append `openai`, `google_genai`, `openrouter`, or `ollama` to the command. Address the reported issues for your selected mode, not unused provider keys.

---

## Setup Details

### Setup Verification Issues

<details>
<summary>Cannot find module 'deepagents' (or similar)</summary>

You're likely running a lesson script without having installed dependencies first.

**Solution:** Run `pnpm install` from the `typescript` directory.

</details>

<details>
<summary>Missing or invalid API key errors</summary>

The key exists in `.env.example` but has no value in your `.env` file.

**Solution:** Open `typescript/.env` and fill in the missing value.

</details>

<details>
<summary>LangSmith tracing errors</summary>

If you see tracing errors at runtime, check that both `LANGSMITH_TRACING=true` and a valid `LANGSMITH_API_KEY` are set in your `.env` file. If you don't have a LangSmith account yet, set `LANGSMITH_TRACING=false` to disable tracing until you do.

</details>

<details>
<summary>Wrong Node.js version</summary>

The course requires Node.js 24.15+.

**Solution:** Install Node.js 24.15+ from [nodejs.org](https://nodejs.org/), or use a version manager like [nvm](https://github.com/nvm-sh/nvm) / [fnm](https://github.com/Schniz/fnm).

</details>

### Getting Started with LangSmith

- Create a [LangSmith](https://smith.langchain.com/) account
- Go to **Settings → API Keys** and create a new API key
- Create or select an agent, copy its ID into `LANGSMITH_AGENT_ID`, and use its `development` environment for the course

### Installing pnpm

See the [pnpm installation docs](https://pnpm.io/installation) for full instructions. Common options:

```bash
# Via Corepack (ships with Node.js 16.13+)
corepack enable
corepack prepare pnpm@latest --activate

# macOS with Homebrew
brew install pnpm

# Standalone script (macOS / Linux)
curl -fsSL https://get.pnpm.io/install.sh | sh -
```
</content>
