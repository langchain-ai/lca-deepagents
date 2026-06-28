# Changes

## Thinkific Module 1, Lesson 1.2: Creating a Deep Agent

- Removed the optional instruction to use a coding agent to create `m1.2_scratch_agent.py`.
- Clarified that the lesson's purpose is to run the smallest useful deep agent before later customization lessons.
- Added the minimal script inline so learners can see the exact `create_deep_agent(model=model)` call, the shared course model import, the invocation shape, and how to read the final returned message.
- Kept the lesson instead of deleting it because it serves as the first runnable checkpoint for the course.

## Thinkific Module 1, Lesson 1.3: Models

- Renamed the section framing from "provider" to "model provider" so the terminology matches the lesson's focus.
- Simplified the provider explanation by removing early-course references to LangChain standard interfaces, embedding models, and vector stores.
- Replaced the broad "1,000+ integrations" claim with the more relevant "50+ chat model providers" framing and linked to chat model integrations.
- Clarified the lab order: run the scratch agent once with the default model, change `python/models.py`, then run the same script again to compare outputs.

## Thinkific Module 1, Lesson 1.4: The System Prompt

- Simplified the system prompt explanation by removing the learner-facing `USER`, `BASE`, `SUFFIX`, and `HarnessProfile` terminology.
- Reframed `system_prompt` as custom instructions that Deep Agents combines with built-in base instructions to form the full system prompt.
- Updated the lab wording, recap, references, and quizzes to reinforce custom instructions + built-in base instructions instead of internal prompt segment names.
- Kept the persona-swapping lab because it is still the clearest demonstration of how one instruction string changes the agent's behavior.

## Thinkific Module 1, Lesson 1.5: Tools

- Removed the Human-in-the-Loop implementation from the tools lesson so HITL can be taught later instead of competing with the core tools mental model.
- Simplified the SQL lab to a read-only `read_sql` tool that demonstrates tool definition, tool selection, Tool Node execution, and ToolMessage results without mutating the database.
- Clarified that tool schemas are provided/bound to the model call rather than appended to the system message.
- Reframed docstrings as the most important natural-language signal, while acknowledging the model also sees the tool name and argument schema.
- Updated the recap and quiz to focus on additive tools, tool calls, tool schemas, and action-tool safety rather than HITL mechanics.
- Removed the old HITL-oriented lab walkthrough videos from Lesson 1.5 so the remaining lesson content does not point learners at outdated behavior.
- Added a plain-language definition of the Tool Node as the built-in tool runner inside the agent before using it throughout the tool-call flow, and avoided early-course "graph" terminology in this lesson.

## Cross-lesson terminology cleanup

- Removed avoidable early-course "graph"/`LangGraph` mentions where learners did not need the implementation detail: the Lesson 1.4 trace-name aside, the Lesson 1.6 MCP example question, and the HITL checkpointer explanation.
- Kept `LangGraph`/`graph` terminology where it refers to actual APIs, imports, mermaid diagram syntax, `langgraph dev`, deployment configuration, or documentation links.

## Thinkific Module 1, Lesson 1.6: MCP

- Kept the docs MCP server lab as the core required path and made the GitHub OAuth material explicitly optional/advanced.
- Rewrote the quiz to match the actual Python `MultiServerMCPClient` lesson flow instead of testing `.mcp.json`/CLI OAuth behavior that the lesson does not teach.
- Added prerequisites and common failure modes for the docs MCP lab and the optional GitHub OAuth lab.
- Changed the docs lab prompt to explicitly ask the agent to use the LangChain docs MCP tool so the LangSmith trace reliably shows an MCP tool call.
- Clarified that GitHub OAuth in this lab uses the GitHub/Copilot MCP endpoint and may require account access beyond a normal GitHub account.
- Standardized the OAuth callback URL on `http://127.0.0.1:8765/` across the lesson and Step 2 script, and fixed the stale Step 3 "Step 4" output.
- Removed stale OAuth walkthrough video embeds and tightened MCP references to the concepts taught in the lesson.

## Thinkific Module 1, Lesson 1.8: Human-in-the-Loop

- Reworked the lesson as the first real HITL implementation now that Lesson 1.5 no longer teaches HITL.
- Kept the TODO video placeholder as requested.
- Reframed HITL around action-tool safety first, with resource release as a secondary benefit.
- Taught the Deep Agents HITL path with `interrupt_on`, `MemorySaver`, stable `thread_id`, and `Command(resume=...)` instead of pointing learners to lower-level LangGraph interrupt docs.
- Added a runnable safe mock email lab in `python/m1/m1.8_hitl.py` with approve, edit, and reject paths.
- Added HITL quiz questions and updated references to Deep Agents docs only.
- Fixed the stale Lesson 1.4 transition so it no longer pre-introduces HITL while pointing to the tools lesson.
- Moved HITL from Lesson 1.7 to Lesson 1.8 so messages, threads, and checkpointers are introduced first.
- Renamed the HITL lab script to `python/m1/m1.8_hitl.py` and updated lesson references, run commands, thread IDs, and image asset names.

