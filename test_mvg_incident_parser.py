#!/usr/bin/env python3
"""
Unit tests for MVG Incident Parser
Tests HTML conversion, deduplication, and datetime formatting functions
"""

import unittest
from datetime import datetime

from mvg_stoerung import add_human_readable_dates, convert_html_fields, deduplicate_lines, format_timestamp, html_to_text


class TestHtmlToText(unittest.TestCase):
    """Test HTML to text conversion functionality"""

    def test_basic_br_conversion(self):
        """Test basic <br> tag conversion"""
        html = "Line 1<br>Line 2<br/>Line 3"
        expected = "Line 1\nLine 2\nLine 3"
        self.assertEqual(html_to_text(html), expected)

    def test_paragraph_conversion(self):
        """Test paragraph tag conversion"""
        html = "<p>Paragraph 1</p><p>Paragraph 2</p>"
        expected = "\nParagraph 1\n\nParagraph 2\n"
        result = html_to_text(html)
        # Clean up multiple newlines for comparison
        result = result.strip()
        expected = expected.strip()
        self.assertEqual(result, expected)

    def test_list_conversion(self):
        """Test list tag conversion"""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        expected = "- Item 1\n- Item 2"
        result = html_to_text(html).strip()
        self.assertEqual(result, expected)

    def test_emphasis_conversion(self):
        """Test bold and italic tag conversion"""
        html = "<strong>Bold text</strong> and <em>italic text</em>"
        expected = "**Bold text** and *italic text*"
        self.assertEqual(html_to_text(html), expected)

    def test_link_conversion(self):
        """Test link tag conversion"""
        html = '<a href="https://example.com">Link text</a>'
        expected = "Link text (https://example.com)"
        self.assertEqual(html_to_text(html), expected)

    def test_html_entities(self):
        """Test HTML entity conversion"""
        html = "Text with &amp; &lt; &gt; &quot; entities"
        expected = 'Text with & < > " entities'
        self.assertEqual(html_to_text(html), expected)

    def test_complex_html(self):
        """Test complex HTML with multiple tags"""
        html = "Dear passengers,<br><strong>Important:</strong> delays due to <em>heavy traffic</em>.<br>More info at <a href='https://mvg.de'>MVG website</a>."
        result = html_to_text(html)
        self.assertIn("Dear passengers,\n", result)
        self.assertIn("**Important:**", result)
        self.assertIn("*heavy traffic*", result)
        self.assertIn("MVG website (https://mvg.de)", result)

    def test_empty_and_none_input(self):
        """Test edge cases with empty or None input"""
        self.assertEqual(html_to_text(""), "")
        self.assertEqual(html_to_text(None), None)
        self.assertEqual(html_to_text(123), 123)  # Non-string input

    def test_mvg_real_example(self):
        """Test with real MVG HTML example"""
        html = "Liebe Fahrgäste,<br>wegen starken Verkehrsaufkommens kommt es derzeit zu Verspätungen.<br>Ihre MVG"
        expected = "Liebe Fahrgäste,\nwegen starken Verkehrsaufkommens kommt es derzeit zu Verspätungen.\nIhre MVG"
        self.assertEqual(html_to_text(html), expected)


class TestConvertHtmlFields(unittest.TestCase):
    """Test HTML field conversion in incident data"""

    def test_description_conversion(self):
        """Test description field HTML conversion"""
        incident = {"title": "Test Incident", "description": "Line 1<br>Line 2", "type": "INCIDENT"}
        result = convert_html_fields(incident)

        # Original should be preserved
        self.assertEqual(result["description"], "Line 1<br>Line 2")
        # Readable version should be added
        self.assertEqual(result["description_readable"], "Line 1\nLine 2")

    def test_title_conversion(self):
        """Test title field HTML conversion"""
        incident = {"title": "Test <strong>Bold</strong> Title", "description": "Description", "type": "INCIDENT"}
        result = convert_html_fields(incident)

        # Original should be preserved
        self.assertEqual(result["title"], "Test <strong>Bold</strong> Title")
        # Readable version should be added
        self.assertEqual(result["title_readable"], "Test **Bold** Title")

    def test_no_html_fields(self):
        """Test incident without HTML fields"""
        incident = {"title": "Plain Title", "description": "Plain description", "type": "INCIDENT"}
        result = convert_html_fields(incident)

        # Should still add readable versions
        self.assertEqual(result["title_readable"], "Plain Title")
        self.assertEqual(result["description_readable"], "Plain description")

    def test_missing_fields(self):
        """Test incident with missing title or description"""
        incident = {"type": "INCIDENT"}
        result = convert_html_fields(incident)

        # Should not crash and should not add readable fields
        self.assertNotIn("title_readable", result)
        self.assertNotIn("description_readable", result)


