# Indexical Python SDK

The Indexical SDK for Python makes it easier to use the Indexical API **for Python projects that are interacting with an existing codebase**. It primarily contains helper functions that can extract the appropriate sources from code/configuration files, for use in Indexical API calls.

Currently, the SDK supports analyzing projects written in JS/TS or in Python. Specifically, the SDK can extract sources in the following ways:

In JS/TS projects:

- Analyzing a JS/TS source file (`extract_sources_from_js`)
- Analyzing a package.json file (`extract_sources_from_package_json`)
- Analyzing a package-lock.json file (`extract_sources_from_package_lock_json`)

In Python projects:

- Analyzing a Python JS/TS source file (`extract_sources_from_py`)
- Analyzing a requirements.txt file (`extract_sources_from_requirements_txt`)

## Installation

```bash
pip install indexical_sdk
```

## Usage

All `extract_sources_from_...` functions expect a single argument (the input file's contents, as a string), and return a Dict that can be combined with the body of your API request (containing either the `npm` or the `pypi` key, depending on the type of project being analyzed). The Indexical SDK is meant to work with whatever library you're currently using for accessing file contents and making API calls. The example here uses `requests` and python's `pathlib`, but could easily be adapted for any other choice:

```python
import indexical_sdk
from pathlib import Path
import requests
import os

package_file_contents = Path("/path/to/package.json").read_text()
prompt = "your prompt here"
npm = indexical_sdk.extract_sources_from_package_json(package_file_contents)["npm"]
API_KEY = os.getenv('INDEXICAL_API_KEY')

response = requests.post(
    "https://api.indexical.dev/context",
    json={
        "npm": npm,
        "prompt": prompt
    },
    headers={
        "Authorization": f"Bearer {API_KEY}"
    }
)
# see https://indexical.dev/docs for API docs on the expected response

```

The same example applies for using any of the SDK's included extractors (listed above, in the first section of the README).
