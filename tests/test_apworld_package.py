from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_builder():
    path = ROOT / "tools" / "build_apworld_official.py"
    spec = importlib.util.spec_from_file_location("mainline_apworld_builder", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class APWorldPackageTests(unittest.TestCase):
    def test_normalization_is_byte_deterministic(self) -> None:
        builder = load_builder()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_source = root / "first.zip"
            second_source = root / "second.zip"
            with zipfile.ZipFile(first_source, "w") as archive:
                archive.writestr("b.py", b"b")
                archive.writestr("a.json", b"a")
            with zipfile.ZipFile(second_source, "w") as archive:
                archive.writestr("a.json", b"a")
                archive.writestr("b.py", b"b")
            first_output = root / "first.apworld"
            second_output = root / "second.apworld"
            builder.normalize_apworld(first_source, first_output)
            builder.normalize_apworld(second_source, second_output)
            self.assertEqual(
                hashlib.sha256(first_output.read_bytes()).digest(),
                hashlib.sha256(second_output.read_bytes()).digest(),
            )


if __name__ == "__main__":
    unittest.main()
