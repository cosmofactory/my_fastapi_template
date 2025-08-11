
Before you start, make sure you have the following installed:

- Python 3.12+ (Make sure Python is added to your PATH)

- [uv](https://docs.astral.sh/uv/getting-started/) (for dependency management)
## Installation

Install uv with our standalone installers:

```bash
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# On Windows.
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Or, from [PyPI](https://pypi.org/project/uv/):

```bash
# With pip.
pip install uv
```

```bash
# Or pipx.
pipx install uv
```

If installed via the standalone installer, uv can update itself to the latest version:

```bash
uv self update
```

See the [installation documentation](https://docs.astral.sh/uv/getting-started/installation/) for
details and alternative installation methods.

## Documentation

uv's documentation is available at [docs.astral.sh/uv](https://docs.astral.sh/uv).

Additionally, the command line reference documentation can be viewed with `uv help`.

## Features

### Projects

uv manages project dependencies and environments, with support for lockfiles, workspaces, and more,
similar to `rye` or `poetry`:


## Project installation

1. Clone the repo:

```bash
TBA
```

## Running application

**Local development**

Run FastAPI in debug mode (without solr service):
Note, if you are running this project on Windows, Makefile will not work.
Just copy the necessary commands from Makefile to terminal and run them.

```bash
make  run
```

To run the test cases:

```bash
make  test
```

To lint:

```bash
make  lint
```
