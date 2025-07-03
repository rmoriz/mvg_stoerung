#!/usr/bin/env python3
"""
MVG API Parser - Filters incidents from MVG disruption messages
Fetches data from https://www.mvg.de/api/bgw-pt/v3/messages and returns only INCIDENT type elements
"""

import requests
import json
import sys
import re
from datetime import datetime
from typing import List, Dict, Any


def fetch_mvg_messages() -> Dict[str, Any]:
    """
    Fetch messages from MVG API

    Returns:
        Dict containing the API response

    Raises:
        requests.RequestException: If API request fails
    """
    url = "https://www.mvg.de/api/bgw-pt/v3/messages"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from MVG API: {e}", file=sys.stderr)
        raise
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}", file=sys.stderr)
        raise


def html_to_text(html_content: str) -> str:
    """
    Convert HTML content to terminal-friendly text

    Args:
        html_content: String containing HTML content

    Returns:
        Plain text with HTML tags converted to terminal equivalents
    """
    if not html_content or not isinstance(html_content, str):
        return html_content

    text = html_content

    # Convert common HTML tags to terminal equivalents
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p\s*[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<div\s*[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)

    # Convert line breaks and paragraphs
    text = re.sub(r"<hr\s*/?>", "\n" + "-" * 50 + "\n", text, flags=re.IGNORECASE)

    # Convert lists
    text = re.sub(r"<ul\s*[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</ul>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<ol\s*[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</ol>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li\s*[^>]*>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)

    # Convert emphasis tags
    text = re.sub(r"<strong\s*[^>]*>(.*?)</strong>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<b\s*[^>]*>(.*?)</b>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<em\s*[^>]*>(.*?)</em>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<i\s*[^>]*>(.*?)</i>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)

    # Convert links (keep the text, optionally show URL)
    text = re.sub(r'<a\s+[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r"\2 (\1)", text, flags=re.IGNORECASE | re.DOTALL)

    # Remove any remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Clean up whitespace
    text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)  # Replace multiple newlines with double newline
    text = re.sub(r"^\s+|\s+$", "", text)  # Strip leading/trailing whitespace

    # Decode common HTML entities
    html_entities = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&apos;": "'",
        "&nbsp;": " ",
        "&hellip;": "...",
        "&mdash;": "-",
        "&ndash;": "-",
        "&copy;": "(c)",
        "&reg;": "(R)",
        "&trade;": "(TM)",
    }

    for entity, replacement in html_entities.items():
        text = text.replace(entity, replacement)

    return text


def format_timestamp(timestamp: int) -> str:
    """
    Convert Unix timestamp (milliseconds) to German datetime format

    Args:
        timestamp: Unix timestamp in milliseconds

    Returns:
        Formatted datetime string in German format
    """
    try:
        # Convert milliseconds to seconds
        dt = datetime.fromtimestamp(timestamp / 1000)
        # German datetime format: DD.MM.YYYY HH:MM
        return dt.strftime("%d.%m.%Y %H:%M")
    except (ValueError, OSError):
        return str(timestamp)


def deduplicate_lines(incident: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove duplicate entries from the lines array

    Args:
        incident: Dictionary containing incident data

    Returns:
        Dictionary with deduplicated lines
    """
    # Create a copy to avoid modifying the original
    converted = incident.copy()

    if "lines" in converted and isinstance(converted["lines"], list):
        seen = set()
        unique_lines = []

        for line in converted["lines"]:
            if isinstance(line, dict):
                # Create a tuple of the line data for comparison
                line_key = tuple(sorted(line.items()))
                if line_key not in seen:
                    seen.add(line_key)
                    unique_lines.append(line)
            else:
                # For non-dict items, just check direct equality
                if line not in unique_lines:
                    unique_lines.append(line)

        converted["lines"] = unique_lines

    return converted


def add_human_readable_dates(incident: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add human-readable datetime fields to incident data

    Args:
        incident: Dictionary containing incident data

    Returns:
        Dictionary with additional human-readable datetime fields
    """
    # Create a copy to avoid modifying the original
    converted = incident.copy()

    # Convert publication timestamp
    if "publication" in converted and isinstance(converted["publication"], int):
        converted["publication_readable"] = format_timestamp(converted["publication"])

    # Convert validFrom and validTo timestamps
    if "validFrom" in converted and isinstance(converted["validFrom"], int):
        converted["validFrom_readable"] = format_timestamp(converted["validFrom"])

    if "validTo" in converted and isinstance(converted["validTo"], int):
        converted["validTo_readable"] = format_timestamp(converted["validTo"])

    # Convert publicationDuration timestamps
    if "publicationDuration" in converted and isinstance(converted["publicationDuration"], dict):
        duration = converted["publicationDuration"].copy()
        if "from" in duration and isinstance(duration["from"], int):
            duration["from_readable"] = format_timestamp(duration["from"])
        if "to" in duration and isinstance(duration["to"], int):
            duration["to_readable"] = format_timestamp(duration["to"])
        converted["publicationDuration"] = duration

    # Convert incidentDurations timestamps
    if "incidentDurations" in converted and isinstance(converted["incidentDurations"], list):
        converted_durations = []
        for duration in converted["incidentDurations"]:
            if isinstance(duration, dict):
                new_duration = duration.copy()
                if "from" in new_duration and isinstance(new_duration["from"], int):
                    new_duration["from_readable"] = format_timestamp(new_duration["from"])
                if "to" in new_duration and isinstance(new_duration["to"], int):
                    new_duration["to_readable"] = format_timestamp(new_duration["to"])
                converted_durations.append(new_duration)
            else:
                converted_durations.append(duration)
        converted["incidentDurations"] = converted_durations

    return converted


def convert_html_fields(incident: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert HTML content in incident fields to terminal-friendly text

    Args:
        incident: Dictionary containing incident data

    Returns:
        Dictionary with HTML converted to text in _readable fields
    """
    # Create a copy to avoid modifying the original
    converted = incident.copy()

    # Convert description field if it exists - keep original and add readable version
    if "description" in converted and isinstance(converted["description"], str):
        converted["description_readable"] = html_to_text(converted["description"])
        # Keep the original description as-is

    # Convert title field if it exists and contains HTML - keep original and add readable version
    if "title" in converted and isinstance(converted["title"], str):
        converted["title_readable"] = html_to_text(converted["title"])
        # Keep the original title as-is

    return converted


def filter_incidents(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filter messages to return only INCIDENT type elements

    Args:
        data: The full API response data

    Returns:
        List of incident messages with HTML converted to text
    """
    incidents = []

    # Handle different possible data structures
    messages = []
    if isinstance(data, list):
        messages = data
    elif isinstance(data, dict):
        # Try common keys where messages might be stored
        for key in ["messages", "data", "items", "results"]:
            if key in data and isinstance(data[key], list):
                messages = data[key]
                break
        else:
            # If no common key found, check if the dict itself contains type field
            if "type" in data:
                messages = [data]

    # Filter for INCIDENT type and convert HTML and timestamps
    for message in messages:
        if isinstance(message, dict) and message.get("type") == "INCIDENT":
            # Convert HTML fields first
            converted_incident = convert_html_fields(message)
            # Then add human-readable dates
            converted_incident = add_human_readable_dates(converted_incident)
            # Finally deduplicate lines
            converted_incident = deduplicate_lines(converted_incident)
            incidents.append(converted_incident)

    return incidents


def main():
    """Main function to fetch and filter MVG incidents"""
    try:
        # Fetch data from API
        print("Fetching data from MVG API...", file=sys.stderr)
        data = fetch_mvg_messages()

        # Filter for incidents and convert HTML
        incidents = filter_incidents(data)

        # Output results as JSON
        print(json.dumps(incidents, indent=2, ensure_ascii=False))

        # Print summary to stderr
        print(f"Found {len(incidents)} incident(s)", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
