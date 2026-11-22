import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dotenv import load_dotenv

from env_utils import doublecheck_env, model_auth_issues


class ModelAuthTests(unittest.TestCase):
    def test_direct_flags_require_selected_provider(self):
        for flag in ("", "false", "FALSE", "0", "no"):
            with self.subTest(flag=flag):
                self.assertIn(
                    "ANTHROPIC_API_KEY",
                    model_auth_issues({"LANGSMITH_GATEWAY": flag})[0],
                )
                self.assertEqual(
                    model_auth_issues(
                        {"LANGSMITH_GATEWAY": flag, "OPENAI_API_KEY": "direct-key"},
                        "openai",
                    ),
                    [],
                )

    def test_gateway_flags_and_key_fallback(self):
        for flag in ("true", "TRUE", "1", "yes", "https://gateway.example.com/"):
            for provider in ("anthropic", "openai", "google_genai"):
                with self.subTest(flag=flag, provider=provider):
                    values = {
                        "LANGSMITH_GATEWAY": flag,
                        "LANGSMITH_API_KEY": "workspace-key",
                    }
                    self.assertEqual(model_auth_issues(values, provider), [])
                    values["LANGSMITH_GATEWAY_API_KEY"] = ""
                    self.assertEqual(model_auth_issues(values, provider), [])
                    values["LANGSMITH_API_KEY"] = ""
                    values["LANGSMITH_GATEWAY_API_KEY"] = "gateway-key"
                    self.assertEqual(model_auth_issues(values, provider), [])

    def test_invalid_credentials_and_override(self):
        for value in (
            "",
            " ",
            "your-anthropic-api-key",
            "your_gateway_key",
            "lsv2_...",
            "<key>",
            "changeme",
            "****",
            "sk-test",
        ):
            with self.subTest(value=value):
                self.assertTrue(model_auth_issues({"ANTHROPIC_API_KEY": value}))
                self.assertTrue(
                    model_auth_issues(
                        {
                            "LANGSMITH_GATEWAY": "true",
                            "LANGSMITH_GATEWAY_API_KEY": value,
                        }
                    )
                )
        issues = model_auth_issues(
            {
                "LANGSMITH_GATEWAY": "true",
                "LANGSMITH_GATEWAY_API_KEY": "your-key",
                "LANGSMITH_API_KEY": "valid-fallback",
            }
        )
        self.assertIn("LANGSMITH_GATEWAY_API_KEY", issues[0])

    def test_tracing_and_non_gateway_providers_stay_separate(self):
        values = {
            "LANGSMITH_GATEWAY": "true",
            "LANGSMITH_GATEWAY_API_KEY": "gateway-key",
            "LANGSMITH_TRACING": "false",
        }
        self.assertEqual(model_auth_issues(values), [])
        self.assertIn("OPENROUTER_API_KEY", model_auth_issues(values, "openrouter")[0])
        self.assertEqual(model_auth_issues(values, "ollama"), [])
        values["LANGSMITH_TRACING"] = "true"
        self.assertIn("LANGSMITH_TRACING", model_auth_issues(values)[0])

    def test_provider_base_url_overrides_gateway(self):
        for provider, key in (
            ("anthropic", "ANTHROPIC_BASE_URL"),
            ("openai", "OPENAI_BASE_URL"),
        ):
            with self.subTest(provider=provider):
                issues = model_auth_issues(
                    {
                        "LANGSMITH_GATEWAY": "true",
                        "LANGSMITH_API_KEY": "gateway-key",
                        key: "https://provider.example.com",
                    },
                    provider,
                )
                self.assertIn(f"{provider.upper()}_API_KEY", issues[0])

    def test_actual_chat_models_route_without_network_calls(self):
        from langchain_anthropic import ChatAnthropic
        from langchain_openai import ChatOpenAI

        for flag in (
            "true",
            "1",
            "yes",
            "https://gateway.example.com/",
            "false",
            "0",
            "no",
            "",
        ):
            for override in ("", "override-key"):
                values = {
                    "LANGSMITH_GATEWAY": flag,
                    "LANGSMITH_API_KEY": "fallback-key",
                    "LANGSMITH_GATEWAY_API_KEY": override,
                    "ANTHROPIC_API_KEY": "anthropic-key",
                    "OPENAI_API_KEY": "openai-key",
                }
                with (
                    self.subTest(flag=flag, override=override),
                    patch.dict(os.environ, values, clear=True),
                ):
                    anthropic = ChatAnthropic(model="claude-sonnet-4-6")
                    openai = ChatOpenAI(model="gpt-4o")
                    if flag in ("false", "0", "no", ""):
                        self.assertEqual(
                            anthropic.anthropic_api_key.get_secret_value(),
                            "anthropic-key",
                        )
                        self.assertEqual(
                            openai.openai_api_key.get_secret_value(), "openai-key"
                        )
                    else:
                        root = (
                            "https://gateway.example.com"
                            if flag.startswith("https:")
                            else "https://gateway.smith.langchain.com"
                        )
                        self.assertEqual(
                            anthropic.anthropic_api_url, root + "/anthropic"
                        )
                        self.assertEqual(openai.openai_api_base, root + "/openai/v1")
                        self.assertEqual(
                            anthropic.anthropic_api_key.get_secret_value(),
                            override or "fallback-key",
                        )
                        self.assertEqual(
                            openai.openai_api_key.get_secret_value(),
                            override or "fallback-key",
                        )

    def test_shell_only_gateway_auth_is_reported_without_tracing_warning(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(
                os.environ,
                {
                    "LANGSMITH_GATEWAY": "true",
                    "LANGSMITH_API_KEY": "fallback-key",
                    "LANGSMITH_TRACING": "false",
                },
                clear=True,
            ),
        ):
            example = Path(directory) / ".env.example"
            example.write_text("ANTHROPIC_API_KEY=your-key\n")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                doublecheck_env(str(example))
            self.assertIn("LangSmith LLM Gateway", output.getvalue())
            self.assertNotIn("Issues found", output.getvalue())

    def test_dotenv_wins_and_tool_requirements_remain(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"LANGSMITH_GATEWAY": "false"}, clear=True),
        ):
            env = Path(directory) / ".env"
            example = Path(directory) / ".env.example"
            env.write_text(
                "LANGSMITH_GATEWAY=true\nLANGSMITH_GATEWAY_API_KEY=gateway-key\nLANGSMITH_TRACING=false\n"
            )
            example.write_text(
                "# Required tool credentials\nTAVILY_API_KEY=your-tool-key\nOPENAI_API_KEY=your-embedding-key\n"
            )
            load_dotenv(env, override=True)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                doublecheck_env(str(example))
            self.assertIn("TAVILY_API_KEY is required but not set", output.getvalue())
            self.assertIn("OPENAI_API_KEY is required but not set", output.getvalue())
            self.assertNotIn("ANTHROPIC_API_KEY", output.getvalue())
            self.assertIn("LangSmith LLM Gateway", output.getvalue())


if __name__ == "__main__":
    unittest.main()
