#!/usr/bin/env python3
"""
Comprehensive error scenario tests for MVG Incident Parser
Tests various failure modes, edge cases, and error handling
"""

import io
import json
import socket
import ssl
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

import requests

from mvg_stoerung import fetch_mvg_messages, filter_incidents, format_timestamp, html_to_text, main


class TestNetworkFailures(unittest.TestCase):
    """Test various network failure scenarios"""

    def test_connection_timeout(self):
        """Test connection timeout handling"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_get.side_effect = requests.Timeout("Connection timed out")

            with self.assertRaises(requests.Timeout):
                fetch_mvg_messages()

    def test_read_timeout(self):
        """Test read timeout handling"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_get.side_effect = requests.ReadTimeout("Read timed out")

            with self.assertRaises(requests.ReadTimeout):
                fetch_mvg_messages()

    def test_connection_error(self):
        """Test connection error handling"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_get.side_effect = requests.ConnectionError("Failed to establish connection")

            with self.assertRaises(requests.ConnectionError):
                fetch_mvg_messages()

    def test_dns_resolution_failure(self):
        """Test DNS resolution failure"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_get.side_effect = socket.gaierror("Name or service not known")

            with self.assertRaises(socket.gaierror):
                fetch_mvg_messages()

    def test_ssl_certificate_error(self):
        """Test SSL certificate verification failure"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.SSLError("SSL certificate verification failed")

            with self.assertRaises(requests.exceptions.SSLError):
                fetch_mvg_messages()

    def test_too_many_redirects(self):
        """Test too many redirects error"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_get.side_effect = requests.TooManyRedirects("Exceeded 30 redirects")

            with self.assertRaises(requests.TooManyRedirects):
                fetch_mvg_messages()

    def test_proxy_error(self):
        """Test proxy connection error"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ProxyError("Cannot connect to proxy")

            with self.assertRaises(requests.exceptions.ProxyError):
                fetch_mvg_messages()


class TestHTTPErrors(unittest.TestCase):
    """Test HTTP error responses"""

    def test_404_not_found(self):
        """Test 404 Not Found response"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Client Error: Not Found")
            mock_get.return_value = mock_response

            with self.assertRaises(requests.HTTPError):
                fetch_mvg_messages()

    def test_500_internal_server_error(self):
        """Test 500 Internal Server Error"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error: Internal Server Error")
            mock_get.return_value = mock_response

            with self.assertRaises(requests.HTTPError):
                fetch_mvg_messages()

    def test_503_service_unavailable(self):
        """Test 503 Service Unavailable"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("503 Server Error: Service Unavailable")
            mock_get.return_value = mock_response

            with self.assertRaises(requests.HTTPError):
                fetch_mvg_messages()

    def test_429_rate_limit_exceeded(self):
        """Test 429 Too Many Requests"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("429 Client Error: Too Many Requests")
            mock_get.return_value = mock_response

            with self.assertRaises(requests.HTTPError):
                fetch_mvg_messages()

    def test_403_forbidden(self):
        """Test 403 Forbidden response"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("403 Client Error: Forbidden")
            mock_get.return_value = mock_response

            with self.assertRaises(requests.HTTPError):
                fetch_mvg_messages()


