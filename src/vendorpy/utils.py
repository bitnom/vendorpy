"""
Utility functions for the vendorpy CLI.
"""

import json
import subprocess
import tomli
import tomli_w
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Union, Any

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


def extract_project_dependencies() -> Set[str]:
    """
    Extract all project dependencies using uv export.

    Returns:
        Set of package names that the project depends on

    Raises:
        RuntimeError: If uv is not available or if the command fails
    """
    try:
        # Run uv export to get all dependencies from the lockfile
        result = subprocess.run(
            ["uv", "export", "--format", "json"],
            check=True,
            capture_output=True,
            text=True,
        )  # nosec B603

        # Parse the JSON output
        packages_data = json.loads(result.stdout)

        # Extract package names (without versions)
        package_names = set()

        # Process the dependencies structure from uv export
        if "dependencies" in packages_data:
            for package_name, package_info in packages_data["dependencies"].items():
                # Normalize package name (lowercase, replace hyphens with underscores)
                normalized_name = package_name.lower().replace("-", "_")
                package_names.add(normalized_name)

        return package_names
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as err:
        error_output = getattr(err, "stderr", "Unknown error")
        raise RuntimeError(
            f"Failed to extract project dependencies: {error_output}"
        ) from err
    except FileNotFoundError as err:
        raise RuntimeError(
            "uv command not found. Please install uv using 'pip install uv'"
        ) from err


def detect_packages_to_vendor() -> Dict[str, List[str]]:
    """
    Detect which packages need to be vendored by comparing project dependencies
    with built-in Cloudflare packages.

    Returns:
        Dictionary with 'vendor' and 'built_in' keys, containing lists of package names

    Raises:
        RuntimeError: If dependency extraction fails
    """
    # Get all project dependencies
    project_dependencies = extract_project_dependencies()

    # Normalize built-in package names for comparison
    normalized_built_in = {
        pkg.lower().replace("-", "_") for pkg in CLOUDFLARE_BUILT_IN_PACKAGES
    }

    # Determine which packages need to be vendored
    to_vendor = project_dependencies - normalized_built_in
    built_in = project_dependencies & normalized_built_in

    # Get original package names for the ones that need to be vendored
    # This is needed because we normalized the names for comparison
    vendor_packages = []
    for package in to_vendor:
        # Use the original name if available
        # Note: This is a simple implementation that assumes the package name
        # in the output of uv export is the same as what should be in vendor.txt
        vendor_packages.append(package.replace("_", "-"))

    # Get original package names for built-in packages
    built_in_packages = []
    for built_in_pkg in built_in:
        # Find the exact package name with correct casing
        exact_name = next(
            (
                pkg
                for pkg in CLOUDFLARE_BUILT_IN_PACKAGES
                if pkg.lower().replace("-", "_") == built_in_pkg
            ),
            built_in_pkg,  # Use normalized name if exact match not found
        )
        built_in_packages.append(exact_name)

    return {
        "vendor": sorted(vendor_packages),
        "built_in": sorted(built_in_packages),
    }


def create_vendor_file(vendor_packages: List[str], vendor_file: Path) -> None:
    """
    Create or update the vendor.txt file with packages that need to be vendored.

    Args:
        vendor_packages: List of package names to vendor
        vendor_file: Path to the vendor.txt file
    """
    # Create vendor file directory if it doesn't exist
    vendor_file.parent.mkdir(parents=True, exist_ok=True)

    # Write packages to vendor.txt
    with open(vendor_file, "w") as f:
        for package in vendor_packages:
            f.write(f"{package}\n")


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


def find_wrangler_config() -> Optional[Tuple[Path, str]]:
    """
    Find the wrangler configuration file in the current directory.

    Returns:
        Optional tuple containing the path to the wrangler config file and its type ('toml' or 'jsonc')
        or None if no wrangler configuration file is found
    """
    # Check for wrangler.toml first (more common)
    wrangler_toml = Path("wrangler.toml")
    if wrangler_toml.exists():
        return wrangler_toml, "toml"

    # Check for wrangler.jsonc as an alternative
    wrangler_jsonc = Path("wrangler.jsonc")
    if wrangler_jsonc.exists():
        return wrangler_jsonc, "jsonc"

    # No wrangler config found
    return None


