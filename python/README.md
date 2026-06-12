You can find the course at [Deep Agents](<fill in Thinkific URL>).

# lca-deepagents

LangChain Academy Course on Deep Agents

## Setup

### Prerequisites

- Python 3.11–3.13
- [uv](https://docs.astral.sh/uv/) — [how to install](#installing-uv)
- Anthropic API key — [get one](https://console.anthropic.com/)
- LangSmith API key — [how to get one](#getting-started-with-langsmith)

### Installation

Clone the repository and move to the `python` directory:

```bash
git clone https://github.com/langchain-ai/lca-deepagents.git
cd lca-deepagents/python
```

Copy `.env.example` and fill in your API keys:

```bash
cp .env.example .env
```

Install dependencies:

```bash
uv sync
```

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