class TestMalformedAPIResponses(unittest.TestCase):
    """Test various malformed API response scenarios"""

    def test_invalid_json_syntax(self):
        """Test invalid JSON syntax"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.side_effect = json.JSONDecodeError("Expecting ',' delimiter", "", 10)
            mock_get.return_value = mock_response

            with self.assertRaises(json.JSONDecodeError):
                fetch_mvg_messages()

    def test_truncated_json(self):
        """Test truncated JSON response"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.side_effect = json.JSONDecodeError("Unterminated string", "", 50)
            mock_get.return_value = mock_response

            with self.assertRaises(json.JSONDecodeError):
                fetch_mvg_messages()

    def test_empty_response_body(self):
        """Test empty response body"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
            mock_get.return_value = mock_response

            with self.assertRaises(json.JSONDecodeError):
                fetch_mvg_messages()

    def test_non_json_content_type(self):
        """Test non-JSON content type response"""
        with patch("mvg_stoerung.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
            mock_response.headers = {"content-type": "text/html"}
            mock_get.return_value = mock_response

            with self.assertRaises(json.JSONDecodeError):
                fetch_mvg_messages()

    def test_null_response(self):
        """Test null JSON response"""
        with patch("mvg_stoerung.fetch_mvg_messages") as mock_fetch:
            mock_fetch.return_value = None

            incidents = filter_incidents(None)
            self.assertEqual(incidents, [])

    def test_unexpected_data_types(self):
        """Test unexpected data types in response"""
        malformed_responses = [
            "string_instead_of_object",
            123,
            True,
            [],  # Empty list
            {"messages": "should_be_list"},
            {"messages": [123, "invalid", True]},  # Invalid message types
        ]

        for response in malformed_responses:
            with self.subTest(response=response):
                incidents = filter_incidents(response)
                # Should handle gracefully and return empty list
                self.assertIsInstance(incidents, list)

    def test_missing_required_fields(self):
        """Test incidents with missing required fields"""
        malformed_incidents = {
            "messages": [
                {},  # Completely empty
                {"type": "INCIDENT"},  # Missing title and description
                {"title": "Test", "type": "INCIDENT"},  # Missing description
                {"description": "Test", "type": "INCIDENT"},  # Missing title
                {"title": "Test", "description": "Test"},  # Missing type
                {"title": None, "description": None, "type": "INCIDENT"},  # Null values
            ]
        }

        incidents = filter_incidents(malformed_incidents)
        # Should process what it can
        self.assertEqual(len(incidents), 4)  # Only INCIDENT types

    def test_corrupted_nested_structures(self):
        """Test corrupted nested data structures"""
        corrupted_response = {
            "messages": [
                {
                    "title": "Test Incident",
                    "type": "INCIDENT",
                    "lines": "should_be_list",  # Wrong type
                    "publicationDuration": "should_be_dict",  # Wrong type
                    "incidentDurations": {"should": "be_list"},  # Wrong type
                    "publication": "not_a_number",  # Wrong type
                }
            ]
        }

        incidents = filter_incidents(corrupted_response)
        self.assertEqual(len(incidents), 1)

        incident = incidents[0]
        # Should handle corrupted fields gracefully
        self.assertEqual(incident["title"], "Test Incident")
        self.assertEqual(incident["type"], "INCIDENT")


class TestDataCorruption(unittest.TestCase):
    """Test handling of corrupted data"""

    def test_unicode_corruption(self):
        """Test handling of corrupted Unicode characters"""
        corrupted_text = "Störung mit \udcff\udcfe ungültigen Zeichen"

        # Should not crash on corrupted Unicode
        result = html_to_text(corrupted_text)
        self.assertIsInstance(result, str)

    def test_extremely_long_strings(self):
        """Test handling of extremely long strings"""
        long_string = "A" * 1000000  # 1MB string

        # Should handle large strings without crashing
        result = html_to_text(long_string)
        self.assertEqual(result, long_string)

    def test_deeply_nested_html(self):
        """Test deeply nested HTML structures"""
        nested_html = "<div>" * 1000 + "Content" + "</div>" * 1000

        # Should handle deep nesting
        result = html_to_text(nested_html)
        self.assertIn("Content", result)

    def test_malicious_html_patterns(self):
        """Test potentially malicious HTML patterns"""
        malicious_patterns = [
            ("<script>alert('xss')</script>", "alert('xss')"),
            ("<!--[if IE]><script>alert('ie')</script><![endif]-->", "alert('ie')"),
            ("<img src=x onerror=alert('img')>", ""),
            ("<svg onload=alert('svg')>", ""),
            ("<iframe src='javascript:alert(1)'></iframe>", ""),
        ]

        for pattern, expected_content in malicious_patterns:
            with self.subTest(pattern=pattern):
                result = html_to_text(pattern)
                # Should strip HTML tags but may preserve content
                self.assertNotIn("<script>", result)
                self.assertNotIn("<img", result)
                self.assertNotIn("<svg", result)
                self.assertNotIn("<iframe", result)
                # Content may remain after tag removal
                if expected_content:
                    self.assertIn(expected_content, result)

    def test_circular_references(self):
        """Test handling of circular references in data"""
        # Create circular reference
        circular_data = {"messages": []}
        circular_incident = {"title": "Circular Test", "type": "INCIDENT", "self_ref": None}
        circular_incident["self_ref"] = circular_incident
        circular_data["messages"].append(circular_incident)

        # Should handle without infinite recursion
        incidents = filter_incidents(circular_data)
        self.assertEqual(len(incidents), 1)


class TestMemoryAndPerformance(unittest.TestCase):
    """Test memory usage and performance under stress"""

    def test_memory_leak_prevention(self):
        """Test that repeated processing doesn't cause memory leaks"""
        import gc

        test_data = {
            "messages": [
                {
                    "title": f"Incident {i}",
                    "description": "Test description<br>Line 2" * 100,
                    "type": "INCIDENT",
                    "lines": [{"label": f"{j}"} for j in range(50)],
                }
                for i in range(100)
            ]
        }

        # Process multiple times
        for _ in range(10):
            incidents = filter_incidents(test_data)
            self.assertEqual(len(incidents), 100)

            # Force garbage collection
            gc.collect()

        # Should complete without memory issues
        self.assertTrue(True)

    def test_large_timestamp_arrays(self):
        """Test handling of large timestamp arrays"""
        large_durations = [{"from": 1704110445000 + i * 1000, "to": 1704110445000 + (i + 1) * 1000} for i in range(1000)]

        incident = {"title": "Large Duration Test", "type": "INCIDENT", "incidentDurations": large_durations}

        incidents = filter_incidents({"messages": [incident]})
        processed_incident = incidents[0]

        # Should process all durations
        self.assertEqual(len(processed_incident["incidentDurations"]), 1000)

        # All should have readable timestamps
        for duration in processed_incident["incidentDurations"]:
            self.assertIn("from_readable", duration)
            self.assertIn("to_readable", duration)