def is_vendor_rule_present(
    config_data: Union[Dict[str, Any], str], config_type: str
) -> bool:
    """
    Check if the vendor rule is already present in the configuration.

    Args:
        config_data: The parsed configuration data or content string
        config_type: Type of configuration file ('toml' or 'jsonc')

    Returns:
        True if the vendor rule is present, False otherwise
    """
    if config_type == "toml":
        if not isinstance(config_data, dict):
            return False

        # Check if rules exist and contain vendor configuration
        if "rules" not in config_data:
            return False

        rules = config_data.get("rules", [])
        for rule in rules:
            if (
                isinstance(rule, dict)
                and rule.get("globs") == ["vendor/**"]
                and rule.get("type") == "Data"
                and rule.get("fallthrough") is True
            ):
                return True

        return False

    elif config_type == "jsonc":
        # For JSONC, we'll check the string content since parsing JSONC is more complex
        vendor_pattern = '"globs":\\s*\\[\\s*"vendor/\\*\\*"\\s*\\]'
        data_pattern = '"type":\\s*"Data"'
        fallthrough_pattern = '"fallthrough":\\s*true'

        import re

        if (
            isinstance(config_data, str)
            and re.search(vendor_pattern, config_data)
            and re.search(data_pattern, config_data)
            and re.search(fallthrough_pattern, config_data)
        ):
            return True

        return False

    return False


def add_vendor_rule_to_config(config_path: Path, config_type: str) -> bool:
    """
    Add vendor rule to wrangler configuration if not already present.

    Args:
        config_path: Path to the configuration file
        config_type: Type of configuration file ('toml' or 'jsonc')

    Returns:
        True if the rule was added or already present, False if there was an error
    """
    try:
        if config_type == "toml":
            # Read the TOML file
            with open(config_path, "rb") as f:
                config_data = tomli.load(f)

            # Check if the rule is already present
            if is_vendor_rule_present(config_data, config_type):
                return True

            # Add the rule
            if "rules" not in config_data:
                config_data["rules"] = []

            vendor_rule = {"globs": ["vendor/**"], "type": "Data", "fallthrough": True}
            config_data["rules"].append(vendor_rule)

            # Write the updated TOML file
            with open(config_path, "wb") as f:
                tomli_w.dump(config_data, f)

            return True

        elif config_type == "jsonc":
            # Read the JSONC file
            with open(config_path, "r") as f:
                content = f.read()

            # Check if the rule is already present
            if is_vendor_rule_present(content, config_type):
                return True

            # Simple JSON modification that preserves comments
            # Find the position to insert the rule
            import re

            # If there's already a rules array, we'll add to it
            rules_match = re.search(r'"rules"\s*:\s*\[\s*', content)
            if rules_match:
                # Find the end of the rules array
                end_pos = rules_match.end()
                # Insert the vendor rule at the beginning of the rules array
                vendor_rule = """
  {
    "globs": ["vendor/**"],
    "type": "Data",
    "fallthrough": true
  },"""
                # Insert the rule after the opening bracket of the rules array
                new_content = content[:end_pos] + vendor_rule + content[end_pos:]
            else:
                # If there's no rules array, we'll need to add it
                # Find the last closing brace
                last_brace = content.rstrip().rfind("}")
                if last_brace == -1:
                    # Invalid JSON
                    return False

                vendor_rule = """
  "rules": [
    {
      "globs": ["vendor/**"],
      "type": "Data",
      "fallthrough": true
    }
  ]"""
                # If there are already properties, add a comma
                if content[:last_brace].rstrip().endswith("}") or content[
                    :last_brace
                ].rstrip().endswith("]"):
                    vendor_rule = "," + vendor_rule

                # Insert the rules array before the final closing brace
                new_content = content[:last_brace] + vendor_rule + content[last_brace:]

            # Write the updated JSONC file
            with open(config_path, "w") as f:
                f.write(new_content)

            return True

        return False

    except Exception as e:
        # Log the error but don't raise it - we don't want to stop the vendoring process
        # if the wrangler config update fails
        import logging

        logging.error(f"Error updating wrangler config: {e}")
        return False


def configure_wrangler_for_vendor() -> Optional[Tuple[bool, str]]:
    """
    Configure wrangler.toml or wrangler.jsonc to include vendor directory.

    Returns:
        Tuple containing success status and message, or None if no wrangler config was found
    """
    # Find the wrangler configuration file
    config_result = find_wrangler_config()
    if not config_result:
        return None

    config_path, config_type = config_result

    # Add vendor rule to config
    success = add_vendor_rule_to_config(config_path, config_type)

    if success:
        return True, f"Successfully configured {config_path.name} for vendoring"
    else:
        return False, f"Failed to configure {config_path.name} for vendoring"
