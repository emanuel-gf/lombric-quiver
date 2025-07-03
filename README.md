# Lombricquiver

An end-to-end Python library for vector field and streamline animations. 
Integrate with Earth Data Hub and create seamless wind animations. 

If you would like to test and  run the examples, please consider the next steps.

## Installation

To build up the library we are using uv. In case uv is not installed in your computer, consider to install for easy management and fastness. 

### Prerequisites
- Python 3.12 or higher
- `uv` package manager


### Manim System Requirements
The main core structure of lombricquiver is from Manim. To install the library properly, a few dependencies are necessary: ffmpeg and latex.

On Windows:
```bash
winget install ffmpeg
winget install latex
```
### Clone and Install

1. Clone the repository
```bash
git clone https://github.com/emanuel-gf/lombricquiver.git
cd lombricquiver
```
Clone and Setup
git clone https://github.com/yourusername/lombricquiver.git
cd lombricquiver

2. Create and activate virtual environment
```bash
uv venv
```
4. Activate env
```bash
source .venv/bin/activate   -  macOS/Linux

.venv\Scripts\activate     -  Windows
```
4. Sync the environment to fetch requirements
```
uv sync 
```
5. Install the library 
```
uv pip install -e .
```
5. Development Setup
If you want to contribute or run tests:
Install with development dependencies
```
uv pip install -e ".[dev]"
```
7. Run tests
pytest


Note: To access ERA5 data, you'll need an Earth Data Hub API key. However, a single example dataset is provided. 


