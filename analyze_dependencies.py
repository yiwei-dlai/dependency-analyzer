#!/usr/bin/env python3
"""
Python Dependency Analyzer

Analyzes Python files and Jupyter notebooks in a directory to find external package dependencies.
Outputs both raw import statements and suggested package names for installation.
"""

import argparse
import ast
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


class DependencyAnalyzer:
    """Analyzes Python files and Jupyter notebooks for external dependencies."""

    # Common built-in modules that don't need installation
    BUILTIN_MODULES = {
        'os', 'sys', 'json', 'csv', 'math', 'random', 'datetime', 'time',
        'collections', 'itertools', 'functools', 'operator', 'typing', 'types',
        'pathlib', 'glob', 'shutil', 'tempfile', 'io', 're', 'string',
        'urllib', 'http', 'email', 'html', 'xml', 'sqlite3', 'pickle',
        'gzip', 'zipfile', 'tarfile', 'hashlib', 'hmac', 'secrets',
        'uuid', 'logging', 'warnings', 'traceback', 'inspect', 'gc',
        'weakref', 'copy', 'pprint', 'reprlib', 'enum', 'dataclasses',
        'contextlib', 'abc', 'numbers', 'decimal', 'fractions', 'statistics',
        'unittest', 'doctest', 'argparse', 'configparser', 'getopt',
        'threading', 'multiprocessing', 'concurrent', 'subprocess',
        'socket', 'ssl', 'asyncio', 'queue', 'sched', 'signal', 'colorsys', 'imghdr', 'timeit', 'textwrap'
    }

    # Common package mappings (import name -> package name)
    PACKAGE_MAPPINGS = {
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'sklearn': 'scikit-learn',
        'yaml': 'PyYAML',
        'bs4': 'beautifulsoup4',
        'requests': 'requests',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'plotly': 'plotly',
        'scipy': 'scipy',
        'torch': 'torch',
        'tensorflow': 'tensorflow',
        'keras': 'keras',
        'flask': 'Flask',
        'django': 'Django',
        'fastapi': 'fastapi',
        'streamlit': 'streamlit',
        'dash': 'dash',
        'openai': 'openai',
        'anthropic': 'anthropic',
        'transformers': 'transformers',
        'datasets': 'datasets',
        'huggingface_hub': 'huggingface-hub',
        'langchain': 'langchain',
        'pymongo': 'pymongo',
        'psycopg2': 'psycopg2-binary',
        'mysql': 'mysql-connector-python',
        'pymysql': 'PyMySQL',
        'sqlalchemy': 'SQLAlchemy',
        'redis': 'redis',
        'celery': 'celery',
        'pytest': 'pytest',
        'tqdm': 'tqdm',
        'click': 'click',
        'rich': 'rich',
        'typer': 'typer',
        'pydantic': 'pydantic',
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'gunicorn': 'gunicorn',
        'boto3': 'boto3',
        'azure': 'azure',
        'google': 'google-cloud',
        'dotenv': 'python-dotenv',
        'environs': 'environs',
        'decouple': 'python-decouple'
    }

    def __init__(self, directory: str):
        self.directory = Path(directory)
        self.imports_found = defaultdict(set)  # file -> set of imports
        self.all_imports = set()
        self.internal_modules = set()  # Track internal project modules (full path match)
        self.potential_internal_modules = set()  # Track potential internal modules (basename match)

    def _discover_internal_modules(self):
        """Discover all internal Python modules in the project directory."""
        self.internal_modules.clear()
        self.potential_internal_modules.clear()

        # Find all Python files and extract their module names
        for py_file in self.directory.rglob("*.py"):
            # Skip __pycache__ and other hidden directories
            if any(part.startswith('.') or part == '__pycache__' for part in py_file.parts):
                continue

            # Get relative path from project root
            rel_path = py_file.relative_to(self.directory)

            # Convert file path to module name
            if rel_path.name == '__init__.py':
                # For __init__.py files, use the parent directory name
                if len(rel_path.parts) > 1:
                    module_name = '.'.join(rel_path.parts[:-1])
                    self.internal_modules.add(module_name)
                    # Also add individual parts for partial imports
                    for i in range(1, len(rel_path.parts)):
                        partial_module = '.'.join(rel_path.parts[:i])
                        self.internal_modules.add(partial_module)

                    # Add basename for potential internal matching
                    basename = rel_path.parts[-2]  # Parent directory name
                    self.potential_internal_modules.add(basename)
            else:
                # For regular .py files, remove .py extension and convert path separators
                module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
                module_name = '.'.join(module_parts)
                self.internal_modules.add(module_name)

                # Also add the base module name (first part) for top-level imports
                if module_parts:
                    self.internal_modules.add(module_parts[0])
                    # Add intermediate module paths too
                    for i in range(1, len(module_parts)):
                        partial_module = '.'.join(module_parts[:i+1])
                        self.internal_modules.add(partial_module)

                # Add basename for potential internal matching
                basename = rel_path.stem  # Just the filename without extension
                self.potential_internal_modules.add(basename)

        print(f"Discovered {len(self.internal_modules)} internal modules: {sorted(self.internal_modules)}")
        print(f"Discovered {len(self.potential_internal_modules)} potential internal modules (basename): {sorted(self.potential_internal_modules)}")

    def analyze(self) -> Tuple[Dict[str, Set[str]], Set[str]]:
        """
        Analyze all Python files and Jupyter notebooks in the directory.

        Returns:
            Tuple of (imports_by_file, suggested_packages)
        """
        print(f"Analyzing directory: {self.directory}")

        # First, discover all internal modules in the project
        self._discover_internal_modules()

        # Find all Python and Jupyter files
        python_files = list(self.directory.rglob("*.py"))
        notebook_files = list(self.directory.rglob("*.ipynb"))

        print(f"Found {len(python_files)} Python files and {len(notebook_files)} Jupyter notebooks")

        # Analyze Python files
        for py_file in python_files:
            try:
                imports = self._analyze_python_file(py_file)
                if imports:
                    self.imports_found[str(py_file.relative_to(self.directory))] = imports
                    self.all_imports.update(imports)
            except Exception as e:
                print(f"Warning: Could not analyze {py_file}: {e}")

        # Analyze Jupyter notebooks
        for nb_file in notebook_files:
            try:
                imports = self._analyze_notebook_file(nb_file)
                if imports:
                    self.imports_found[str(nb_file.relative_to(self.directory))] = imports
                    self.all_imports.update(imports)
            except Exception as e:
                print(f"Warning: Could not analyze {nb_file}: {e}")

        # Generate package suggestions
        suggested_packages = self._suggest_packages()

        return dict(self.imports_found), suggested_packages

    def _analyze_python_file(self, file_path: Path) -> Set[str]:
        """Analyze a Python file for import statements."""
        imports = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse with AST
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])

        except SyntaxError:
            # If AST fails, try regex as fallback
            imports.update(self._extract_imports_regex(content))
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

        return imports

    def _analyze_notebook_file(self, file_path: Path) -> Set[str]:
        """Analyze a Jupyter notebook for import statements."""
        imports = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)

            # Extract code from all code cells
            for cell in notebook.get('cells', []):
                if cell.get('cell_type') == 'code':
                    source = cell.get('source', [])
                    if isinstance(source, list):
                        code = ''.join(source)
                    else:
                        code = source

                    # Try AST parsing first
                    try:
                        tree = ast.parse(code)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    imports.add(alias.name.split('.')[0])
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    imports.add(node.module.split('.')[0])
                    except SyntaxError:
                        # Fallback to regex for incomplete code cells
                        imports.update(self._extract_imports_regex(code))

        except Exception as e:
            print(f"Error parsing notebook {file_path}: {e}")

        return imports

    def _extract_imports_regex(self, code: str) -> Set[str]:
        """Extract imports using regex as fallback when AST fails."""
        imports = set()

        # Match import statements
        import_patterns = [
            r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
            r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import'
        ]

        for line in code.split('\n'):
            line = line.strip()
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    module_name = match.group(1).split('.')[0]
                    imports.add(module_name)

        return imports

    def _suggest_packages(self) -> Set[str]:
        """Suggest package names based on found imports."""
        suggested = set()

        for import_name in self.all_imports:
            # Skip built-in modules
            if import_name in self.BUILTIN_MODULES:
                continue

            # Skip internal project modules (full path match)
            if import_name in self.internal_modules:
                continue

            # Skip potential internal modules (basename match)
            if import_name in self.potential_internal_modules:
                continue

            # Check if we have a known mapping
            if import_name in self.PACKAGE_MAPPINGS:
                suggested.add(self.PACKAGE_MAPPINGS[import_name])
            else:
                # For unknown imports, suggest the import name itself
                # (this works for many packages like requests, flask, etc.)
                suggested.add(import_name)

        return suggested

    def print_results(self, imports_by_file: Dict[str, Set[str]], suggested_packages: Set[str]):
        """Print the analysis results in a formatted way."""
        print("\n" + "="*80)
        print("DEPENDENCY ANALYSIS RESULTS")
        print("="*80)

        # Part 1: All import statements by file
        print("\n1. IMPORT STATEMENTS BY FILE:")
        print("-" * 40)

        if not imports_by_file:
            print("No import statements found.")
        else:
            for file_path, imports in sorted(imports_by_file.items()):
                print(f"\n📁 {file_path}:")
                for imp in sorted(imports):
                    is_builtin = imp in self.BUILTIN_MODULES
                    is_internal = imp in self.internal_modules
                    is_potential_internal = imp in self.potential_internal_modules

                    if is_builtin:
                        status = "(built-in)"
                    elif is_internal:
                        status = "(internal)"
                    elif is_potential_internal:
                        status = "(potential internal)"
                    else:
                        status = "(external)"

                    print(f"  • {imp} {status}")

        # Part 2: Suggested packages
        print(f"\n\n2. SUGGESTED PACKAGES TO INSTALL:")
        print("-" * 40)

        if not suggested_packages:
            print("No external packages detected.")
        else:
            print(f"Found {len(suggested_packages)} potential packages:\n")

            # Group by common categories for better readability
            categorized = self._categorize_packages(suggested_packages)

            for category, packages in categorized.items():
                if packages:
                    print(f"🔧 {category}:")
                    for pkg in sorted(packages):
                        print(f"  • {pkg}")
                    print()

            # Generate pip install command
            all_packages = sorted(suggested_packages)
            print("💡 To install all suggested packages:")
            print(f"pip install {' '.join(all_packages)}")

            # Generate requirements.txt content
            print(f"\n📄 For requirements.txt:")
            for pkg in all_packages:
                print(pkg)

    def _categorize_packages(self, packages: Set[str]) -> Dict[str, List[str]]:
        """Categorize packages for better display."""
        categories = {
            "Data Science & ML": [],
            "Web Development": [],
            "Database": [],
            "Cloud & APIs": [],
            "Utilities": [],
            "Other": []
        }

        data_science = {'numpy', 'pandas', 'matplotlib', 'seaborn', 'plotly', 'scipy',
                       'scikit-learn', 'torch', 'tensorflow', 'keras', 'transformers',
                       'datasets', 'huggingface-hub'}
        web_dev = {'Flask', 'Django', 'fastapi', 'streamlit', 'dash', 'uvicorn',
                  'gunicorn', 'requests', 'beautifulsoup4'}
        database = {'pymongo', 'psycopg2-binary', 'mysql-connector-python', 'PyMySQL',
                   'SQLAlchemy', 'redis'}
        cloud_apis = {'boto3', 'azure', 'google-cloud', 'openai', 'anthropic'}
        utilities = {'python-dotenv', 'environs', 'python-decouple', 'click', 'rich',
                    'typer', 'tqdm', 'pytest', 'Pillow', 'opencv-python', 'PyYAML'}

        for pkg in packages:
            if pkg in data_science:
                categories["Data Science & ML"].append(pkg)
            elif pkg in web_dev:
                categories["Web Development"].append(pkg)
            elif pkg in database:
                categories["Database"].append(pkg)
            elif pkg in cloud_apis:
                categories["Cloud & APIs"].append(pkg)
            elif pkg in utilities:
                categories["Utilities"].append(pkg)
            else:
                categories["Other"].append(pkg)

        return categories


def main():
    """Main function to run the dependency analyzer."""
    parser = argparse.ArgumentParser(
        description="Analyze Python files and Jupyter notebooks for external dependencies"
    )
    parser.add_argument(
        "directory",
        help="Directory to analyze for Python files and notebooks"
    )
    parser.add_argument(
        "--output",
        choices=["console", "json", "requirements"],
        default="console",
        help="Output format (default: console)"
    )

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        return 1

    # Run analysis
    analyzer = DependencyAnalyzer(args.directory)
    imports_by_file, suggested_packages = analyzer.analyze()

    if args.output == "console":
        analyzer.print_results(imports_by_file, suggested_packages)
    elif args.output == "json":
        result = {
            "imports_by_file": {k: list(v) for k, v in imports_by_file.items()},
            "suggested_packages": list(suggested_packages)
        }
        print(json.dumps(result, indent=2))
    elif args.output == "requirements":
        for pkg in sorted(suggested_packages):
            print(pkg)

    return 0


if __name__ == "__main__":
    exit(main())
