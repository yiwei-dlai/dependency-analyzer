# Python Dependency Analyzer

A tool to analyze Python files and Jupyter notebooks in a directory to identify external package dependencies.

## Features

- **Recursive Analysis**: Scans all `.py` and `.ipynb` files in a directory and subdirectories
- **Dual Output**: 
  1. Lists all import statements found by file (with built-in vs external classification)
  2. Suggests specific Python packages to install
- **Smart Package Mapping**: Maps import names to correct package names (e.g., `cv2` → `opencv-python`)
- **Multiple Output Formats**: Console (default), JSON, or requirements.txt format
- **Robust Parsing**: Uses AST parsing with regex fallback for incomplete code

## Usage

### Basic Usage
```bash
python analyze_dependencies.py /path/to/your/project
```

### Output Formats
```bash
# Pretty console output (default)
python analyze_dependencies.py /path/to/project

# JSON output
python analyze_dependencies.py /path/to/project --output json

# Requirements.txt format
python analyze_dependencies.py /path/to/project --output requirements
```

### Example Output

```
================================================================================
DEPENDENCY ANALYSIS RESULTS
================================================================================

1. IMPORT STATEMENTS BY FILE:
----------------------------------------

📁 data_analysis.py:
  • numpy (external)
  • pandas (external)
  • matplotlib (external)
  • os (built-in)

📁 notebooks/exploration.ipynb:
  • seaborn (external)
  • plotly (external)
  • json (built-in)

2. SUGGESTED PACKAGES TO INSTALL:
----------------------------------------
Found 4 potential packages:

🔧 Data Science & ML:
  • matplotlib
  • numpy
  • pandas
  • plotly
  • seaborn

💡 To install all suggested packages:
pip install matplotlib numpy pandas plotly seaborn

📄 For requirements.txt:
matplotlib
numpy
pandas
plotly
seaborn
```

## How It Works

1. **File Discovery**: Recursively finds all `.py` and `.ipynb` files
2. **Import Extraction**: 
   - Uses Python's AST module for accurate parsing
   - Falls back to regex for incomplete/invalid syntax
   - Extracts from Jupyter notebook code cells
3. **Classification**: Separates built-in modules from external packages
4. **Package Mapping**: Maps import names to installable package names
5. **Categorization**: Groups packages by type (Data Science, Web Dev, etc.)

## Supported File Types

- **Python files** (`.py`): Full AST parsing with regex fallback
- **Jupyter notebooks** (`.ipynb`): Extracts code from all code cells

## Package Mapping Examples

The tool includes intelligent mapping for common packages:

| Import Name | Package Name |
|-------------|--------------|
| `cv2` | `opencv-python` |
| `PIL` | `Pillow` |
| `sklearn` | `scikit-learn` |
| `yaml` | `PyYAML` |
| `bs4` | `beautifulsoup4` |

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)
