import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from asset_quant.reporting.charts_svg import _risk_return_svg, write_comparison_charts


PERIODS = ("weekly", "monthly", "quarterly", "semiannual", "annual")


def _results():
    rows = []
    for period_index, period in enumerate(PERIODS):
        for weight in range(0, 101, 10):
            rows.append(
                {
                    "rebalance_period": period,
                    "weight_480080_pct": weight,
                    "weight_480081_pct": 100 - weight,
                    "annualized_return": 0.04 + weight / 1000 + period_index / 100,
                    "annualized_volatility": 0.1 + weight / 1000,
                    "maximum_drawdown": -0.3 + weight / 1000,
                    "sharpe_ratio": 0.2 + period_index / 10 + weight / 100,
                }
            )
    return rows


class ChartsSvgTests(unittest.TestCase):
    def test_writes_complete_heatmaps_and_55_distinguishable_scatter_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            heatmap_path, scatter_path = write_comparison_charts(_results(), directory)
            heatmap = ET.parse(heatmap_path).getroot()
            scatter = ET.parse(scatter_path).getroot()

        ns = {"svg": "http://www.w3.org/2000/svg"}
        panels = heatmap.findall(".//svg:g[@class='heatmap-panel']", ns)
        self.assertEqual(len(panels), 3)
        background = heatmap.find("svg:rect[@class='background']", ns)
        self.assertIsNotNone(background)
        self.assertEqual(background.attrib["fill"], "#ffffff")
        for panel in panels:
            cells = [
                cell for cell in panel.findall(".//svg:rect", ns)
                if "heatmap-cell" in cell.attrib.get("class", "").split()
            ]
            self.assertEqual(len(cells), 55)
            self.assertEqual(
                {cell.attrib["data-weight"] for cell in cells},
                {str(weight) for weight in range(0, 101, 10)},
            )
            self.assertEqual(
                {cell.attrib["data-period"] for cell in cells}, set(PERIODS)
            )
            self.assertTrue(all("data-value" in cell.attrib for cell in cells))
            expected_metric = panel.attrib["data-metric"]
            source = {
                (float(row["weight_480080_pct"]), row["rebalance_period"]): row
                for row in _results()
            }
            for cell in cells:
                key = (float(cell.attrib["data-weight"]), cell.attrib["data-period"])
                self.assertAlmostEqual(
                    float(cell.attrib["data-value"]), float(source[key][expected_metric])
                )
        for current, following in zip(panels, panels[1:]):
            current_cells = [
                cell for cell in current.findall(".//svg:rect", ns)
                if "heatmap-cell" in cell.attrib.get("class", "").split()
            ]
            current_bottom = max(
                float(cell.attrib["y"]) + float(cell.attrib["height"])
                for cell in current_cells
            )
            following_title = following.find("svg:text[@class='panel-title']", ns)
            self.assertLess(current_bottom, float(following_title.attrib["y"]))

        points = scatter.findall(".//svg:circle[@class='case-point']", ns)
        self.assertEqual(len(points), 55)
        self.assertEqual({point.attrib["data-period"] for point in points}, set(PERIODS))
        self.assertTrue(all(point.attrib.get("fill") for point in points))

    def test_scatter_marks_all_three_metric_leaders(self):
        with tempfile.TemporaryDirectory() as directory:
            _, scatter_path = write_comparison_charts(_results(), directory)
            root = ET.parse(scatter_path).getroot()
        ns = {"svg": "http://www.w3.org/2000/svg"}
        labels = {
            item.attrib["data-leader"]
            for item in root.findall(".//svg:text[@class='leader-label']", ns)
        }
        self.assertEqual(labels, {"annualized_return", "sharpe_ratio", "maximum_drawdown"})

    def test_both_svgs_have_accessible_metadata_valid_xml_and_escape_dynamic_labels(self):
        rows = _results()
        with tempfile.TemporaryDirectory() as directory:
            paths = write_comparison_charts(rows, directory)
            for path in paths:
                root = ET.parse(path).getroot()
                ns = {"svg": "http://www.w3.org/2000/svg"}
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                self.assertTrue(root.find("svg:title", ns).text)
                self.assertTrue(root.find("svg:desc", ns).text)
                background = root.find("svg:rect[@class='background']", ns)
                self.assertIsNotNone(background)
                self.assertEqual(background.attrib["fill"], "#ffffff")
        rows[0]["rebalance_period"] = "周<&期"
        escaped_svg = _risk_return_svg(rows)
        ET.fromstring(escaped_svg)
        self.assertNotIn("周<&期", escaped_svg)
        self.assertIn("周&lt;&amp;期", escaped_svg)


if __name__ == "__main__":
    unittest.main()
