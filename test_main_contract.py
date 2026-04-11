import ast
import pathlib
import unittest


def _load_serialize_state():
    source_path = pathlib.Path(__file__).with_name("main.py")
    source = source_path.read_text(encoding="utf-8")
    module = ast.parse(source, filename=str(source_path))

    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == "serialize_state":
            function_module = ast.Module(body=[node], type_ignores=[])
            namespace: dict[str, object] = {}
            exec(compile(function_module, filename=str(source_path), mode="exec"), namespace)
            return namespace["serialize_state"]

    raise RuntimeError("serialize_state not found in main.py")


serialize_state = _load_serialize_state()


class MainContractTest(unittest.TestCase):
    def test_serialize_state_normalizes_university_to_uni(self):
        result = {
            "stage": {"current_stage": "university"},
            "university": {"done": True},
        }

        serialized = serialize_state(result)

        self.assertEqual(serialized["currentStage"], "uni")
        self.assertEqual(serialized["completedStages"], ["uni"])

    def test_serialize_state_maps_forced_anchor_stage(self):
        result = {
            "stage": {
                "current_stage": "thinking",
                "anchor_stage": "university",
                "anchor_mode": "forced",
            },
        }

        serialized = serialize_state(result)

        self.assertEqual(serialized["currentStage"], "thinking")
        self.assertEqual(serialized["forcedStage"], "uni")


if __name__ == "__main__":
    unittest.main()
