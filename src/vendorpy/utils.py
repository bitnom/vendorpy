"""
Utility functions for the vendorpy CLI.
"""

import subprocess
from pathlib import Path

# List of built-in packages available in Cloudflare Workers
# This list is based on the documentation and should be updated as needed
CLOUDFLARE_BUILT_IN_PACKAGES = [
    "aiohttp",
    "aiohttp-tests",
    "aiosignal",
    "annotated-types",
    "annotated-types-tests",
    "anyio",
    "async-timeout",
    "attrs",
    "certifi",
    "charset-normalizer",
    "distro",
    "fastapi",
    "frozenlist",
    "h11",
    "h11-tests",
    "hashlib",
    "httpcore",
    "httpx",
    "idna",
    "jsonpatch",
    "jsonpointer",
    "langchain",
    "langchain-core",
    "langchain-openai",
    "langsmith",
    "lzma",
    "micropip",
    "multidict",
    "numpy",
    "numpy-tests",
    "openai",
    "openssl",
    "packaging",
    "pydantic",
    "pydantic-core",
    "pydecimal",
    "pydoc-data",
    "pyyaml",
    "regex",
    "regex-tests",
    "requests",
    "six",
    "sniffio",
    "sniffio-tests",
    "sqlite3",
    "ssl",
    "starlette",
]


def create_virtual_env(python_version: str = "3.12") -> Path:
    """
    Create a Python virtual environment.

    Args:
        python_version: The Python version to use (must be 3.12 for Cloudflare Workers)

    Returns:
        Path to the created virtual environment
    """
    venv_path = Path(".venv")

    # Check if Python 3.12 is available
    try:
        # Using capture_output instead of PIPE for stdout and stderr
        subprocess.run(
            [f"python{python_version}", "--version"],
            check=True,
            capture_output=True,
            text=True,  # nosec B603
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as err:
        # Use raise from to properly chain exceptions
        msg = f"Python {python_version} is not available"
        raise RuntimeError(msg) from err

    # Create virtual environment
    # Using fixed command list is safe as we're not using shell=True
    subprocess.run(
        [f"python{python_version}", "-m", "venv", str(venv_path)],
        check=True,
        capture_output=True,
        text=True,
    )  # nosec B603

    # Install pyodide-build in the virtual environment
    pip_path = venv_path / "bin" / "pip"
    subprocess.run(
        [str(pip_path), "install", "pyodide-build"],
        check=True,
        capture_output=True,
        text=True,
    )  # nosec B603

    return venv_path


def create_pyodide_env(venv_path: Path) -> Path:
    """
    Create a Pyodide virtual environment.

    Args:
        venv_path: Path to the Python virtual environment

    Returns:
        Path to the created Pyodide virtual environment
    """
    pyodide_venv_path = Path(".venv-pyodide")

    # Create Pyodide virtual environment
    pyodide_path = venv_path / "bin" / "pyodide"
    subprocess.run(
        [str(pyodide_path), "venv", str(pyodide_venv_path)],
        check=True,
        capture_output=True,
        text=True,
    )  # nosec B603

    return pyodide_venv_path


def install_packages_to_vendor(
    pyodide_venv_path: Path, vendor_file: Path, vendor_dir: Path
) -> None:
    """
    Install packages to the vendor directory.

    Args:
        pyodide_venv_path: Path to the Pyodide virtual environment
        vendor_file: Path to the vendor.txt file
        vendor_dir: Directory to install vendored packages to
    """
    # Create vendor directory if it doesn't exist
    vendor_dir.mkdir(parents=True, exist_ok=True)

    # Install packages to vendor directory
    pip_path = pyodide_venv_path / "bin" / "pip"
    subprocess.run(
        [str(pip_path), "install", "-t", str(vendor_dir), "-r", str(vendor_file)],
        check=True,
        capture_output=True,
        text=True,
    )  # nosec B603
