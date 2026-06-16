"""Lightweight checks for versioned agent prompt templates."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from incident_copilot.adk_agents import SPECIALIST_AGENT_NAMES, SUMMARY_SAFETY_AGENT_NAME
from incident_copilot.paths import project_root

PROMPTS_DIR = project_root() / "prompts"

EXPECTED_PROMPT_FILES = (
    "README.md",
    "coordinator.md",
    "airflow-investigator.md",
    "kubernetes-investigator.md",
    "logs-metrics-investigator.md",
    "runbook-advisor.md",
    "summary-safety.md",
)

REQUIRED_SECTIONS = (
    "## Role",
    "## Inputs",
    "## Tools or context available",
    "## Required output behavior",
    "## Safety constraints",
    "## Evidence requirements",
    "## Contract alignment",
    "## What not to do",
)

CONTRACT_KEYWORDS = (
    "output contract",
    "root_cause",
    "evidence",
    "clarifying_questions",
    "rollback",
)

FORBIDDEN_INSTRUCTION_PATTERNS = (
    re.compile(r"provide (your )?api key", re.IGNORECASE),
    re.compile(r"use real production", re.IGNORECASE),
    re.compile(r"connect to live", re.IGNORECASE),
    re.compile(r"deploy to (cloud run|production)", re.IGNORECASE),
)


def _find_forbidden_instruction(content: str, pattern: re.Pattern[str]) -> re.Match[str] | None:
    for match in pattern.finditer(content):
        prefix = content[max(0, match.start() - 32) : match.start()].casefold()
        normalized = re.sub(r"\s+", " ", prefix)
        if normalized.endswith("do not ") or " do not " in normalized:
            continue
        return match
    return None


class PromptTemplateTests(unittest.TestCase):
    def test_all_expected_prompt_files_exist(self) -> None:
        for filename in EXPECTED_PROMPT_FILES:
            path = PROMPTS_DIR / filename
            self.assertTrue(path.is_file(), msg=f"missing prompt file: {filename}")

    def test_prompt_files_are_non_empty(self) -> None:
        for filename in EXPECTED_PROMPT_FILES:
            content = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
            self.assertTrue(content.strip(), msg=f"empty prompt file: {filename}")

    def test_agent_prompts_include_required_sections(self) -> None:
        agent_prompts = [name for name in EXPECTED_PROMPT_FILES if name != "README.md"]
        for filename in agent_prompts:
            content = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
            for section in REQUIRED_SECTIONS:
                self.assertIn(
                    section,
                    content,
                    msg=f"{filename} missing section: {section}",
                )

    def test_coordinator_references_all_specialists(self) -> None:
        content = (PROMPTS_DIR / "coordinator.md").read_text(encoding="utf-8")
        for specialist in SPECIALIST_AGENT_NAMES:
            self.assertIn(specialist, content)
        self.assertIn(SUMMARY_SAFETY_AGENT_NAME, content)

    def test_prompts_reference_evidence_and_contract_behavior(self) -> None:
        agent_prompts = [name for name in EXPECTED_PROMPT_FILES if name != "README.md"]
        for filename in agent_prompts:
            content = (PROMPTS_DIR / filename).read_text(encoding="utf-8").casefold()
            self.assertIn("evidence", content, msg=f"{filename} should mention evidence")
            matched = sum(1 for keyword in CONTRACT_KEYWORDS if keyword in content)
            self.assertGreaterEqual(
                matched,
                2,
                msg=f"{filename} should reference output contract behavior",
            )

    def test_prompts_mention_mock_capstone_context(self) -> None:
        agent_prompts = [name for name in EXPECTED_PROMPT_FILES if name != "README.md"]
        for filename in agent_prompts:
            content = (PROMPTS_DIR / filename).read_text(encoding="utf-8").casefold()
            self.assertIn("mock", content, msg=f"{filename} should mention mock data/tools")

    def test_prompts_do_not_request_live_credentials_or_cloud_access(self) -> None:
        agent_prompts = [name for name in EXPECTED_PROMPT_FILES if name != "README.md"]
        for filename in agent_prompts:
            content = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
            for pattern in FORBIDDEN_INSTRUCTION_PATTERNS:
                match = _find_forbidden_instruction(content, pattern)
                self.assertIsNone(
                    match,
                    msg=f"{filename} contains forbidden instruction: {pattern.pattern}",
                )

    def test_prompts_are_markdown_files(self) -> None:
        for filename in EXPECTED_PROMPT_FILES:
            self.assertTrue(filename.endswith(".md"))
            content = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
            self.assertTrue(content.startswith("#"), msg=f"{filename} should start with heading")


if __name__ == "__main__":
    unittest.main()
