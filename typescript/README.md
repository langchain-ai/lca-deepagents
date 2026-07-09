# Deep Agents

You can find the course at [Deep Agents](https://academy.langchain.com/courses/foundation-introduction-to-deepagents).

## Setup

### Prerequisites

- Node.js 20+
- [pnpm](https://pnpm.io/): [how to install](#installing-pnpm)
- LLM Model API key: choose your favorite provider. The course defaults to Anthropic ([sign up for an Anthropic API key here](https://console.anthropic.com/))
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

Insert API keys directly into `.env` — LangSmith (required) and your model provider (required):

```bash
# LangSmith — tracing and observability
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=lca-deepagents
# Non-US region? Uncomment your endpoint (else your API key won't authenticate):
# LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com    # GCP EU
# LANGSMITH_ENDPOINT=https://apac.api.smith.langchain.com  # GCP APAC

# Model provider API keys — set the one you're using
ANTHROPIC_API_KEY=your-anthropic-api-key
# OPENAI_API_KEY=your-openai-api-key
# GOOGLE_API_KEY=your-google-api-key

# OpenRouter: optional, for trying free hosted open-source models (used in the Models lesson)
# Get a free key at https://openrouter.ai/keys
# OPENROUTER_API_KEY=sk-or-v1-...

# Tavily web search — for the research labs (Module 4 and the Module 5
# newsletter). Leave blank to run those labs without web search.
# Get a free key at https://app.tavily.com
TAVILY_API_KEY=
```

This course uses `dotenv/config` — `.env` values are loaded automatically when a lesson script starts.

Install dependencies:

```bash
pnpm install
```

### Setup Verification

After completing the steps above, run the following to verify your environment:

```bash
cd typescript
pnpm tsx env_utils.ts
```

You should see masked values for each key in your `.env` file. If anything shows `<not set>`, see [Setup Verification Issues](#setup-verification-issues).

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

The course requires Node.js 20+.

**Solution:** Install Node.js 20+ from [nodejs.org](https://nodejs.org/), or use a version manager like [nvm](https://github.com/nvm-sh/nvm) / [fnm](https://github.com/Schniz/fnm).

</details>

### Getting Started with LangSmith

- Create a [LangSmith](https://smith.langchain.com/) account
- Go to **Settings → API Keys** and create a new API key

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
