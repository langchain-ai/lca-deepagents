/**
 * Model Initialization File
 *
 * Configures the LLM model used throughout the course.
 *
 * Default: Anthropic claude-haiku-4-5 (fast, cheap, great for learning).
 *
 * ═══════════════════════════════════════════════════════════════════════════
 *   ⚠  IMPORTANT: install the matching package BEFORE swapping providers
 * ═══════════════════════════════════════════════════════════════════════════
 *
 *   Provider              Package                      Installed?
 *   --------------------  ---------------------------  ---------------------
 *   Anthropic (default)   @langchain/anthropic          yes (default dep)
 *   OpenAI                @langchain/openai             yes (default dep)
 *   Ollama                @langchain/ollama             yes (default dep)
 *   AWS Bedrock           @langchain/aws               install separately
 *   Google Gemini         @langchain/google-genai       install separately
 *
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * To swap providers:
 *   1. Comment out the active model line(s) below.
 *   2. Uncomment the section for your desired provider.
 *   3. Set the provider's env vars in `.env` (see notes inline).
 */

import "dotenv/config";
import { initChatModel } from "langchain";

// ═══ Default Models ══════════════════════════════════════════════════════════
// Workshop default: Anthropic claude-haiku-4-5, fast and cost-effective.
// Requires ANTHROPIC_API_KEY in .env
export const model = await initChatModel("anthropic:claude-haiku-4-5");

// A more capable model for steps that need stronger reasoning
export const strongModel = await initChatModel("anthropic:claude-sonnet-4-6");

// ═══ Alternative Models (comment out default above, uncomment one below) ═════
// export const model = await initChatModel("anthropic:claude-sonnet-4-6");
// export const model = await initChatModel("openai:gpt-4.1-mini");
// export const model = await initChatModel("openai:gpt-4.1");
// export const strongModel = await initChatModel("openai:gpt-4.1");

// ═══ Open-Source / Alternative Hosted Models ══════════════════════════════════

// Ollama: run models locally (no API key required)
// Install the Ollama app first: https://ollama.com
// Pull a model first, e.g.:  ollama pull llama3.2
//
// export const model = await initChatModel("ollama:llama3.2");

// OpenRouter: hosted open-source models via OpenAI-compatible API
// Free models available; sign up at openrouter.ai and get an API key
// Requires OPENROUTER_API_KEY in .env
//
// export const model = await initChatModel("openrouter:nvidia/nemotron-3-ultra-550b-a55b:free");
