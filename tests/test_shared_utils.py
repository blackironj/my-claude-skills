"""Unit tests for skills/shared_utils.py."""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

# Add skills/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills"))
import shared_utils


class TestCleanContent(unittest.TestCase):
    def test_strips_system_reminder(self):
        text = "hello <system-reminder>secret</system-reminder> world"
        self.assertEqual(shared_utils.clean_content(text), "hello  world")

    def test_strips_task_notification(self):
        text = "before <task-notification>task stuff</task-notification> after"
        self.assertEqual(shared_utils.clean_content(text), "before  after")

    def test_preserves_plain_text(self):
        self.assertEqual(shared_utils.clean_content("just text"), "just text")

    def test_non_string_returns_empty(self):
        self.assertEqual(shared_utils.clean_content(None), "")
        self.assertEqual(shared_utils.clean_content(123), "")

    def test_clean_text_is_alias(self):
        self.assertIs(shared_utils.clean_text, shared_utils.clean_content)


class TestExtractText(unittest.TestCase):
    def test_string_input(self):
        self.assertEqual(shared_utils.extract_text("hello"), "hello")

    def test_list_of_text_blocks(self):
        content = [
            {"type": "text", "text": "line1"},
            {"type": "text", "text": "line2"},
        ]
        self.assertEqual(shared_utils.extract_text(content), "line1\nline2")

    def test_skips_non_text_blocks(self):
        content = [
            {"type": "text", "text": "hello"},
            {"type": "tool_use", "name": "Bash"},
        ]
        self.assertEqual(shared_utils.extract_text(content), "hello")

    def test_mixed_string_and_dict(self):
        content = ["raw string", {"type": "text", "text": "block"}]
        self.assertEqual(shared_utils.extract_text(content), "raw string\nblock")

    def test_empty_list(self):
        self.assertEqual(shared_utils.extract_text([]), "")

    def test_none_returns_empty(self):
        self.assertEqual(shared_utils.extract_text(None), "")

    def test_int_returns_empty(self):
        self.assertEqual(shared_utils.extract_text(42), "")


class TestIterContentBlocks(unittest.TestCase):
    def test_filters_by_type(self):
        content = [
            {"type": "text", "text": "hello"},
            {"type": "tool_use", "name": "Bash"},
            {"type": "text", "text": "world"},
        ]
        result = list(shared_utils.iter_content_blocks(content, "text"))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["text"], "hello")

    def test_no_filter(self):
        content = [
            {"type": "text", "text": "a"},
            {"type": "tool_use", "name": "B"},
        ]
        result = list(shared_utils.iter_content_blocks(content))
        self.assertEqual(len(result), 2)

    def test_non_list_yields_nothing(self):
        self.assertEqual(list(shared_utils.iter_content_blocks("string")), [])
        self.assertEqual(list(shared_utils.iter_content_blocks(None)), [])

    def test_skips_non_dict(self):
        content = ["raw string", {"type": "text", "text": "ok"}]
        result = list(shared_utils.iter_content_blocks(content))
        self.assertEqual(len(result), 1)


