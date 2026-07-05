# Deep Agents

You can find the course at [Deep Agents](<fill in Thinkific URL>).

## Setup

### Prerequisites

- Python 3.11–3.14
- [uv](https://docs.astral.sh/uv/) — [how to install](#installing-uv)
- LLM Model API key — choose your favorite provider. The course defaults to Anthropic ([sign up for an Anthropic API key here](https://console.anthropic.com/))
- LangSmith API key — [how to get one](#getting-started-with-langsmith)
- Tavily API key (optional, for the Module 4 & 5 web-search labs) — [get a free key](https://app.tavily.com)

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

This course uses `load_dotenv(override=True)` — `.env` values always win over OS environment variables.

Install dependencies:

```bash
uv sync
```

### Setup Verification

After completing the steps above, run the following to verify your environment:

```bash
cd python
uv run python env_utils.py
```

You should see masked values for each key in your `.env` file. If anything shows `<not set>`, see [Setup Verification Issues](#setup-verification-issues).

### Setup Your Coding Agent

Using a coding agent to build your agents is encouraged throughout this course. Three additions make it significantly more effective.

#### LangChain Skills

Install the LangChain skills to give your coding agent deep knowledge of Deep Agents, LangGraph, and the LangChain ecosystem:

```bash
npx skills add langchain-ai/langchain-skills --skill '*' --yes --global
```

This installs skills including `deep-agents-core`, `deep-agents-memory`, `deep-agents-orchestration`, and more.

#### LangChain Docs MCP Server

Gives your coding agent direct access to LangChain, LangGraph, and LangSmith documentation — including search and a loaded skill that covers core concepts. Add it once and it is available in all your projects.

[Full setup instructions](https://docs.langchain.com/use-these-docs#use-our-mcp-server)

#### LangSmith Skills

On-demand capabilities for querying traces, generating datasets, and defining evaluators — directly from within your agent session.

[Full setup instructions](https://docs.langchain.com/langsmith/skills)

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

The course requires Python 3.11–3.14.

**Solution:** If using `uv`, run `uv sync` — it will install the correct Python version automatically. If using pip, install Python 3.11–3.14 from [python.org](https://www.python.org/downloads/).

</details>

### Getting Started with LangSmith

- Create a [LangSmith](https://smith.langchain.com/) account
- Create a LangSmith API key

<img width="600" alt="LangSmith API key - step 1" src="https://github.com/user-attachments/assets/e39b8364-c3e3-4c75-a287-d9d4685caad5" />
<img width="600" alt="LangSmith API key - step 2" src="https://github.com/user-attachments/assets/2e916b2d-e3b0-4c59-a178-c5818604b8fe" />

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
