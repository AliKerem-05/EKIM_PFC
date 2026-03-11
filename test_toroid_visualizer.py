import unittest
from datetime import datetime
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

        expected_dir = Path(__file__).resolve().parent / "gorsellestirme"
        timestamp = datetime.now().strftime("%M_%H_%Y%m%d")
        expected_path = expected_dir / f"test_toroid_visualizer_render_{timestamp}.png"

        out_path = plot_toroid(core, turns=24, awg="18", out_path=str(expected_path), dpi=120, show=False)
        self.assertTrue(out_path.exists())
        self.assertGreater(out_path.stat().st_size, 0)
        self.assertEqual(out_path.resolve(), expected_path.resolve())


if __name__ == "__main__":
    unittest.main(verbosity=2)
