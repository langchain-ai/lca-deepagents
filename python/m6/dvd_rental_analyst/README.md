# DVD Rental Analyst (Managed Deep Agents)

A data analyst for a DVD rental chain. It answers business questions by writing
SQL and Python against `sakila.db` in a managed sandbox, and it can produce a
Quarterly Business Review on demand.

This is the project Module 6 deploys. MDA supplies the backend, store, and
checkpointer, and the database is built inside a per-thread sandbox rather than
read from the repo.

> **Public beta.** MDA runs on LangSmith Cloud in the **US region only**. You
> need a LangSmith Cloud account and an API key.

## What's here

| Path | What it does |
|---|---|
| `agent.py` | The agent definition: name, model, and the `email_report` tool |
| `instructions.md` | The system prompt, including the Sakila schema cheat sheet. Editable live in Context Hub |
| `sandbox/__init__.py` | `define_sandbox()` |
| `sandbox/setup.sh` | Installs pandas and matplotlib, then builds `sakila.db` |
| `skills/qbr-report/SKILL.md` | The QBR playbook. Also editable in Context Hub |
| `identity.py` | Who can call the deployment |
| `channels/slack.py` | Lets people `@mention` the agent in Slack. Authorize once during a deploy; LangSmith builds the app |
| `pyproject.toml` | Dependencies |

`sakila.db` is not in the repo. `sandbox/setup.sh` downloads the Sakila schema
and data from [jOOQ/sakila](https://github.com/jOOQ/sakila) and builds the
database in the sandbox on first use, so there is no 9 MB binary to check in.

## Setup

```bash
cd python/m6/dvd_rental_analyst
cp .env.example .env     # then fill in your keys
```

Install the SDK and the `mda` CLI. Both ship in the
[`managed-deepagents`](https://pypi.org/project/managed-deepagents/) package on
PyPI, which `pyproject.toml` pins to the version this project was built against:

```bash
uv sync
uv run mda --version
```

Run every `mda` command through `uv run` so it uses that pinned version. No
`uv`? Install it from [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/).

## Deploy it

```bash
uv run mda deploy .
```

That prints an Agent Server URL and a LangSmith dashboard URL. Open the
dashboard URL, click **Connect**, then **Open in Studio** to chat with it.

Near the end of `mda deploy`, a **Connect Slack** prompt appears with an
authorization link. Press Enter to skip it and the deploy finishes with Slack
events disabled. Approving it lets LangSmith create the Slack app, install it
in your workspace, and point its Events endpoint at the deployment. The bot
token is stored as a workspace connection, visible with `mda connections list`,
so it stays out of `.env`.

## Try these

- "What were our top 5 categories by revenue last quarter?"
- "Which store is doing better, and by how much?"
- "Generate the QBR."

Then edit `instructions.md` in Context Hub, add a persona, and ask the same
question again in the same chat. The tone changes with no redeploy.

## About the data

The public Sakila sample only contains English-language films and dates from
2005-2006. `sandbox/setup.sh` shifts all rental and payment dates forward so
"this quarter" resolves sensibly, spreads some films across French, Italian,
and Japanese, and cleans up a few `$0.00` comped payments. The numbers are
therefore not comparable to anyone else's Sakila queries; they are shaped for
a live demo.

## Tear down

```bash
uv run mda delete .
```

Removes the deployment, its tracing project, its Context Hub repo, and any
sandboxes it created. Memory and thread history are not recoverable afterward.

Note that the deployment **name stays reserved for about 7 days** after a
delete. To redeploy sooner, use a different name:

```bash
uv run mda deploy . --name dvd-rental-analyst-2
```

## Caveat

MDA is in public beta and its SDK moves quickly. This project is pinned to
`managed-deepagents==0.8.3`; `define_deep_agent`, `define_sandbox`,
`define_identity`, `auth.langsmith_api_key()`, and `channels.slack()` were
checked against that version. If you install a newer version and a call
doesn't match, the
[Managed Deep Agents docs](https://docs.langchain.com/langsmith/managed-deep-agents)
are the source of truth.
