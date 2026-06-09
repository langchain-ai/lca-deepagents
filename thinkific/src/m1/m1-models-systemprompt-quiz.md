[🔗 For translation, open lesson in new tab and use Chrome translate](https://langchain-ai.github.io/lca-deepagents/m1/m1-models-systemprompt-quiz.html)

<style>@import url('../shared/sd-components.css');</style>
<script src="../shared/sd-components.js"></script>

# Quiz: Models & the System Prompt

<MCQ
    question="What does the string 'anthropic:claude-haiku-4-5' in init_chat_model('anthropic:claude-haiku-4-5') specify?"
    choices='["Just the model; the provider is inferred from the API key", "Just the provider; the model defaults to the latest version", "Both the provider and the model, letting one function target any LangChain-supported backend", "The API endpoint URL to call"]'
    correctIndex={2}
    explanation="The provider:model format tells init_chat_model which LangChain integration to use and which model to request. Changing the prefix (e.g. openai: vs anthropic:) switches the entire backend; changing the suffix swaps the model within that provider."
/>

<MCQ
    question="When you swap the model in models.py, what is the only thing that changes in the agent?"
    choices='["The file tools available to the agent", "The BASE instructions injected by the SDK", "The model", "The assembled system prompt"]'
    correctIndex={2}
    explanation="The model is the only thing that changes. The SDK wraps the same BASE instructions and file tools around every model; one-line swap in models.py, everything else stays put."
/>

<hr style="border:none;border-top:1px solid #e5e7eb;margin:2rem 0;" />

*Bonus: harness profiles are covered in a later lesson:*

<MCQ
    question="Which part of a Deep Agent's assembled system prompt is model-specific?"
    choices='["The BASE prompt; each provider ships its own version", "The SUFFIX; it comes from a harness profile registered for that specific model", "The filesystem instructions; tailored per provider", "None; the entire system prompt is identical across all models"]'
    correctIndex={1}
    explanation="The SUFFIX is the only model-specific segment, coming from a harness profile keyed to the model. claude-haiku-4-5 and claude-sonnet-4-6 each ship one; gpt-4.1-mini has no registered profile so its SUFFIX is empty. The BASE prompt and filesystem instructions are identical regardless of model."
/>

<MCQ
    question="Where does your system_prompt sit in the assembled prompt the model receives?"
    choices='["After the BASE instructions, before the SUFFIX", "At the very front, before the BASE instructions", "At the end, after the SUFFIX", "It replaces the BASE instructions entirely"]'
    correctIndex={1}
    explanation="The SDK slots the USER segment, your system_prompt, at the very front of the assembled prompt, ahead of the BASE behavior instructions and any SUFFIX. It is the first thing the model reads, which is why it reliably shapes tone and persona."
/>

<MCQ
    question="You define SYSTEM_PROMPT = 'You are a pirate captain.' in scratch_agent.py but the agent replies with no pirate tone. What is most likely wrong?"
    choices='["The BASE prompt overrides user-defined personas", "SYSTEM_PROMPT was defined but not passed to create_deep_agent", "The model requires a special setting to apply personas", "The SUFFIX overrides the USER segment"]'
    correctIndex={1}
    explanation="Defining the string is not enough; it must be passed explicitly: create_deep_agent(model=model, system_prompt=SYSTEM_PROMPT). Without the argument, the agent never receives the USER segment and falls back to the BASE behavior only."
/>