class TestMainFunctionErrorHandling(unittest.TestCase):
    """Test error handling in the main function"""

    def test_main_with_network_error(self):
        """Test main function with network error"""
        with patch("mvg_stoerung.fetch_mvg_messages") as mock_fetch:
            mock_fetch.side_effect = requests.ConnectionError("Network error")

            captured_stderr = io.StringIO()

            with patch("sys.stderr", captured_stderr):
                with self.assertRaises(SystemExit) as cm:
                    main()

                self.assertEqual(cm.exception.code, 1)

            stderr_content = captured_stderr.getvalue()
            self.assertIn("Error:", stderr_content)

    def test_main_with_json_error(self):
        """Test main function with JSON decode error"""
        with patch("mvg_stoerung.fetch_mvg_messages") as mock_fetch:
            mock_fetch.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

            captured_stderr = io.StringIO()

            with patch("sys.stderr", captured_stderr):
                with self.assertRaises(SystemExit) as cm:
                    main()

                self.assertEqual(cm.exception.code, 1)

            stderr_content = captured_stderr.getvalue()
            self.assertIn("Error:", stderr_content)

    def test_main_with_unexpected_exception(self):
        """Test main function with unexpected exception"""
        with patch("mvg_stoerung.fetch_mvg_messages") as mock_fetch:
            mock_fetch.side_effect = ValueError("Unexpected error")

            captured_stderr = io.StringIO()

            with patch("sys.stderr", captured_stderr):
                with self.assertRaises(SystemExit) as cm:
                    main()

                self.assertEqual(cm.exception.code, 1)

            stderr_content = captured_stderr.getvalue()
            self.assertIn("Error:", stderr_content)


class TestEdgeCaseTimestamps(unittest.TestCase):
    """Test edge cases in timestamp handling"""

    def test_negative_timestamps(self):
        """Test negative timestamp values"""
        negative_timestamps = [-1, -1000000, -9999999999999]

        for timestamp in negative_timestamps:
            with self.subTest(timestamp=timestamp):
                result = format_timestamp(timestamp)
                # Negative timestamps are processed as valid dates before Unix epoch
                # Should return a formatted date string
                self.assertIsInstance(result, str)
                self.assertRegex(result, r"\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}")

    def test_zero_and_epoch_timestamps(self):
        """Test zero and epoch timestamps"""
        result_zero = format_timestamp(0)
        self.assertRegex(result_zero, r"\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}")

        # Unix epoch (January 1, 1970)
        result_epoch = format_timestamp(1000)  # 1 second after epoch
        self.assertRegex(result_epoch, r"\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}")

    def test_far_future_timestamps(self):
        """Test far future timestamp values"""
        far_future = 9999999999999  # Year 2286
        result = format_timestamp(far_future)
        # Should handle or return string representation
        self.assertIsInstance(result, str)

    def test_non_numeric_timestamps(self):
        """Test non-numeric timestamp values"""
        invalid_timestamps = ["not_a_number", None, [], {}, True]

        for timestamp in invalid_timestamps:
            with self.subTest(timestamp=timestamp):
                try:
                    result = format_timestamp(timestamp)
                    # Should handle gracefully
                    self.assertIsInstance(result, str)
                except (TypeError, ValueError):
                    # Acceptable to raise these exceptions
                    pass


if __name__ == "__main__":
    # Run error scenario tests with detailed output
    unittest.main(verbosity=2, buffer=True)
