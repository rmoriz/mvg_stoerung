#!/usr/bin/env python3
"""
Integration tests for MVG Incident Parser
Tests the full API workflow including real API calls and end-to-end functionality
"""

import unittest
import json
import sys
import io
from unittest.mock import patch, Mock
import requests
from mvg_stoerung import (
    fetch_mvg_messages,
    filter_incidents,
    main
)


class TestMVGAPIIntegration(unittest.TestCase):
    """Test integration with the real MVG API"""
    
    def test_real_api_call(self):
        """Test actual API call to MVG (with timeout for CI)"""
        try:
            data = fetch_mvg_messages()
            
            # Basic structure validation
            self.assertIsInstance(data, (dict, list))
            
            # If it's a dict, it should have some expected structure
            if isinstance(data, dict):
                # Common keys that might exist in API response
                possible_keys = ['messages', 'data', 'items', 'results']
                has_expected_structure = any(key in data for key in possible_keys)
                
                # If none of the common keys exist, check if it's a single message
                if not has_expected_structure:
                    has_expected_structure = 'type' in data
                
                self.assertTrue(has_expected_structure, 
                              f"API response doesn't have expected structure: {list(data.keys())}")
            
            print(f"✅ Real API call successful, received {type(data).__name__}")
            
        except requests.RequestException as e:
            self.skipTest(f"API call failed (expected in CI): {e}")
        except Exception as e:
            self.fail(f"Unexpected error during API call: {e}")
    
    def test_api_timeout_handling(self):
        """Test API timeout handling"""
        with patch('mvg_stoerung.requests.get') as mock_get:
            mock_get.side_effect = requests.Timeout("Connection timeout")
            
            with self.assertRaises(requests.Timeout):
                fetch_mvg_messages()
    
    def test_api_http_error_handling(self):
        """Test HTTP error handling"""
        with patch('mvg_stoerung.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            with self.assertRaises(requests.HTTPError):
                fetch_mvg_messages()
    
    def test_api_json_decode_error(self):
        """Test JSON decode error handling"""
        with patch('mvg_stoerung.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_get.return_value = mock_response
            
            with self.assertRaises(json.JSONDecodeError):
                fetch_mvg_messages()


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete end-to-end workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.sample_api_response = {
            "messages": [
                {
                    "title": "Test <strong>Incident</strong>",
                    "description": "Line 1<br>Line 2<br>Line 3",
                    "type": "INCIDENT",
                    "publication": 1704110445000,
                    "validFrom": 1704110445000,
                    "validTo": 1704117645000,
                    "publicationDuration": {
                        "from": 1704110445000,
                        "to": 1704117645000
                    },
                    "incidentDurations": [
                        {
                            "from": 1704110445000,
                            "to": 1704117645000
                        }
                    ],
                    "lines": [
                        {"label": "51", "transportType": "BUS", "network": "swm"},
                        {"label": "51", "transportType": "BUS", "network": "swm"},  # duplicate
                        {"label": "151", "transportType": "TRAM", "network": "swm"}
                    ],
                    "provider": "MVG"
                },
                {
                    "title": "Non-incident message",
                    "description": "This should be filtered out",
                    "type": "INFO",
                    "provider": "MVG"
                }
            ]
        }
    
    def test_complete_workflow_with_mock_data(self):
        """Test complete workflow from API call to final output"""
        with patch('mvg_stoerung.fetch_mvg_messages') as mock_fetch:
            mock_fetch.return_value = self.sample_api_response
            
            # Test the filtering and processing
            incidents = filter_incidents(self.sample_api_response)
            
            # Should have only 1 incident (INFO type filtered out)
            self.assertEqual(len(incidents), 1)
            
            incident = incidents[0]
            
            # Check HTML conversion
            self.assertEqual(incident['title'], "Test <strong>Incident</strong>")
            self.assertEqual(incident['title_readable'], "Test **Incident**")
            self.assertEqual(incident['description'], "Line 1<br>Line 2<br>Line 3")
            self.assertEqual(incident['description_readable'], "Line 1\nLine 2\nLine 3")
            
            # Check timestamp conversion
            self.assertIn('publication_readable', incident)
            self.assertIn('validFrom_readable', incident)
            self.assertIn('validTo_readable', incident)
            self.assertIn('from_readable', incident['publicationDuration'])
            self.assertIn('to_readable', incident['publicationDuration'])
            self.assertIn('from_readable', incident['incidentDurations'][0])
            self.assertIn('to_readable', incident['incidentDurations'][0])
            
            # Check deduplication
            self.assertEqual(len(incident['lines']), 2)  # Duplicate removed
            
            # Verify timestamp format (German)
            self.assertRegex(incident['publication_readable'], r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}')
    
    def test_main_function_with_mock(self):
        """Test the main function with mocked API response"""
        with patch('mvg_stoerung.fetch_mvg_messages') as mock_fetch:
            mock_fetch.return_value = self.sample_api_response
            
            # Capture stdout and stderr
            captured_stdout = io.StringIO()
            captured_stderr = io.StringIO()
            
            with patch('sys.stdout', captured_stdout), patch('sys.stderr', captured_stderr):
                try:
                    main()
                except SystemExit:
                    pass  # main() might call sys.exit(1) on error
            
            # Check stderr for status messages
            stderr_content = captured_stderr.getvalue()
            self.assertIn("Fetching data from MVG API", stderr_content)
            self.assertIn("Found 1 incident(s)", stderr_content)
            
            # Check stdout for JSON output
            stdout_content = captured_stdout.getvalue()
            self.assertTrue(stdout_content.strip())  # Should have content
            
            # Validate JSON structure
            try:
                json_data = json.loads(stdout_content)
                self.assertIsInstance(json_data, list)
                self.assertEqual(len(json_data), 1)
                
                incident = json_data[0]
                self.assertEqual(incident['type'], 'INCIDENT')
                self.assertIn('title_readable', incident)
                self.assertIn('description_readable', incident)
                self.assertIn('publication_readable', incident)
                
            except json.JSONDecodeError as e:
                self.fail(f"Invalid JSON output: {e}\nOutput: {stdout_content}")


class TestErrorScenarios(unittest.TestCase):
    """Test various error scenarios in the integration workflow"""
    
    def test_network_error_handling(self):
        """Test network connectivity issues"""
        with patch('mvg_stoerung.fetch_mvg_messages') as mock_fetch:
            mock_fetch.side_effect = requests.ConnectionError("Network unreachable")
            
            captured_stderr = io.StringIO()
            
            with patch('sys.stderr', captured_stderr):
                with self.assertRaises(SystemExit):
                    main()
            
            stderr_content = captured_stderr.getvalue()
            self.assertIn("Error:", stderr_content)
    
    def test_empty_api_response(self):
        """Test handling of empty API response"""
        with patch('mvg_stoerung.fetch_mvg_messages') as mock_fetch:
            mock_fetch.return_value = {"messages": []}
            
            captured_stdout = io.StringIO()
            captured_stderr = io.StringIO()
            
            with patch('sys.stdout', captured_stdout), patch('sys.stderr', captured_stderr):
                main()
            
            # Should handle empty response gracefully
            stderr_content = captured_stderr.getvalue()
            self.assertIn("Found 0 incident(s)", stderr_content)
            
            stdout_content = captured_stdout.getvalue()
            json_data = json.loads(stdout_content)
            self.assertEqual(json_data, [])
    
    def test_malformed_api_response(self):
        """Test handling of malformed API response"""
        with patch('mvg_stoerung.fetch_mvg_messages') as mock_fetch:
            # Return unexpected structure
            mock_fetch.return_value = {"unexpected": "structure"}
            
            captured_stdout = io.StringIO()
            captured_stderr = io.StringIO()
            
            with patch('sys.stdout', captured_stdout), patch('sys.stderr', captured_stderr):
                main()
            
            # Should handle gracefully and return empty list
            stdout_content = captured_stdout.getvalue()
            json_data = json.loads(stdout_content)
            self.assertEqual(json_data, [])
    
    def test_partial_data_corruption(self):
        """Test handling of partially corrupted incident data"""
        corrupted_response = {
            "messages": [
                {
                    "title": "Valid Incident",
                    "type": "INCIDENT",
                    # Missing description
                    "lines": [
                        {"label": "51"},  # Missing some fields
                        "invalid_line_format",  # Wrong format
                        {"label": "151", "transportType": "BUS"}
                    ]
                },
                {
                    # Missing title
                    "description": "Another incident",
                    "type": "INCIDENT"
                }
            ]
        }
        
        with patch('mvg_stoerung.fetch_mvg_messages') as mock_fetch:
            mock_fetch.return_value = corrupted_response
            
            captured_stdout = io.StringIO()
            
            with patch('sys.stdout', captured_stdout):
                main()
            
            # Should process what it can
            stdout_content = captured_stdout.getvalue()
            json_data = json.loads(stdout_content)
            self.assertEqual(len(json_data), 2)  # Both incidents processed


class TestDataValidation(unittest.TestCase):
    """Test data validation and edge cases"""
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters in API response"""
        unicode_response = {
            "messages": [
                {
                    "title": "Störung mit Umlauten: äöüß",
                    "description": "Züge fahren nicht.<br>Entschuldigung für die Unannehmlichkeiten.",
                    "type": "INCIDENT",
                    "provider": "MVG"
                }
            ]
        }
        
        with patch('mvg_stoerung.fetch_mvg_messages') as mock_fetch:
            mock_fetch.return_value = unicode_response
            
            captured_stdout = io.StringIO()
            
            with patch('sys.stdout', captured_stdout):
                main()
            
            stdout_content = captured_stdout.getvalue()
            json_data = json.loads(stdout_content)
            
            incident = json_data[0]
            self.assertIn("äöüß", incident['title'])
            self.assertIn("Züge fahren nicht.\nEntschuldigung", incident['description_readable'])
    
    def test_large_dataset_handling(self):
        """Test handling of large number of incidents"""
        large_response = {
            "messages": [
                {
                    "title": f"Incident {i}",
                    "description": f"Description {i}<br>Line 2",
                    "type": "INCIDENT",
                    "lines": [
                        {"label": f"{i}", "transportType": "BUS"},
                        {"label": f"{i}", "transportType": "BUS"}  # duplicate
                    ]
                }
                for i in range(100)  # 100 incidents
            ]
        }
        
        with patch('mvg_stoerung.fetch_mvg_messages') as mock_fetch:
            mock_fetch.return_value = large_response
            
            captured_stdout = io.StringIO()
            captured_stderr = io.StringIO()
            
            with patch('sys.stdout', captured_stdout), patch('sys.stderr', captured_stderr):
                main()
            
            stderr_content = captured_stderr.getvalue()
            self.assertIn("Found 100 incident(s)", stderr_content)
            
            stdout_content = captured_stdout.getvalue()
            json_data = json.loads(stdout_content)
            self.assertEqual(len(json_data), 100)
            
            # Check that deduplication worked for all incidents
            for incident in json_data:
                self.assertEqual(len(incident['lines']), 1)  # Duplicates removed
    
    def test_extreme_timestamp_values(self):
        """Test handling of extreme timestamp values"""
        extreme_response = {
            "messages": [
                {
                    "title": "Future Incident",
                    "type": "INCIDENT",
                    "publication": 9999999999999,  # Far future
                    "validFrom": 0,  # Unix epoch
                    "validTo": -1  # Invalid negative timestamp
                }
            ]
        }
        
        with patch('mvg_stoerung.fetch_mvg_messages') as mock_fetch:
            mock_fetch.return_value = extreme_response
            
            captured_stdout = io.StringIO()
            
            with patch('sys.stdout', captured_stdout):
                main()
            
            stdout_content = captured_stdout.getvalue()
            json_data = json.loads(stdout_content)
            
            incident = json_data[0]
            # Should handle extreme values gracefully
            self.assertIn('publication_readable', incident)
            self.assertIn('validFrom_readable', incident)
            self.assertIn('validTo_readable', incident)


class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def test_processing_time(self):
        """Test that processing completes in reasonable time"""
        import time
        
        # Create a moderately large dataset
        large_response = {
            "messages": [
                {
                    "title": f"Incident {i}",
                    "description": "Long description with <strong>HTML</strong><br>" * 10,
                    "type": "INCIDENT",
                    "publication": 1704110445000 + i,
                    "lines": [{"label": f"{j}", "transportType": "BUS"} for j in range(10)]
                }
                for i in range(50)
            ]
        }
        
        with patch('mvg_stoerung.fetch_mvg_messages') as mock_fetch:
            mock_fetch.return_value = large_response
            
            start_time = time.time()
            
            captured_stdout = io.StringIO()
            with patch('sys.stdout', captured_stdout):
                main()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should complete within reasonable time (adjust threshold as needed)
            self.assertLess(processing_time, 5.0, 
                          f"Processing took too long: {processing_time:.2f} seconds")
            
            # Verify output is correct
            stdout_content = captured_stdout.getvalue()
            json_data = json.loads(stdout_content)
            self.assertEqual(len(json_data), 50)


if __name__ == "__main__":
    # Run integration tests with more verbose output
    unittest.main(verbosity=2, buffer=True)