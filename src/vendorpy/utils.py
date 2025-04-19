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

    Raises:
        RuntimeError: If Python is not available or if the virtual environment creation fails
        FileNotFoundError: If pip is not found in the created environment
    """
    venv_path = Path(".venv")

    # Remove existing virtual environment if it exists
    if venv_path.exists():
        import shutil

        shutil.rmtree(venv_path)

    # Check if Python version is available
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
        msg = f"Python {python_version} is not available. Please install Python {python_version} and try again."
        raise RuntimeError(msg) from err

    # Create virtual environment
    try:
        # Using fixed command list is safe as we're not using shell=True
        subprocess.run(
            [f"python{python_version}", "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
            text=True,
        )  # nosec B603
    except subprocess.CalledProcessError as err:
        error_output = err.stderr if err.stderr else "Unknown error"
        raise RuntimeError(
            f"Failed to create virtual environment: {error_output}"
        ) from err

    # Verify the environment was created
    if not venv_path.exists():
        raise RuntimeError(f"Virtual environment was not created at {venv_path}")

    # Install pyodide-build in the virtual environment
    pip_path = venv_path / "bin" / "pip"

    # Check if pip exists
    if not pip_path.exists():
        raise FileNotFoundError(
            f"pip not found in virtual environment at {pip_path}. "
            "Make sure the virtual environment was created correctly."
        )

    try:
        subprocess.run(
            [str(pip_path), "install", "pyodide-build"],
            check=True,
            capture_output=True,
            text=True,
        )  # nosec B603
    except subprocess.CalledProcessError as err:
        error_output = err.stderr if err.stderr else "Unknown error"
        raise RuntimeError(f"Failed to install pyodide-build: {error_output}") from err

    return venv_path


def create_pyodide_env(venv_path: Path) -> Path:
    """
    Create a Pyodide virtual environment.

    Args:
        venv_path: Path to the Python virtual environment

    Returns:
        Path to the created Pyodide virtual environment

    Raises:
        RuntimeError: If the pyodide command is not found or fails to create the environment
    """
    pyodide_venv_path = Path(".venv-pyodide")

    # Create Pyodide virtual environment
    pyodide_path = venv_path / "bin" / "pyodide"

    # Check if pyodide exists
    if not pyodide_path.exists():
        raise RuntimeError(
            f"Pyodide command not found at {pyodide_path}. Make sure pyodide-build is installed correctly."
        )

    try:
        subprocess.run(
            [str(pyodide_path), "venv", str(pyodide_venv_path)],
            check=True,
            capture_output=True,
            text=True,
        )  # nosec B603
    except subprocess.CalledProcessError as err:
        error_output = err.stderr if err.stderr else "Unknown error"
        raise RuntimeError(
            f"Failed to create Pyodide environment: {error_output}"
        ) from err

    # Verify the environment was created
    if not pyodide_venv_path.exists():
        raise RuntimeError(
            f"Pyodide environment was not created at {pyodide_venv_path}"
        )

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

    Raises:
        FileNotFoundError: If the vendor.txt file or pip command is not found
        RuntimeError: If the installation fails
    """
    # Check if vendor file exists and is not empty
    if not vendor_file.exists():
        raise FileNotFoundError(f"Vendor file not found: {vendor_file}")

    # Check if vendor file is empty
    if vendor_file.stat().st_size == 0:
        raise ValueError(f"Vendor file is empty: {vendor_file}")

    # Create vendor directory if it doesn't exist
    vendor_dir.mkdir(parents=True, exist_ok=True)

    # Check if pip exists in the Pyodide environment
    pip_path = pyodide_venv_path / "bin" / "pip"
    if not pip_path.exists():
        raise FileNotFoundError(
            f"pip not found in Pyodide environment at {pip_path}. "
            "Make sure the Pyodide environment was created correctly."
        )

    try:
        # Install packages to vendor directory
        result = subprocess.run(
            [str(pip_path), "install", "-t", str(vendor_dir), "-r", str(vendor_file)],
            check=True,
            capture_output=True,
            text=True,
        )  # nosec B603

        # Check if any packages were installed
        if "Successfully installed" not in result.stdout and not any(
            Path(vendor_dir).glob("*/__init__.py")
        ):
            raise RuntimeError(
                f"No packages were installed to {vendor_dir}. "
                "Check your vendor.txt file and make sure the packages are available."
            )
    except subprocess.CalledProcessError as err:
        error_output = err.stderr if err.stderr else "Unknown error"
        raise RuntimeError(f"Failed to install packages: {error_output}") from err