## Thinkific Module 1, Lesson 1.7: Messages, Threads, and Checkpointers

- Inserted a new Lesson 1.7 to define runtime concepts without naming HITL before learners encounter it.
- Explained messages as the conversation history passed into and returned from `agent.invoke`, including user messages, `AIMessage`, and `ToolMessage`.
- Explained threads as ongoing conversations identified by `thread_id`, where the same `thread_id` continues state and a different `thread_id` starts a separate state.
- Explained checkpointers as the mechanism that saves thread state between calls, with `MemorySaver()` as the local development option.
- Added `python/m1/m1.7_messages_threads_checkpointers.py` to demonstrate same-thread memory versus a separate thread.

- Removed unnecessary forward references from Lesson 1.7 so it does not pre-introduce the next lesson's topic.

## Thinkific Module 2, Lesson 2.1: The Deep Agent Environment

- Reframed the lesson around the idea that deep agents run in an environment rather than introducing a generic execution environment.
- Clarified that every environment has a filesystem, shell access is optional through a backend, and the interpreter is optional but separate from the backend.
- Added a dedicated Backends section after filesystem, shell, and interpreter, defining backend as the implementation behind filesystem storage and optional shell execution.
- Removed early StateBackend, Store, CompositeBackend, and thread-vs-cross-thread persistence detail from the lesson quiz so those concepts can be taught where they are actually needed.
- Qualified sandbox safety language and simplified the filesystem section to focus on the always-present tool surface.
- Made the interpreter section more concrete while avoiding QuickJS-specific details until the interpreter lesson.

## Thinkific Module 2, Lesson 2.2: Filesystem Backends

- Simplified the opening to emphasize that the agent always sees the same filesystem tools while the backend decides where files are stored.
- Kept `StateBackend`, `FilesystemBackend / local disk`, and `CompositeBackend` in this lesson, but removed `StoreBackend`, Context Hub, namespaces, `/memories/`, and `/skills/` so durable memory storage can be introduced in the memory lesson.
- Updated CompositeBackend examples to route `/reference/` to a local `FilesystemBackend` while everything else uses `StateBackend`.
- Reworked the permissions lab to use a local `/reference/` route and deny writes to `/reference/**`, avoiding memory/skills semantics.
- Aligned the lab code snippet with `python/m2/m2.2_agent.py`, fixed the stale source filename comment, and labeled the output as model-dependent example behavior.
- Kept permissions references and removed Context Hub references from this lesson.

## Thinkific Module 3, Lesson 3.3: Memory

- Moved `StoreBackend` teaching into the memory lesson, where durable cross-thread storage and namespaces are naturally motivated.
- Updated the memory lab script to seed `/memories/AGENTS.md` into a `StoreBackend` backed by `InMemoryStore` and print the stored memory after the write.
- Added a StoreBackend quiz question and clarified that `memory=[...]` activates MemoryMiddleware injection; storage alone does not make a file memory.
- Updated memory injection terminology from `[agent_memory]` to `<agent_memory>` and clarified that memory files are loaded before a run, injected on model calls in that run, and refreshed after reload.
- Added an explicit distinction between checkpointers preserving thread history and memory storing durable file-backed facts/instructions.
- Updated the memory lab run command to be repo-relative.
- Rewrote the M3.3 lesson structure around a clearer lifecycle: memory vs checkpointers, memory as files, injection, updates, backend storage, scoping, recap, and aligned quiz questions.
- Reframed the memory storage section around the common `CompositeBackend` pattern: route `/memories/` to `StoreBackend` for durable long-term memory while leaving other working files on the default backend; updated the lab script to match and derive memory namespace from runtime context instead of hardcoding a user ID.

## Thinkific Module 4, Lesson 4.1: Delegation

- Restructured the opening around long-running agent coordination: planning keeps the main agent organized, while delegation moves specialized/context-heavy work to subagents.
- Clarified that `write_todos` state persists across turns only with the same thread and a checkpointer.
- Reframed subagents as full agents with their own instructions, tools, skills, model, and isolated context.
- Removed the stale promise to return to async subagents later and instead positioned async as a production/background workflow pattern.
- Updated recap and quiz wording so delegation is not described as having `write_todos` as one of its parts.

## Thinkific Module 4, Lesson 4.2: Building a Subagent Team

- Added an explicit architecture/data-flow overview for the newsletter subagent team.
- Reworded research folders as assigned scratch folders rather than truly private per-subagent files; clarified that permissions restrict writes to `/research/**` but do not enforce per-genre isolation.
- Replaced the informal `task("genre-researcher", …)` pseudo-call with schema-shaped `task(subagent_type=..., description=...)` wording.
- Clarified that the lab uses the default state-backed filesystem, not a sandboxed local disk, and that trusted host code mirrors `result["files"]` to disk.
- Added lab prerequisites for model credentials and `TAVILY_API_KEY`, plus a friendly runtime error when Tavily is missing.
- Fixed curly quote delimiters in quiz choices, the `write_todo` typo, and stale source filename/sanitization comments.

