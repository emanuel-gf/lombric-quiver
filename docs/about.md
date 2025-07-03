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
The main core structure of lombricquiver is from Manim. To install the library properly, a few dependencies are necessar: ffmpeg and latex.

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

2. Create and activate virtual environment using uv
```bash
uv venv
# On Windows:
.venv\Scripts\activate
```

3. Install lombricquiver for testing
## Sync all dependencies 
uv sync

# Install lombricquiver
uv pip install lombricquiver

4. If you are running for development ->  Install dependencies and development packages 
```bas
uv pip install lombriquiver .dev
uv pip install -e ".[dev,docs]"
uv pip install jupyter notebook ipykernel
```
5. Try it out
Test the example file: quiver-plot for a more compreensive exploratory 


Note: To access ERA5 data, you'll need an Earth Data Hub API key. However, a single example dataset is provided. 

## Development

If you want to contribute or modify the code:

### Clone and Install
```bash
# Get the code
git clone https://github.com/emanuel-gf/lombricquiver.git
cd lombricquiver

# Setup development environment
uv venv
.venv\Scripts\activate
uv pip install -e ".[dev,docs]"
python -m ipykernel install --user --name=lombric-quiver
```

### Build documentation
```bash