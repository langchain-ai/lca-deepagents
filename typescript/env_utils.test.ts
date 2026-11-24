import { ChatAnthropic } from "@langchain/anthropic";
import { ChatOpenAI } from "@langchain/openai";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";

import { doublecheckEnv, modelAuthIssues } from "./env_utils.js";

test("direct flags require the selected provider", () => {
  for (const flag of ["", "false", "FALSE", "0", "no"]) {
    assert.match(modelAuthIssues({ LANGSMITH_GATEWAY: flag })[0], /ANTHROPIC_API_KEY/);
    assert.deepEqual(modelAuthIssues({ LANGSMITH_GATEWAY: flag, OPENAI_API_KEY: "direct-key" }, "openai"), []);
  }
});

test("gateway flags accept an override or LangSmith fallback without provider keys", () => {
  for (const flag of ["true", "TRUE", "1", "yes", "https://gateway.example.com/"]) {
    for (const provider of ["anthropic", "openai"]) {
      const values = { LANGSMITH_GATEWAY: flag, LANGSMITH_API_KEY: "workspace-key", LANGSMITH_GATEWAY_API_KEY: "" };
      assert.deepEqual(modelAuthIssues(values, provider), []);
      values.LANGSMITH_API_KEY = "";
      values.LANGSMITH_GATEWAY_API_KEY = "gateway-key";
      assert.deepEqual(modelAuthIssues(values, provider), []);
    }
  }
});

test("invalid credentials and placeholder overrides are reported", () => {
  for (const value of ["", " ", "your-anthropic-api-key", "your_gateway_key", "lsv2_...", "<key>", "changeme", "****", "sk-test"]) {
    assert.ok(modelAuthIssues({ ANTHROPIC_API_KEY: value }).length);
    assert.ok(modelAuthIssues({ LANGSMITH_GATEWAY: "true", LANGSMITH_GATEWAY_API_KEY: value }).length);
  }
  assert.match(modelAuthIssues({ LANGSMITH_GATEWAY: "true", LANGSMITH_GATEWAY_API_KEY: "your-key", LANGSMITH_API_KEY: "valid-fallback" })[0], /LANGSMITH_GATEWAY_API_KEY/);
});

test("tracing, unsupported providers, and local models remain separate", () => {
  const values = { LANGSMITH_GATEWAY: "true", LANGSMITH_GATEWAY_API_KEY: "gateway-key", LANGSMITH_TRACING: "false" };
  assert.deepEqual(modelAuthIssues(values), []);
  assert.match(modelAuthIssues(values, "openrouter")[0], /OPENROUTER_API_KEY/);
  assert.match(modelAuthIssues(values, "google_genai")[0], /GOOGLE_API_KEY/);
  assert.deepEqual(modelAuthIssues(values, "ollama"), []);
  values.LANGSMITH_TRACING = "true";
  assert.match(modelAuthIssues(values)[0], /LANGSMITH_TRACING/);
});

test("dotenv wins over shell for model auth and tracing; tool requirements remain", () => {
  const directory = mkdtempSync(path.join(tmpdir(), "academy-env-"));
  const previous = process.env.LANGSMITH_GATEWAY;
  const output: string[] = [];
  const log = console.log;
  try {
    process.env.LANGSMITH_GATEWAY = "false";
    console.log = (...args: unknown[]) => output.push(args.join(" "));
    const example = path.join(directory, ".env.example");
    const env = path.join(directory, ".env");
    writeFileSync(example, "# Required tool credentials\nTAVILY_API_KEY=your-tool-key\nOPENAI_API_KEY=your-embedding-key\n");
    writeFileSync(env, "LANGSMITH_GATEWAY=true\nLANGSMITH_GATEWAY_API_KEY=gateway-key\nLANGSMITH_TRACING=false\n");
    doublecheckEnv(example, env);
    assert.match(output.join("\n"), /TAVILY_API_KEY is required but not set/);
    assert.match(output.join("\n"), /OPENAI_API_KEY is required but not set/);
    assert.doesNotMatch(output.join("\n"), /ANTHROPIC_API_KEY/);
    assert.match(output.join("\n"), /LangSmith LLM Gateway/);
  } finally {
    console.log = log;
    if (previous === undefined) delete process.env.LANGSMITH_GATEWAY;
    else process.env.LANGSMITH_GATEWAY = previous;
    rmSync(directory, { recursive: true, force: true });
  }
});

test("provider base URL overrides gateway mode", () => {
  assert.match(modelAuthIssues({ LANGSMITH_GATEWAY: "true", LANGSMITH_API_KEY: "gateway-key", ANTHROPIC_BASE_URL: "https://provider.example.com" })[0], /ANTHROPIC_API_KEY/);
  assert.match(modelAuthIssues({ LANGSMITH_GATEWAY: "true", LANGSMITH_API_KEY: "gateway-key", OPENAI_BASE_URL: "https://provider.example.com" }, "openai")[0], /OPENAI_API_KEY/);
});

test("actual chat models route with flags and key fallback without network calls", () => {
  const previous = process.env;
  try {
    for (const flag of ["true", "1", "yes", "https://gateway.example.com/", "false", "0", "no", ""]) {
      for (const override of ["", "override-key"]) {
        process.env = { LANGSMITH_GATEWAY: flag, LANGSMITH_API_KEY: "fallback-key", LANGSMITH_GATEWAY_API_KEY: override, ANTHROPIC_API_KEY: "anthropic-key", OPENAI_API_KEY: "openai-key" };
        const anthropic = new ChatAnthropic({ model: "claude-sonnet-4-6" });
        const openai = new ChatOpenAI({ model: "gpt-4o" });
        if (["false", "0", "no", ""].includes(flag)) {
          assert.equal(anthropic.apiKey, "anthropic-key");
          assert.equal(openai.apiKey, "openai-key");
        } else {
          const root = flag.startsWith("https:") ? "https://gateway.example.com" : "https://gateway.smith.langchain.com";
          assert.equal(anthropic.apiUrl, root + "/anthropic");
          assert.equal(openai.clientConfig.baseURL, root + "/openai/v1");
          assert.equal(anthropic.apiKey, override || "fallback-key");
          assert.equal(openai.apiKey, override || "fallback-key");
        }
      }
    }
  } finally {
    process.env = previous;
  }
});

test("shell-only gateway auth reports its mode without a tracing warning", () => {
  const directory = mkdtempSync(path.join(tmpdir(), "academy-shell-"));
  const previous = process.env;
  const log = console.log;
  const output: string[] = [];
  try {
    process.env = { LANGSMITH_GATEWAY: "true", LANGSMITH_API_KEY: "fallback-key", LANGSMITH_TRACING: "false" };
    console.log = (...args: unknown[]) => output.push(args.join(" "));
    const example = path.join(directory, ".env.example");
    writeFileSync(example, "ANTHROPIC_API_KEY=your-key\n");
    doublecheckEnv(example, path.join(directory, ".env"));
    assert.match(output.join("\n"), /LangSmith LLM Gateway/);
    assert.doesNotMatch(output.join("\n"), /Issues found/);
  } finally {
    process.env = previous;
    console.log = log;
    rmSync(directory, { recursive: true, force: true });
  }
});