## Thinkific Module 5, Lesson 5.1: Putting It All Together

- Corrected the capstone overview to say the shipped module uses a mock Gmail-style MCP inbox, not real Gmail/OAuth.
- Clarified that optional chart generation uses a LangSmith Sandbox inside a chart-rendering tool while the main agent still uses its local filesystem backend.
- Tightened filesystem wording to describe the assistant's local `FilesystemBackend` during local development.
- Qualified newsletter/genre-researcher behavior as dependent on web search configuration.

## Thinkific Module 5, Lesson 5.2: Local Deployment

- Fixed the `langgraph.json` snippet to match the source dependency path (`"../.."`).
- Reframed `langgraph dev` as a local Agent Server runtime rather than vague cloud-like deployment.
- Connected server threads to the earlier thread/checkpointer pattern and clarified that Store is separate long-term key-value storage used by memory/backends.
- Added a model API key prerequisite note to the local deployment lab.

## Thinkific Module 5, Lesson 5.3: The Sales Assistant

- Fixed the `langgraph.json` snippet to match the source dependency path (`"../.."`).
- Updated mail wording and diagram alt text to reflect the shipped mock MCP mail server, not real Gmail/OAuth.
- Labeled long code snippets as important excerpts instead of claiming the file is shown in full, and included the mail-discovery degradation behavior.
- Clarified optional config: RFQ/numeric territory report run with standard setup; newsletter requires `TAVILY_API_KEY`; chart rendering uses optional LangSmith Sandbox while the main agent uses local filesystem backend.
- Added reset guidance for the mock mailbox and local database after approval flows.
- Fixed the RFQ seed to use a genuinely absent customer so the new-customer approval path is exercised, and removed stale analyst memory that marked the old seed customer as existing.
- Fixed a stale path comment in the mock inbox seed helper.

## Thinkific Module 2, Lesson 2.3: Sandboxes and LocalShell

- Reframed the lesson around shell-capable backends, with local shell and sandboxes as common families rather than the only possible `execute` implementations.
- Corrected `execute` result wording to combined command output, exit code, and execution metadata instead of separate stdout/stderr fields.
- Softened sandbox safety claims and aligned them with the M2.1 framing that sandbox safety depends on configuration, credentials, network access, and provider isolation.
- Clarified that `root_dir`/`virtual_mode` can scope filesystem tools but does not restrict `execute` for LocalShellBackend.
- Aligned sandbox setup snippets with source files, added unique sandbox names to reduce collisions, and clarified sandbox lifecycle as fresh per sandbox creation.
- Added lab prerequisite notes for model and LangSmith sandbox credentials.
- Hardened the sales chart lab by checking `upload_files()` results before invoking the agent.

## Thinkific Module 2, Lesson 2.4: Interpreters

- Aligned the opening with the revised environment/backend framing: filesystem is always present, shell comes from shell-capable backends, and the interpreter is a separate in-loop capability.
- Clarified QuickJS direct capabilities and limits, including that filesystem/network access is only possible indirectly through explicitly allowlisted PTC tools.
- Fixed SQL examples to qualify `InvoiceLine.UnitPrice * InvoiceLine.Quantity` and carry `GenreId` forward instead of interpolating a genre name into SQL.
- Added a PTC safety note emphasizing narrow allowlists and removed the premature subagent orchestration section/reference.
- Revised the interpreter comparison table to compare interpreter vs shell-capable backend/sandbox instead of implying sandbox is the only alternative.
- Added lab prerequisite notes and clarified that example outputs may vary by model.
- Updated the Lab 2 system prompt to steer generated SQL toward qualified revenue expressions while leaving the `query_chinook` tool behavior unchanged.

## Thinkific Module 3, Lesson 3.1: Summarization and Context Offloading

- Clarified that summarization appends the messages being summarized to `/conversation_history/{thread_id}.md`, rather than implying that a single file is always the full raw transcript by itself.
- Added a note connecting the demo to the Module 1 thread/checkpointer pattern: separate invokes accumulate history only when using a checkpointer and the same `thread_id`.
- Qualified `state["messages"]` language to describe the normal summarization path as preserving raw state while changing what is sent to the model.
- Fixed stale `m3.x_summarization.py` filename references in the Python script docstring.

## Thinkific Module 3, Lesson 3.2: Skills

- Aligned the demo script prompt with the lesson's fully specified BANT lead so the qualify-lead skill produces a clearer classification instead of likely follow-up questions.
- Labeled the Skills System block as simplified so learners do not expect it to exactly match the full generated system prompt.
- Reworded description guidance to say the description is the main selection text rather than the only visible text before activation.
- Updated the lab run command to be repo-relative and added a model API key prerequisite note.
- Added a general "How to use skills" section covering skill directories, `SKILL.md` metadata/body, backend availability, agent registration, runtime activation, and LangSmith debugging.
- Made the skills backend requirement explicit and updated the M3.2 lab to use virtual backend path `/skills` with `FilesystemBackend(..., virtual_mode=True)`.

