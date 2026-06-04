[🔗 For translation, open lesson in new tab and use Chrome translate](https://langchain-ai.github.io/lca-lessons/reliable-agents/module-1/tracing-with-langsmith)

# Setting Up Tracing with LangSmith

In this tutorial, you'll learn how to set up tracing for your AI agents. We'll cover tracing with built-in integrations and how to manually instrument your own applications.

## Environment Setup

<Columns>
<Column>

First, set up your environment variables.

1. Create a `.env` file in your project root.

2. Copy and paste this cell block

3. Fill with your keys

</Column>
<Column>

```bash
# LangSmith Variables
LANGSMITH_API_KEY=your_api_key_here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=your_project_name

# 3rd Party Variables
MODEL_PROVIDER_KEY=your_api_key_here
```

</Column>
</Columns>

Then, load your environment variables into your application.

:::python
```python
  from dotenv import load_dotenv

  load_dotenv()
  ```
:::

:::js
```typescript
  import 'dotenv/config';

  const apiKey = process.env.LANGSMITH_API_KEY;
  ```
:::


---

## Scenario 1: Trace Using LangSmith Integrations

LangSmith offers integrations with a growing set of popular LLM providers, agent frameworks, and dev tools. If your agent is built using any of these frameworks this is usually the best way to start!

- [LangChain](https://docs.langchain.com/langsmith/trace-with-langchain), [LangGraph](https://docs.langchain.com/langsmith/trace-with-langgraph) and [Deep Agents](https://docs.langchain.com/langsmith/trace-deep-agents)
- [Claude Agent SDK](https://docs.langchain.com/langsmith/trace-claude-agent-sdk)
- [OpenAI Agent SDK](https://docs.langchain.com/langsmith/trace-with-openai-agents-sdk)
- [Vercel AI SDK](https://docs.langchain.com/langsmith/trace-with-vercel-ai-sdk)
- [Claude Code](https://docs.langchain.com/langsmith/trace-claude-code)

LangSmith also supports [OpenTelemetry (OTel)](https://docs.langchain.com/langsmith/trace-with-opentelemetry) as both a receiver and exporter. If your organization already has an observability stack with OTel instrumentation in place, LangSmith can plug directly into that pipeline as an additional destination.

For a full list of all integrations click [here](https://docs.langchain.com/langsmith/integrations).

---

## Scenario 2: Manually Trace your Applications

If you're building with a provider or framework that doesn't have a built-in integration, you can trace your application manually. There are three steps:

### Step 1: Wrap Your LLM Calls

<Columns>
<Column>

To capture the prompt and response from an LLM, LangSmith provides wrappers for model providers:

- OpenAI: `wrap_openai`
- Anthropic: `wrap_anthropic`
- Gemini: `wrap_gemini`

</Column>
<Column>

:::python
<CodeGroup>
```python OpenAI {2,5}
    from openai import OpenAI
    from langsmith.wrappers import wrap_openai

    client = OpenAI()
    wrapped_client = wrap_openai(client)
```
```python Anthropic {2,5}
    from anthropic import Anthropic
    from langsmith.wrappers import wrap_anthropic

    client = Anthropic()
    wrapped_client = wrap_anthropic(client)
```
```python Gemini {2,5}
    from google import genai
    from langsmith.wrappers import wrap_gemini

    client = genai.Client()
    wrapped_client = wrap_gemini(client)
```
</CodeGroup>
:::

:::js
<CodeGroup>
```typescript OpenAI {2,5}
    import OpenAI from "openai";
    import { wrapOpenAI } from "langsmith/wrappers";

    const client = new OpenAI();
    const wrappedClient = wrapOpenAI(client);
```
```typescript Anthropic {2,5}
    import Anthropic from "@anthropic-ai/sdk";
    import { wrapAnthropic } from "langsmith/wrappers/anthropic";

    const client = new Anthropic();
    const wrappedClient = wrapAnthropic(client);
```
```typescript Gemini {2,5}
    import { GoogleGenAI } from "@google/genai";
    import { wrapGemini } from "langsmith/wrappers/gemini";

    const client = new GoogleGenAI();
    const wrappedClient = wrapGemini(client);
```
</CodeGroup>
:::


</Column>
</Columns>

### Step 2: Use the `traceable` Decorator

Use the `traceable` decorator to capture the entire agent workflow, including tool calls. Wrap it around:

- Key functions in your agent (e.g., tool calls)
- Your agent pipeline or orchestration layer

<Tip>

**Specify the function type with `run_type`.** 
For example, use `@traceable(run_type="tool")` on tool functions so they appear correctly categorized in the LangSmith UI.

</Tip>

**Example: 3rd Party Weather Agent**

Toggle the tab below to see how to trace the following agent:

:::python
<CodeGroup>
```python Without Tracing
    from openai import OpenAI
    from dotenv import load_dotenv

    load_dotenv()

    client = OpenAI()

    def weather_retriever():
        """Retrieve current weather information."""
        return "It is sunny today"

    # Define the tool schema for OpenAI
    WEATHER_TOOL = {
        "type": "function",
        "function": {
            "name": "weather_retriever",
            "description": "Get the current weather conditions",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }

    def agent(question: str) -> dict:

        messages = [{"role": "user", "content": question}]

        # First API call with tool available
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=messages,
            tools=[WEATHER_TOOL],
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        # Handle tool calls if the model wants to use them
        if response_message.tool_calls:
            # Add assistant's tool call to messages
            messages.append({
                "role": "assistant",
                "content": response_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in response_message.tool_calls
                ]
            })

            # Execute the tool call(s)
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "weather_retriever":
                    result = weather_retriever()

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": "weather_retriever",
                        "content": result
                    })

            # Make second API call with tool results
            response = client.chat.completions.create(
                model="gpt-5-nano",
                messages=messages,
                tools=[WEATHER_TOOL],
                tool_choice="auto"
            )
            response_message = response.choices[0].message

        messages.append({"role": "assistant", "content": response_message.content})
        return {"messages": messages, "output": response_message.content}

    if __name__ == "__main__":
        result = agent("What is the weather today?")
        print(result["output"])
```
```python With LangSmith {2,3,8,10,29}
    from openai import OpenAI
    from langsmith.wrappers import wrap_openai
    from langsmith import traceable
    from dotenv import load_dotenv

    load_dotenv()

    client = wrap_openai(OpenAI())

    @traceable(run_type="tool")
    def weather_retriever():
        """Retrieve current weather information."""
        return "It is sunny today"

    # Define the tool schema for OpenAI
    WEATHER_TOOL = {
        "type": "function",
        "function": {
            "name": "weather_retriever",
            "description": "Get the current weather conditions",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }

    @traceable
    def agent(question: str) -> dict:

        messages = [{"role": "user", "content": question}]

        # First API call with tool available
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=messages,
            tools=[WEATHER_TOOL],
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        # Handle tool calls if the model wants to use them
        if response_message.tool_calls:
            # Add assistant's tool call to messages
            messages.append({
                "role": "assistant",
                "content": response_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in response_message.tool_calls
                ]
            })

            # Execute the tool call(s)
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "weather_retriever":
                    result = weather_retriever()

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": "weather_retriever",
                        "content": result
                    })

            # Make second API call with tool results
            response = client.chat.completions.create(
                model="gpt-5-nano",
                messages=messages,
                tools=[WEATHER_TOOL],
                tool_choice="auto"
            )
            response_message = response.choices[0].message

        messages.append({"role": "assistant", "content": response_message.content})
        return {"messages": messages, "output": response_message.content}

    if __name__ == "__main__":
        result = agent("What is the weather today?")
        print(result["output"])
```
</CodeGroup>
:::

:::js
<CodeGroup>
```typescript Without Tracing
    import "dotenv/config";
    import OpenAI from "openai";

    const client = new OpenAI();

    const weatherRetriever = async () => {
      return "It is sunny today";
    };

    // Define the tool schema for OpenAI
    const WEATHER_TOOL: OpenAI.Chat.Completions.ChatCompletionTool = {
      type: "function",
      function: {
        name: "weather_retriever",
        description: "Get the current weather conditions",
        parameters: {
          type: "object",
          properties: {},
          required: []
        }
      }
    };

    const agent = async (question: string) => {
      const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
        { role: "user", content: question }
      ];

      // First API call with tool available
      let response = await client.chat.completions.create({
        model: "gpt-5-nano",
        messages,
        tools: [WEATHER_TOOL],
        tool_choice: "auto"
      });

      let responseMessage = response.choices[0].message;

      // Handle tool calls if the model wants to use them
      if (responseMessage.tool_calls && responseMessage.tool_calls.length > 0) {
        // Add assistant's tool call to messages
        messages.push({
          role: "assistant",
          content: responseMessage.content || "",
          tool_calls: responseMessage.tool_calls
        });

        // Execute the tool call(s)
        for (const toolCall of responseMessage.tool_calls) {
          if (toolCall.function.name === "weather_retriever") {
            const result = await weatherRetriever();

            // Add tool result to messages
            messages.push({
              role: "tool",
              tool_call_id: toolCall.id,
              content: result
            });
          }
        }

        // Make second API call with tool results
        response = await client.chat.completions.create({
          model: "gpt-5-nano",
          messages,
          tools: [WEATHER_TOOL],
          tool_choice: "auto"
        });
        responseMessage = response.choices[0].message;
      }

      messages.push({ role: "assistant", content: responseMessage.content || "" });
      return { messages, output: responseMessage.content };
    };

    (async () => {
      const result = await agent("What is the weather today?");
      console.log(result.output);
    })();
```
```typescript With LangSmith {3,4,6,8,29}
    import "dotenv/config";
    import OpenAI from "openai";
    import { wrapOpenAI } from "langsmith/wrappers";
    import { traceable } from "langsmith/traceable";

    const client = wrapOpenAI(new OpenAI());

    const weatherRetriever = traceable(
      async () => {
        return "It is sunny today";
      },
      { name: "weather_retriever", run_type: "tool" }
    );

    // Define the tool schema for OpenAI
    const WEATHER_TOOL: OpenAI.Chat.Completions.ChatCompletionTool = {
      type: "function",
      function: {
        name: "weather_retriever",
        description: "Get the current weather conditions",
        parameters: {
          type: "object",
          properties: {},
          required: []
        }
      }
    };

    const agent = traceable(
      async (question: string) => {
        const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
          { role: "user", content: question }
        ];

        // First API call with tool available
        let response = await client.chat.completions.create({
          model: "gpt-5-nano",
          messages,
          tools: [WEATHER_TOOL],
          tool_choice: "auto"
        });

        let responseMessage = response.choices[0].message;

        // Handle tool calls if the model wants to use them
        if (responseMessage.tool_calls && responseMessage.tool_calls.length > 0) {
          // Add assistant's tool call to messages
          messages.push({
            role: "assistant",
            content: responseMessage.content || "",
            tool_calls: responseMessage.tool_calls
          });

          // Execute the tool call(s)
          for (const toolCall of responseMessage.tool_calls) {
            if (toolCall.function.name === "weather_retriever") {
              const result = await weatherRetriever();

              // Add tool result to messages
              messages.push({
                role: "tool",
                tool_call_id: toolCall.id,
                content: result
              });
            }
          }

          // Make second API call with tool results
          response = await client.chat.completions.create({
            model: "gpt-5-nano",
            messages,
            tools: [WEATHER_TOOL],
            tool_choice: "auto"
          });
          responseMessage = response.choices[0].message;
        }

        messages.push({ role: "assistant", content: responseMessage.content || "" });
        return { messages, output: responseMessage.content };
      },
      { name: "agent" }
    );

    (async () => {
      const result = await agent("What is the weather today?");
      console.log(result.output);
    })();
```
</CodeGroup>
:::

<RunCode>
:::python
```bash
cd lca-reliable-agents/python/module-1/lesson-2
uv run python third_party_agent.py
```
:::
:::js
```bash
cd lca-reliable-agents/ts/module-1/lesson-2
npx ts-node third_party_agent.ts
```
:::
</RunCode>

Which creates [this trace](https://smith.langchain.com/public/0d6f6624-ae55-47d5-b96c-116888a4f2db/r) in the LangSmith UI.

<Tip>

**Return the full message list, not just the final message.** This ensures all tool calls, intermediate steps, and the full conversation flow are visible in your trace output.

</Tip>

### Step 3: Group Traces into Threads

A thread is a sequence of traces representing a single conversation. Each response is represented as its own trace, but these traces are linked together by being part of the same thread.

To associate traces together, you need to pass in a special metadata key where the value is the unique identifier for that thread. The key name should be one of:
- session_id
- thread_id
- conversation_id

The value can be any string you want, but we recommend using UUIDs, such as `f47ac10b-58cc-4372-a567-0e02b2c3d479`.

**Building Stateful Conversations:**

To build a conversational agent that remembers past interactions, you need two things:

1. **Your own conversation storage** (e.g., an in-memory dictionary or database) to persist message history between turns
2. **Thread metadata** on your `@traceable` decorator so LangSmith groups all turns into a single thread for observability

**Example: Say My Name, Say My Name**

This example demonstrates how to build a conversational agent that maintains conversation history across multiple interactions using local storage and thread metadata:

:::python
<CodeGroup>
```python Without Tracing
    from openai import OpenAI
    from dotenv import load_dotenv

    load_dotenv()

    # Initialize client
    client = OpenAI()

    # Configuration
    THREAD_ID = "my-thread"

    # Conversation history store (use a database in production)
    thread_store: dict[str, list] = {}

    def get_thread_history(thread_id: str) -> list:
        return thread_store.get(thread_id, [])

    def save_thread_history(thread_id: str, messages: list):
        thread_store[thread_id] = messages

    def chat_pipeline(messages: list):
        # Automatically fetch history if it exists
        history_messages = get_thread_history(THREAD_ID)

        # Combine history with new messages
        all_messages = history_messages + messages

        # Invoke the model
        chat_completion = client.chat.completions.create(
            model="gpt-5-nano",
            messages=all_messages
        )

        # Save and return the complete conversation including input and response
        response_message = chat_completion.choices[0].message
        full_conversation = all_messages + [{"role": response_message.role, "content": response_message.content}]
        save_thread_history(THREAD_ID, full_conversation)

        return {
            "messages": full_conversation
        }
```
```python With LangSmith {3-4,9,12,23}
    from openai import OpenAI
    from dotenv import load_dotenv
    from langsmith import traceable, uuid7
    from langsmith.wrappers import wrap_openai

    load_dotenv()

    # Initialize clients
    client = wrap_openai(OpenAI())

    # Configuration
    THREAD_ID = str(uuid7())

    # Conversation history store (use a database in production)
    thread_store: dict[str, list] = {}

    def get_thread_history(thread_id: str) -> list:
        return thread_store.get(thread_id, [])

    def save_thread_history(thread_id: str, messages: list):
        thread_store[thread_id] = messages

    @traceable(name="Name Agent", metadata={"thread_id": THREAD_ID})
    def chat_pipeline(messages: list):
        # Automatically fetch history if it exists
        history_messages = get_thread_history(THREAD_ID)

        # Combine history with new messages
        all_messages = history_messages + messages

        # Invoke the model
        chat_completion = client.chat.completions.create(
            model="gpt-5-nano",
            messages=all_messages
        )

        # Save and return the complete conversation including input and response
        response_message = chat_completion.choices[0].message
        full_conversation = all_messages + [{"role": response_message.role, "content": response_message.content}]
        save_thread_history(THREAD_ID, full_conversation)

        return {
            "messages": full_conversation
        }
```
</CodeGroup>
:::

:::js
<CodeGroup>
```typescript Without Tracing
    import "dotenv/config";
    import OpenAI from "openai";

    // Initialize client
    const client = new OpenAI();

    // Configuration
    const THREAD_ID = "my-thread";

    // Conversation history store (use a database in production)
    type Message = { role: string; content: string };
    const threadStore: Record<string, Message[]> = {};

    function getThreadHistory(threadId: string): Message[] {
      return threadStore[threadId] ?? [];
    }

    function saveThreadHistory(threadId: string, messages: Message[]): void {
      threadStore[threadId] = messages;
    }

    async function chatPipeline(
      messages: OpenAI.Chat.ChatCompletionMessageParam[]
    ) {
      // Automatically fetch history if it exists
      const historyMessages = getThreadHistory(THREAD_ID);

      // Combine history with new messages
      const allMessages = [...historyMessages, ...messages];

      // Invoke the model
      const chatCompletion = await client.chat.completions.create({
        model: "gpt-5-nano",
        messages: allMessages
      });

      // Save and return the complete conversation including input and response
      const responseMessage = chatCompletion.choices[0].message;
      const fullConversation: Message[] = [
        ...allMessages,
        { role: responseMessage.role, content: responseMessage.content ?? "" },
      ];
      saveThreadHistory(THREAD_ID, fullConversation);

      return { messages: fullConversation };
    }
```
```typescript With LangSmith {3-5,8,11,25,49}
    import "dotenv/config";
    import OpenAI from "openai";
    import { wrapOpenAI } from "langsmith/wrappers";
    import { traceable } from "langsmith/traceable";
    import { uuid7 } from "langsmith";

    // Initialize clients
    const client = wrapOpenAI(new OpenAI());

    // Configuration
    const THREAD_ID = uuid7();

    // Conversation history store (use a database in production)
    type Message = { role: string; content: string };
    const threadStore: Record<string, Message[]> = {};

    function getThreadHistory(threadId: string): Message[] {
      return threadStore[threadId] ?? [];
    }

    function saveThreadHistory(threadId: string, messages: Message[]): void {
      threadStore[threadId] = messages;
    }

    const chatPipeline = traceable(
      async (messages: OpenAI.Chat.ChatCompletionMessageParam[]) => {
        // Automatically fetch history if it exists
        const historyMessages = getThreadHistory(THREAD_ID);

        // Combine history with new messages
        const allMessages = [...historyMessages, ...messages];

        // Invoke the model
        const chatCompletion = await client.chat.completions.create({
          model: "gpt-5-nano",
          messages: allMessages
        });

        // Save and return the complete conversation including input and response
        const responseMessage = chatCompletion.choices[0].message;
        const fullConversation: Message[] = [
          ...allMessages,
          { role: responseMessage.role, content: responseMessage.content ?? "" },
        ];
        saveThreadHistory(THREAD_ID, fullConversation);

        return { messages: fullConversation };
      },
      { name: "Name Agent", metadata: { thread_id: THREAD_ID } }
    );
```
</CodeGroup>
:::

<RunCode>
:::python
```bash
cd lca-reliable-agents/python/module-1/lesson-2
uv run python thread_agent.py
```
:::
:::js
```bash
cd lca-reliable-agents/ts/module-1/lesson-2
npx ts-node thread_agent.ts
```
:::
</RunCode>

Sending it a single message creates a typical [trace](https://smith.langchain.com/public/1c6ee782-148b-4a1a-aa9b-ff9208818420/r) like the one we've seen before:

:::python
```python
  # Format message
  messages = [
      {
          "content": "Hi, my name is Sally",
          "role": "user"
      }
  ]

  # Call the chat pipeline - automatically handles new conversation
  result = chat_pipeline(messages)
  ```
:::

:::js
```typescript
  // Format message
  const messages: OpenAI.Chat.ChatCompletionMessageParam[] = [
    {
      content: "Hi, my name is Sally",
      role: "user"
    }
  ];

  // Call the chat pipeline - automatically handles new conversation
  const result = await chatPipeline(messages);
  ```
:::


Send a follow up message and it remembers the previous conversation. The entire conversation is grouped into one thread and visible in the output of the [trace](https://smith.langchain.com/public/2cb4d6f2-30ac-4f3c-b592-73adcdc49bd2/r):

:::python
```python
  # Format message
  messages = [
      {
          "content": "What's my name?",
          "role": "user"
      }
  ]

  # Call the chat pipeline - automatically continues conversation
  result = chat_pipeline(messages)
  ```
:::

:::js
```typescript
  // Format message
  const messages: OpenAI.Chat.ChatCompletionMessageParam[] = [
    {
      content: "What's my name?",
      role: "user"
    }
  ];

  // Call the chat pipeline - automatically continues conversation
  const result = await chatPipeline(messages);
  ```
:::


Check out [this guide](https://docs.langchain.com/langsmith/add-metadata-tags) for more information on adding metadata to your traces.

## Recap

In this lesson, you learned how to set up tracing for AI agents:

- Integrations: LangSmith supports [integrations](https://docs.langchain.com/langsmith/integrations) with many agent frameworks
- 3rd party apps: Use wrappers (`wrap_openai`, `wrap_anthropic`) for LLM calls and `@traceable` decorator for functions
- Thread tracking: Group related traces together using `session_id`/`thread_id` metadata, and store conversation history (e.g., in-memory or in a database) for persistence across turns

## Next

You'll learn how to use traces to debug and evaluate your agents on LangSmith!

---

## References

Tracing has a great deal of expressivity beyond the basics covered here. Please reference the Introduction to Agent Observability & Evaluations course which has several lessons in Module 1 on tracing. Also see our documentation which describes the many available features.

**LangChain Academy Courses:**
- [Introduction to Agent Observability & Evaluations: Module 1:Visibility While Building with Tracing](https://academy.langchain.com/courses/intro-to-langsmith)
- [LangSmith Essentials](https://academy.langchain.com/courses/quickstart-langsmith-essentials)

**Documentation:**
- [LangSmith Tracing Documentation](https://docs.langchain.com/langsmith/tracing)
- [LangSmith Integrations](https://docs.langchain.com/langsmith/integrations)
- [Adding Metadata and Tags to Traces](https://docs.langchain.com/langsmith/add-metadata-tags)

