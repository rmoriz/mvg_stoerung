# MVG Störung

This script fetches data from the MVG (Münchner Verkehrsgesellschaft) API and filters for incident-type messages.

## Usage

### Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the parser
python3 mvg_stoerung.py
```

### Docker Usage

```bash
# Pull the latest image from GitHub Container Registry
docker pull ghcr.io/rmoriz/mvg_stoerung:latest

# Run the container
docker run --rm ghcr.io/rmoriz/mvg_stoerung:latest

# Build locally
docker build -t mvg_stoerung .
docker run --rm mvg_stoerung

# Using make targets
make docker-build
make docker-run
make docker-test
```

## API Endpoint

The script fetches data from: `https://www.mvg.de/api/bgw-pt/v3/messages`

## Output

The script outputs JSON containing only messages with `type=INCIDENT`. The filtered results are printed to stdout, while status messages are printed to stderr.

## Example Output

```json
[
  {
    "title": "Verspätungen wegen starken Verkehrsaufkommens",
    "description": "...",
    "type": "INCIDENT",
    "provider": "MVG",
    "lines": [...],
    ...
  }
]
```

## Features

- **HTML to Text Conversion**: Converts HTML descriptions to terminal-friendly format
- **German Date Formatting**: Human-readable timestamps in DD.MM.YYYY HH:MM format
- **Duplicate Removal**: Automatically deduplicates line entries
- **Robust Error Handling**: Comprehensive network and API error handling
- **Flexible Data Parsing**: Handles various API response structures
- **Clean JSON Output**: Structured output to STDOUT, status to STDERR
- **Docker Support**: Multi-architecture container images
- **Comprehensive Testing**: 74 tests covering unit, integration, and error scenarios

## License

This project is released under the [CC0 1.0 Universal](LICENSE) license - dedicated to the public domain.