class TestDeduplicateLines(unittest.TestCase):
    """Test line deduplication functionality"""

    def test_duplicate_removal(self):
        """Test removal of duplicate line entries"""
        incident = {
            "lines": [
                {"label": "51", "transportType": "BUS", "network": "swm"},
                {"label": "51", "transportType": "BUS", "network": "swm"},  # duplicate
                {"label": "151", "transportType": "BUS", "network": "swm"},
                {"label": "151", "transportType": "BUS", "network": "swm"},  # duplicate
            ]
        }
        result = deduplicate_lines(incident)

        self.assertEqual(len(result["lines"]), 2)
        self.assertEqual(result["lines"][0]["label"], "51")
        self.assertEqual(result["lines"][1]["label"], "151")

    def test_no_duplicates(self):
        """Test with no duplicates present"""
        incident = {"lines": [{"label": "51", "transportType": "BUS"}, {"label": "151", "transportType": "TRAM"}]}
        result = deduplicate_lines(incident)

        self.assertEqual(len(result["lines"]), 2)
        self.assertEqual(result["lines"], incident["lines"])

    def test_empty_lines(self):
        """Test with empty lines array"""
        incident = {"lines": []}
        result = deduplicate_lines(incident)

        self.assertEqual(result["lines"], [])

    def test_no_lines_field(self):
        """Test incident without lines field"""
        incident = {"type": "INCIDENT"}
        result = deduplicate_lines(incident)

        # Should not crash and should not modify incident
        self.assertEqual(result, incident)

    def test_non_dict_lines(self):
        """Test with non-dictionary line entries"""
        incident = {"lines": ["line1", "line1", "line2", "line3"]}  # duplicates
        result = deduplicate_lines(incident)

        self.assertEqual(len(result["lines"]), 3)
        self.assertEqual(result["lines"], ["line1", "line2", "line3"])

    def test_mixed_line_types(self):
        """Test with mixed dictionary and non-dictionary entries"""
        incident = {
            "lines": [
                {"label": "51"},
                "string_line",
                {"label": "51"},  # duplicate dict
                "string_line",  # duplicate string
                {"label": "151"},
            ]
        }
        result = deduplicate_lines(incident)

        self.assertEqual(len(result["lines"]), 3)


class TestFormatTimestamp(unittest.TestCase):
    """Test timestamp formatting functionality"""

    def test_valid_timestamp(self):
        """Test valid timestamp conversion"""
        # January 1, 2024, 12:30:45 UTC (in milliseconds)
        timestamp = 1704110445000
        result = format_timestamp(timestamp)

        # Should be in German format DD.MM.YYYY HH:MM
        self.assertRegex(result, r"\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}")

    def test_invalid_timestamp(self):
        """Test invalid timestamp handling"""
        # Very large timestamp that would cause overflow
        invalid_timestamp = 999999999999999999
        result = format_timestamp(invalid_timestamp)

        # Should return string representation of original timestamp
        self.assertEqual(result, str(invalid_timestamp))

    def test_zero_timestamp(self):
        """Test zero timestamp"""
        result = format_timestamp(0)
        # Should be January 1, 1970 (timezone may vary)
        self.assertRegex(result, r"01\.01\.1970 \d{2}:\d{2}")  # Accept any hour


class TestAddHumanReadableDates(unittest.TestCase):
    """Test human-readable date addition functionality"""

    def test_basic_timestamp_conversion(self):
        """Test basic timestamp field conversion"""
        incident = {"publication": 1704110445000, "validFrom": 1704110445000, "validTo": 1704117645000}  # Example timestamp
        result = add_human_readable_dates(incident)

        # Original timestamps should be preserved
        self.assertEqual(result["publication"], 1704110445000)
        self.assertEqual(result["validFrom"], 1704110445000)
        self.assertEqual(result["validTo"], 1704117645000)

        # Readable versions should be added
        self.assertIn("publication_readable", result)
        self.assertIn("validFrom_readable", result)
        self.assertIn("validTo_readable", result)

        # Should be in German format
        self.assertRegex(result["publication_readable"], r"\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}")

    def test_publication_duration_conversion(self):
        """Test publicationDuration nested timestamp conversion"""
        incident = {"publicationDuration": {"from": 1704110445000, "to": 1704117645000}}
        result = add_human_readable_dates(incident)

        # Original should be preserved
        self.assertEqual(result["publicationDuration"]["from"], 1704110445000)
        self.assertEqual(result["publicationDuration"]["to"], 1704117645000)

        # Readable versions should be added
        self.assertIn("from_readable", result["publicationDuration"])
        self.assertIn("to_readable", result["publicationDuration"])

    def test_incident_durations_conversion(self):
        """Test incidentDurations array conversion"""
        incident = {
            "incidentDurations": [{"from": 1704110445000, "to": 1704117645000}, {"from": 1704124845000, "to": 1704132045000}]
        }
        result = add_human_readable_dates(incident)

        # Should have same number of durations
        self.assertEqual(len(result["incidentDurations"]), 2)

        # Each duration should have readable versions
        for duration in result["incidentDurations"]:
            self.assertIn("from_readable", duration)
            self.assertIn("to_readable", duration)

    def test_missing_timestamp_fields(self):
        """Test incident without timestamp fields"""
        incident = {"type": "INCIDENT", "title": "Test"}
        result = add_human_readable_dates(incident)

        # Should not crash and should not add readable fields
        self.assertEqual(result, incident)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
