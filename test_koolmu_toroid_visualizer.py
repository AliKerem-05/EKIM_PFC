import unittest
from datetime import datetime
from pathlib import Path

from KoolMu_toroid_core_library import KoolMuToroidCoreLibrary

try:
    from toroid_visualizer import PLOTLY_READY, plot_toroid, plot_toroid_3d, plot_toroid_3d_interactive, save_toroid_pdf_bundle

    VISUALIZER_READY = True
except Exception:
    VISUALIZER_READY = False
    PLOTLY_READY = False
    plot_toroid = None
    plot_toroid_3d = None
    plot_toroid_3d_interactive = None
    save_toroid_pdf_bundle = None


@unittest.skipUnless(VISUALIZER_READY, "visualizer import is unavailable")
class TestKoolMuToroidVisualizer(unittest.TestCase):
    def setUp(self) -> None:
        self.core = KoolMuToroidCoreLibrary().get_core("206")
        self.assertIsNotNone(self.core)
        self.expected_dir = Path(__file__).resolve().parent / "gorsellestirme"
        self.timestamp = datetime.now().strftime("%M_%H_%Y%m%d")

    def test_render_smoke_2d(self) -> None:
        expected_path = self.expected_dir / f"test_koolmu_toroid_render_206_{self.timestamp}.png"
        out_path = plot_toroid(self.core, turns=24, awg="18", out_path=str(expected_path), dpi=120, show=False)
        self.assertTrue(out_path.exists())
        self.assertGreater(out_path.stat().st_size, 0)
        self.assertEqual(out_path.resolve(), expected_path.resolve())

    def test_render_smoke_3d(self) -> None:
        expected_path = self.expected_dir / f"test_koolmu_toroid_render_206_{self.timestamp}_3d.png"
        out_path = plot_toroid_3d(self.core, turns=24, awg="18", out_path=str(expected_path), dpi=120, show=False)
        self.assertTrue(out_path.exists())
        self.assertGreater(out_path.stat().st_size, 0)
        self.assertEqual(out_path.resolve(), expected_path.resolve())

    def test_render_pdf_bundle(self) -> None:
        expected_2d = self.expected_dir / f"test_koolmu_toroid_render_206_{self.timestamp}.pdf"
        expected_3d = self.expected_dir / f"test_koolmu_toroid_render_206_{self.timestamp}_3d.pdf"
        out_2d, out_3d = save_toroid_pdf_bundle(
            self.core,
            turns=24,
            awg="18",
            out_path_2d=str(expected_2d),
            out_path_3d=str(expected_3d),
            dpi=120,
        )
        self.assertTrue(out_2d.exists())
        self.assertTrue(out_3d.exists())
        self.assertGreater(out_2d.stat().st_size, 0)
        self.assertGreater(out_3d.stat().st_size, 0)

    @unittest.skipUnless(PLOTLY_READY, "plotly is unavailable")
    def test_render_html_3d(self) -> None:
        expected_path = self.expected_dir / f"test_koolmu_toroid_render_206_{self.timestamp}_3d.html"
        out_path = plot_toroid_3d_interactive(self.core, turns=24, awg="18", out_path=str(expected_path))
        self.assertTrue(out_path.exists())
        self.assertGreater(out_path.stat().st_size, 0)
        self.assertEqual(out_path.resolve(), expected_path.resolve())


if __name__ == "__main__":
    unittest.main(verbosity=2)
