import unittest
from pathlib import Path

from toroid_core_library import ToroidCoreLibrary

try:
    from toroid_visualizer import plot_toroid

    MATPLOTLIB_READY = True
except Exception:
    MATPLOTLIB_READY = False
    plot_toroid = None


@unittest.skipUnless(MATPLOTLIB_READY, "matplotlib or visualizer import is unavailable")
class TestToroidVisualizer(unittest.TestCase):
    def test_render_smoke(self) -> None:
        lib = ToroidCoreLibrary()
        core = lib.get_core("2206")
        self.assertIsNotNone(core)

        out_path = plot_toroid(core, turns=24, awg="18", out_path=None, dpi=120, show=False)
        self.assertTrue(out_path.exists())
        self.assertGreater(out_path.stat().st_size, 0)

        expected_dir = Path(__file__).resolve().parent / "gorsellestirme"
        self.assertEqual(out_path.parent.resolve(), expected_dir.resolve())


if __name__ == "__main__":
    unittest.main(verbosity=2)
