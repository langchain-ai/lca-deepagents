# Deep Agents

You can find the course at [Deep Agents](https://academy.langchain.com/courses/foundation-introduction-to-deepagents).

## Setup

> **Already set up?** As of August 5, 2026 this course runs on `deepagents==0.7.0`. If you cloned before this date, pull the latest changes and resync your environment:
> ```bash
> git pull
> uv sync
> ```

### Prerequisites

- Python 3.11 to 3.14
- [uv](https://docs.astral.sh/uv/): [how to install](#installing-uv)
- Model authentication: use a direct provider API key (default), or a gateway-enabled LangSmith key as described below. For direct access, choose your favorite provider. The course defaults to Anthropic ([sign up for an Anthropic API key here](https://console.anthropic.com/))
- LangSmith API key: [how to get one](#getting-started-with-langsmith)
- Tavily API key (optional, for the Module 4 & 5 web-search labs): [get a free key](https://app.tavily.com)
- Windows: supported through [WSL (Windows Subsystem for Linux)](https://learn.microsoft.com/en-us/windows/wsl/install)

### Installation

Clone the repository and move to the `python` directory:

```bash
git clone --depth 1 https://github.com/langchain-ai/lca-deepagents.git
cd lca-deepagents/python
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

This course uses `load_dotenv(override=True)`, so `.env` values always win over OS environment variables.

Set `LANGSMITH_AGENT_ID` to your LangSmith agent ID and keep `LANGSMITH_AGENT_ENVIRONMENT=development` for local lessons. Set both values together, and remove any legacy `LANGSMITH_PROJECT` setting from `.env` and your shell to avoid conflicting trace destinations.

### Optional: LangSmith LLM Gateway

If your workspace administrator has enabled [LLM Gateway](https://docs.langchain.com/langsmith/llm-gateway-direct-model-access) and configured access to your chosen provider and model, replace the model-provider key requirement for supported chat calls with:

```dotenv
LANGSMITH_GATEWAY=true
LANGSMITH_GATEWAY_API_KEY=your-gateway-enabled-langsmith-key
```

`LANGSMITH_GATEWAY_API_KEY` overrides `LANGSMITH_API_KEY` for gateway authentication; if unset or empty, the integrations fall back to `LANGSMITH_API_KEY`. Keep native model names and provider selections unchanged. `true` (also `1` or `yes`) selects the hosted gateway; `false` (also `0` or `no`) or an unset or empty flag keeps direct access. A custom gateway root URL is also accepted; integrations append their provider paths. Remove explicit provider base URLs when using this switch, since those override gateway routing.

The locked Python integrations support this switch (`langchain-anthropic>=1.5.1` and `langchain-openai>=1.4.1`, with `langchain-core>=1.5.3` for LangSmith key fallback). For the optional Google integration, use `uv sync --extra google` (`langchain-google-genai>=4.3.2`).

Tracing is separate: use `LANGSMITH_TRACING=true` and a valid `LANGSMITH_API_KEY` to trace, or `LANGSMITH_TRACING=false` to turn tracing off. A dedicated gateway key does not enable tracing, and `LANGSMITH_ENDPOINT` configures LangSmith APIs, not the gateway URL.

This applies to the LangChain chat models used by the lessons, not OpenRouter, Ollama, raw provider SDKs, embeddings, or external tools. Keep Tavily and GitHub OAuth credentials for the labs that use them. The Module 5 remote agents need the same model settings in their own runtime. The Module 6 managed deployment has separate server-side model configuration; do not assume local gateway variables configure it.

You may export these settings in your shell instead of writing `.env`. Remove conflicting values from `.env` first: lesson loaders that use `override=True` / `override: true` prefer the file. Never commit credentials.

### Install dependencies

```bash
uv sync
```

### Setup Verification

After completing the steps above, run the following to verify your environment:

```bash
cd python
uv run python env_utils.py
```

You should see masked values for each key in your `.env` file. Optional keys may show `<not set>`. The checker validates the default Anthropic chat model; if you change providers, append `openai`, `google_genai`, `openrouter`, or `ollama` to the command. Address the reported issues for your selected mode, not unused provider keys.

---

## Setup Details

### Setup Verification Issues

<details>
<summary>ImportError when running env_utils.py</summary>

If you see `ModuleNotFoundError: No module named 'dotenv'`, you're likely running Python outside the virtual environment.

**Solution:** Use `uv run python env_utils.py` (recommended), or activate the virtual environment first:
- macOS/Linux: `source .venv/bin/activate`
- Windows: `.venv\Scripts\activate`

</details>

<details>
<summary>A key shows &lt;not set&gt;</summary>

The key exists in `.env.example` but has no value in your `.env` file.

**Solution:** Open `python/.env` and fill in the missing value.

</details>

<details>
<summary>LangSmith tracing errors</summary>

If you see tracing errors at runtime, check that both `LANGSMITH_TRACING=true` and a valid `LANGSMITH_API_KEY` are set in your `.env` file. If you don't have a LangSmith account yet, set `LANGSMITH_TRACING=false` to disable tracing until you do.

</details>

<details>
<summary>Wrong Python version</summary>

The course requires Python 3.11 to 3.14.

**Solution:** If using `uv`, run `uv sync`; it will install the correct Python version automatically. If using pip, install Python 3.11 to 3.14 from [python.org](https://www.python.org/downloads/).

</details>

### Getting Started with LangSmith

- Create a [LangSmith](https://smith.langchain.com/) account
- Go to **Settings → API Keys** and create a new API key
- Create or select an agent, copy its ID into `LANGSMITH_AGENT_ID`, and use its `development` environment for the course

### Installing uv

See the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) for full instructions. Common options:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# macOS with Homebrew
brew install uv

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
