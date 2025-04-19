"""
Tests for the vendorpy utils module.
"""

import json
from unittest.mock import MagicMock, patch

from vendorpy.utils import (
    CLOUDFLARE_BUILT_IN_PACKAGES,
    create_vendor_file,
    detect_packages_to_vendor,
    extract_project_dependencies,
)


def test_cloudflare_built_in_packages():
    """Test that the CLOUDFLARE_BUILT_IN_PACKAGES list is not empty."""
    assert len(CLOUDFLARE_BUILT_IN_PACKAGES) > 0

    # Check that some expected packages are in the list
    assert "fastapi" in CLOUDFLARE_BUILT_IN_PACKAGES
    assert "requests" in CLOUDFLARE_BUILT_IN_PACKAGES
    assert "numpy" in CLOUDFLARE_BUILT_IN_PACKAGES


@patch("subprocess.run")
def test_extract_project_dependencies(mock_run):
    """Test the extract_project_dependencies function."""
    # Mock the subprocess run function to return a list of packages
    mock_process = MagicMock()
    mock_process.stdout = json.dumps(
        {
            "dependencies": {
                "FastAPI": {"version": "0.110.0"},
                "jinja2": {"version": "3.1.2"},
                "markupsafe": {"version": "2.1.3"},
                "requests": {"version": "2.31.0"},
            }
        }
    )
    mock_run.return_value = mock_process

    # Call the function
    dependencies = extract_project_dependencies()

    # Check that the function returns the expected result
    assert dependencies == {"fastapi", "jinja2", "markupsafe", "requests"}

    # Check that the subprocess run function was called correctly
    mock_run.assert_called_once_with(
        ["uv", "export", "--format", "json"],
        check=True,
        capture_output=True,
        text=True,
    )


@patch("vendorpy.utils.extract_project_dependencies")
def test_detect_packages_to_vendor(mock_extract_deps):
    """Test the detect_packages_to_vendor function."""
    # Mock the extract_project_dependencies function to return a list of packages
    mock_extract_deps.return_value = {
        "fastapi",
        "jinja2",
        "markupsafe",
        "requests",
    }

    # Call the function
    packages = detect_packages_to_vendor()

    # Check that the function returns the expected result
    assert "vendor" in packages
    assert "built_in" in packages

    # FastAPI and requests are built-in, jinja2 and markupsafe need to be vendored
    assert sorted(packages["vendor"]) == ["jinja2", "markupsafe"]
    assert sorted(packages["built_in"]) == ["fastapi", "requests"]


def test_create_vendor_file(tmp_path):
    """Test the create_vendor_file function."""
    # Set up test data
    vendor_packages = ["jinja2", "markupsafe"]
    vendor_file = tmp_path / "vendor.txt"

    # Call the function
    create_vendor_file(vendor_packages, vendor_file)

    # Check that the file was created
    assert vendor_file.exists()

    # Check the content of the file
    with open(vendor_file, "r") as f:
        content = f.read()
        assert "jinja2" in content
        assert "markupsafe" in content
