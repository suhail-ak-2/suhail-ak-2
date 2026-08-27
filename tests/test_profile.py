from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CARD = ROOT / "assets" / "profile-terminal.svg"
MOBILE_CARD = ROOT / "assets" / "profile-terminal-mobile.svg"
LIGHT_CARD = ROOT / "assets" / "profile-terminal-light.svg"
LIGHT_MOBILE_CARD = ROOT / "assets" / "profile-terminal-mobile-light.svg"


class ProfileReadmeTests(unittest.TestCase):
    def test_readme_switches_local_cards_for_theme_and_viewport(self):
        content = README.read_text(encoding="utf-8")

        self.assertIn("assets/profile-terminal.svg", content)
        self.assertIn("assets/profile-terminal-mobile.svg", content)
        self.assertIn("assets/profile-terminal-light.svg", content)
        self.assertIn("assets/profile-terminal-mobile-light.svg", content)
        self.assertIn("prefers-color-scheme: dark", content)
        self.assertIn(
            "(prefers-color-scheme: dark) and (max-width: 640px)", content
        )
        self.assertIn('media="(max-width: 640px)"', content)
        self.assertIn("Agentic AI Engineer focused on MCP, RAG and LLM platforms", content)
        self.assertIn("23 public repos, 7 original projects and 20 stars", content)
        self.assertNotIn("github-readme-stats", content)

    def test_card_is_a_valid_responsive_svg(self):
        root = ET.parse(CARD).getroot()

        self.assertEqual(root.attrib["viewBox"], "0 0 1200 560")
        self.assertEqual(root.attrib["role"], "img")
        self.assertIn("aria-labelledby", root.attrib)
        self.assertNotIn("width", root.attrib)
        self.assertNotIn("height", root.attrib)

        mobile_root = ET.parse(MOBILE_CARD).getroot()
        self.assertEqual(mobile_root.attrib["viewBox"], "0 0 560 1135")
        self.assertEqual(mobile_root.attrib["role"], "img")
        self.assertIn("aria-labelledby", mobile_root.attrib)
        self.assertNotIn("width", mobile_root.attrib)
        self.assertNotIn("height", mobile_root.attrib)

        mobile_text = {
            "".join(element.itertext()): element.attrib
            for element in mobile_root.iter()
            if element.tag.endswith("text")
        }
        self.assertNotEqual(mobile_text["Repos"]["y"], mobile_text["Stars"]["y"])

    def test_card_contains_verified_identity_and_project_data(self):
        content = CARD.read_text(encoding="utf-8")

        for expected in (
            "Suhail @suhail-ak-2",
            "Agentic AI Engineer",
            "MCP · RAG · LLM Platforms",
            "LIFEOSAI",
            "Typesense MCP Server",
            "Claude Code UI",
            "Public repos",
            "23",
            "Stars earned",
            "20",
            "agents with roles, tasks &amp; accountability",
        ):
            self.assertIn(expected, content)

        texts = [
            "".join(element.itertext())
            for element in ET.parse(CARD).getroot().iter()
            if element.tag.endswith("text")
        ]
        adjacent_pairs = set(zip(texts, texts[1:]))
        self.assertIn(("Public repos", "23"), adjacent_pairs)
        self.assertIn(("Original projects", "7"), adjacent_pairs)
        self.assertIn(("Stars earned", "20"), adjacent_pairs)
        self.assertIn(
            ("Typesense MCP Server", "AI search bridge · 19 stars"), adjacent_pairs
        )

    def test_card_uses_the_approved_palette_and_a_substantial_ascii_portrait(self):
        content = CARD.read_text(encoding="utf-8")

        for color in ("#0D1117", "#161B22", "#79C0FF", "#E3B341", "#7EE787"):
            self.assertIn(color, content)

        root = ET.parse(CARD).getroot()
        portrait = next(element for element in root.iter() if element.attrib.get("id") == "ascii-portrait")
        rows = ["".join(element.itertext()) for element in portrait if element.tag.endswith("text")]
        visible_rows = [row for row in rows if row.strip()]
        visible_characters = set("".join(visible_rows)) - {" "}
        self.assertGreaterEqual(len(visible_rows), 28)
        self.assertGreaterEqual(len(visible_characters), 8)

    def test_portrait_is_a_pure_text_full_body_figure(self):
        def portrait_rows(path):
            root = ET.parse(path).getroot()
            portrait = next(
                element for element in root.iter() if element.attrib.get("id") == "ascii-portrait"
            )
            self.assertFalse(
                any(element.tag.endswith("image") for element in portrait.iter())
            )
            rows = [
                "".join(element.itertext())
                for element in portrait
                if element.tag.endswith("text") and "".join(element.itertext()).strip()
            ]
            return rows

        def has_two_legs(row):
            return re.search(r"\S{4,}\s{3,}\S{4,}", row) is not None

        desktop_rows = portrait_rows(CARD)
        mobile_rows = portrait_rows(MOBILE_CARD)
        lower_body = desktop_rows[int(len(desktop_rows) * 0.62) :]

        self.assertGreaterEqual(len(desktop_rows), 80)
        self.assertGreaterEqual(sum(has_two_legs(row) for row in lower_body), 18)
        self.assertEqual(desktop_rows, mobile_rows)

    def test_portrait_rendering_preserves_the_approved_body_proportions(self):
        def rendered_aspect(path):
            root = ET.parse(path).getroot()
            portrait = next(
                element for element in root.iter() if element.attrib.get("id") == "ascii-portrait"
            )
            rows = [
                element
                for element in portrait
                if element.tag.endswith("text") and "".join(element.itertext()).strip()
            ]
            left = min(
                len("".join(row.itertext())) - len("".join(row.itertext()).lstrip())
                for row in rows
            )
            right = max(len("".join(row.itertext()).rstrip()) for row in rows)
            transform = portrait.attrib.get("transform", "matrix(1 0 0 1 0 0)")
            match = re.fullmatch(
                r"matrix\(([0-9.]+) 0 0 1 [-0-9.]+ 0\)", transform
            )
            self.assertIsNotNone(match)
            scale_x = float(match.group(1))
            font_size = float(portrait.attrib["font-size"])
            first_y = float(rows[0].attrib["y"])
            last_y = float(rows[-1].attrib["y"])
            rendered_width = (right - left) * font_size * 0.6 * scale_x
            rendered_height = last_y - first_y + font_size
            return rendered_width / rendered_height

        for path in (CARD, MOBILE_CARD):
            self.assertAlmostEqual(rendered_aspect(path), 0.269, delta=0.035)

    def test_light_cards_match_dark_content_with_a_light_palette(self):
        for dark_path, light_path in (
            (CARD, LIGHT_CARD),
            (MOBILE_CARD, LIGHT_MOBILE_CARD),
        ):
            self.assertTrue(light_path.exists())
            dark_root = ET.parse(dark_path).getroot()
            light_root = ET.parse(light_path).getroot()
            light_rects = [
                element for element in light_root.iter() if element.tag.endswith("rect")
            ]
            self.assertEqual(light_rects[0].attrib["fill"], "#F6F8FA")
            self.assertEqual(light_rects[1].attrib["fill"], "#FFFFFF")
            dark_text = [
                "".join(element.itertext())
                for element in dark_root.iter()
                if element.tag.endswith("text")
            ]
            light_text = [
                "".join(element.itertext())
                for element in light_root.iter()
                if element.tag.endswith("text")
            ]
            self.assertEqual(light_text, dark_text)

    def test_light_portraits_use_heavier_glyphs_without_changing_geometry(self):
        for dark_path, light_path in (
            (CARD, LIGHT_CARD),
            (MOBILE_CARD, LIGHT_MOBILE_CARD),
        ):
            dark_root = ET.parse(dark_path).getroot()
            light_root = ET.parse(light_path).getroot()
            dark_portrait = next(
                element for element in dark_root.iter() if element.attrib.get("id") == "ascii-portrait"
            )
            light_portrait = next(
                element for element in light_root.iter() if element.attrib.get("id") == "ascii-portrait"
            )

            self.assertNotIn("font-weight", dark_portrait.attrib)
            self.assertEqual(light_portrait.attrib.get("font-weight"), "700")
            self.assertNotIn("stroke", dark_portrait.attrib)
            self.assertEqual(
                light_portrait.attrib.get("stroke"), light_portrait.attrib["fill"]
            )
            self.assertGreaterEqual(
                float(light_portrait.attrib.get("stroke-width", "0")), 0.3
            )
            self.assertEqual(
                light_portrait.attrib["transform"], dark_portrait.attrib["transform"]
            )

    def test_repository_does_not_publish_the_source_photo(self):
        published_images = [
            path
            for path in ROOT.rglob("*")
            if path.is_file()
            and path.suffix.lower()
            in {".jpg", ".jpeg", ".png", ".webp", ".heic", ".avif", ".tif", ".tiff", ".gif", ".bmp"}
        ]

        self.assertEqual(published_images, [])


if __name__ == "__main__":
    unittest.main()