class TestExtractAssistantData(unittest.TestCase):
    def test_text_and_skills(self):
        content = [
            {"type": "text", "text": "I'll help with that."},
            {"type": "tool_use", "name": "Skill", "input": {"skill": "tdd"}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
            {"type": "text", "text": "Done."},
        ]
        text, skills = shared_utils.extract_assistant_data(content)
        self.assertEqual(text, "I'll help with that.\nDone.")
        self.assertEqual(skills, ["tdd"])

    def test_no_skills(self):
        content = [{"type": "text", "text": "hello"}]
        text, skills = shared_utils.extract_assistant_data(content)
        self.assertEqual(text, "hello")
        self.assertEqual(skills, [])

    def test_empty_content(self):
        text, skills = shared_utils.extract_assistant_data([])
        self.assertEqual(text, "")
        self.assertEqual(skills, [])

    def test_skips_empty_text(self):
        content = [{"type": "text", "text": "  "}, {"type": "text", "text": "real"}]
        text, skills = shared_utils.extract_assistant_data(content)
        self.assertEqual(text, "real")


class TestParseIsoTimestamp(unittest.TestCase):
    def test_z_suffix(self):
        dt = shared_utils.parse_iso_timestamp("2026-03-26T10:00:00Z")
        self.assertEqual(dt.tzinfo, timezone.utc)
        self.assertEqual(dt.hour, 10)

    def test_offset_suffix(self):
        dt = shared_utils.parse_iso_timestamp("2026-03-26T10:00:00+09:00")
        self.assertEqual(dt.hour, 10)

    def test_with_tz_conversion(self):
        dt = shared_utils.parse_iso_timestamp("2026-03-26T00:00:00Z", tz=timezone.utc)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_returns_datetime(self):
        dt = shared_utils.parse_iso_timestamp("2026-01-01T12:00:00Z")
        self.assertIsInstance(dt, datetime)


class TestParseFrontmatter(unittest.TestCase):
    def test_simple_key_value(self):
        content = "---\ntitle: Hello\ndate: 2026-01-01\n---\nBody\n"
        fm = shared_utils.parse_frontmatter(content)
        self.assertEqual(fm["title"], "Hello")
        self.assertEqual(fm["date"], "2026-01-01")

    def test_quoted_value(self):
        content = '---\ntitle: "Hello World"\n---\nBody\n'
        fm = shared_utils.parse_frontmatter(content)
        self.assertEqual(fm["title"], "Hello World")

    def test_array(self):
        content = "---\ntags:\n  - python\n  - refactor\n---\nBody\n"
        fm = shared_utils.parse_frontmatter(content)
        self.assertEqual(fm["tags"], ["python", "refactor"])

    def test_empty_array(self):
        content = "---\ntags: []\n---\nBody\n"
        fm = shared_utils.parse_frontmatter(content)
        self.assertEqual(fm["tags"], [])

    def test_multiline_value(self):
        content = "---\ncomments: |\n  line one\n  line two\n---\nBody\n"
        fm = shared_utils.parse_frontmatter(content)
        self.assertEqual(fm["comments"], "line one\nline two")

    def test_no_frontmatter(self):
        self.assertEqual(shared_utils.parse_frontmatter("No frontmatter"), {})

    def test_value_with_colon(self):
        content = "---\nurl: https://example.com\n---\nBody\n"
        fm = shared_utils.parse_frontmatter(content)
        self.assertEqual(fm["url"], "https://example.com")

    def test_mixed_types(self):
        content = "---\ntitle: Test\ntags:\n  - a\n  - b\ncomments: |\n  note\nstatus: active\n---\nBody\n"
        fm = shared_utils.parse_frontmatter(content)
        self.assertEqual(fm["title"], "Test")
        self.assertEqual(fm["tags"], ["a", "b"])
        self.assertEqual(fm["comments"], "note")
        self.assertEqual(fm["status"], "active")


class TestParseFrontmatterFile(unittest.TestCase):
    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("---\ntitle: Test\n---\nBody\n")
            f.flush()
            result = shared_utils.parse_frontmatter_file(f.name)
        os.unlink(f.name)
        self.assertEqual(result["title"], "Test")

    def test_missing_file(self):
        self.assertIsNone(shared_utils.parse_frontmatter_file("/nonexistent/path.md"))

    def test_no_frontmatter_returns_none(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("No frontmatter here\n")
            f.flush()
            result = shared_utils.parse_frontmatter_file(f.name)
        os.unlink(f.name)
        self.assertIsNone(result)


class TestParseJsonl(unittest.TestCase):
    def test_valid_jsonl(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"type": "user"}\n{"type": "assistant"}\n')
            f.flush()
            records = shared_utils.parse_jsonl(f.name)
        os.unlink(f.name)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["type"], "user")

    def test_skips_invalid_lines(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"ok": true}\nnot json\n{"ok": false}\n')
            f.flush()
            records = shared_utils.parse_jsonl(f.name)
        os.unlink(f.name)
        self.assertEqual(len(records), 2)

    def test_missing_file(self):
        self.assertEqual(shared_utils.parse_jsonl("/nonexistent.jsonl"), [])

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write("")
            f.flush()
            records = shared_utils.parse_jsonl(f.name)
        os.unlink(f.name)
        self.assertEqual(records, [])


class TestDeriveTitle(unittest.TestCase):
    def test_simple_message(self):
        self.assertEqual(shared_utils.derive_title(["Fix the login bug"]), "Fix the login bug")

    def test_skips_skill_instructions(self):
        msgs = ["Base directory for this skill: /path", "Actual question"]
        self.assertEqual(shared_utils.derive_title(msgs), "Actual question")

    def test_skips_short_messages(self):
        msgs = ["hi", "ok", "Refactor the auth module"]
        self.assertEqual(shared_utils.derive_title(msgs), "Refactor the auth module")

    def test_strips_markdown_headers(self):
        self.assertEqual(shared_utils.derive_title(["## My Title"]), "My Title")
        self.assertEqual(shared_utils.derive_title(["# H1 Title"]), "H1 Title")

    def test_truncation_with_ellipsis(self):
        long_msg = "A" * 100
        result = shared_utils.derive_title([long_msg], max_len=80)
        self.assertEqual(len(result), 80)
        self.assertTrue(result.endswith("..."))

    def test_empty_returns_untitled(self):
        self.assertEqual(shared_utils.derive_title([]), "Untitled")

    def test_only_noise_returns_untitled(self):
        msgs = ["Base directory for this skill: /foo", "hi"]
        self.assertEqual(shared_utils.derive_title(msgs), "Untitled")

    def test_continue_prefix(self):
        msgs = ["## Continue: Previous task name\nMore context here"]
        result = shared_utils.derive_title(msgs)
        self.assertEqual(result, "Previous task name")

    def test_newlines_collapsed(self):
        result = shared_utils.derive_title(["Line one\nLine two"])
        self.assertEqual(result, "Line one Line two")


class TestShortId(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(shared_utils.short_id("abcdef1234567890"), "abcdef12")

    def test_length(self):
        self.assertEqual(len(shared_utils.short_id("a" * 36)), shared_utils.SHORT_ID_LEN)

    def test_constant_value(self):
        self.assertEqual(shared_utils.SHORT_ID_LEN, 8)


if __name__ == "__main__":
    unittest.main()
