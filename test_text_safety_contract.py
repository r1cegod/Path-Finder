import unittest

from backend.text_safety import sanitize_student_reply, sanitize_student_stream_token


class TextSafetyContractTest(unittest.TestCase):
    def test_student_reply_sanitizer_removes_foreign_script_and_collapses_spaces(self):
        cleaned = sanitize_student_reply("nó هنوز chưa rõ")

        self.assertEqual(cleaned, "nó chưa rõ")

    def test_stream_token_sanitizer_removes_foreign_script_without_stripping_spacing(self):
        cleaned = sanitize_student_stream_token(" vẫn هنوز chưa ")

        self.assertEqual(cleaned, " vẫn  chưa ")


if __name__ == "__main__":
    unittest.main()
