"""
Tests for the vendorpy CLI.
"""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner as TyperCliRunner

from vendorpy.cli import app
from vendorpy.utils import CLOUDFLARE_BUILT_IN_PACKAGES


def test_list_built_in():
    """Test the list-built-in command."""
    runner = TyperCliRunner()
    result = runner.invoke(app, ["list-built-in"])
    assert result.exit_code == 0

    # Check that all built-in packages are listed in the output
    for package in CLOUDFLARE_BUILT_IN_PACKAGES:
        assert package in result.stdout


def test_cli_help():
    """Test the CLI help command."""
    runner = TyperCliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert (
        "Vendorpy - A tool for automating Cloudflare Python Workers vendoring"
        in result.stdout
    )


def test_vendor_help():
    """Test the vendor command help."""
    runner = TyperCliRunner()
    result = runner.invoke(app, ["vendor", "--help"])
    assert result.exit_code == 0
    assert "Vendor Python packages for Cloudflare Workers" in result.stdout


def test_auto_vendor_help():
    """Test the auto-vendor command help."""
    runner = TyperCliRunner()
    result = runner.invoke(app, ["auto-vendor", "--help"])
    assert result.exit_code == 0
    assert "Automatically detect and vendor packages" in result.stdout


@patch("vendorpy.cli.detect_packages_to_vendor")
@patch("vendorpy.cli.create_vendor_file")
@patch("vendorpy.cli.generate_requirements")
@patch("vendorpy.cli.create_virtual_env")
@patch("vendorpy.cli.create_pyodide_env")
@patch("vendorpy.cli.install_packages_to_vendor")
def test_auto_vendor_command(
    mock_install_packages,
    mock_create_pyodide_env,
    mock_create_virtual_env,
    mock_generate_requirements,
    mock_create_vendor_file,
    mock_detect_packages,
    tmp_path,
):
    """Test the auto-vendor command."""
    # Mock the detection of packages
    mock_detect_packages.return_value = {
        "vendor": ["jinja2", "markupsafe"],
        "built_in": ["fastapi", "requests"],
    }

    # Mock the creation of environments
    mock_create_virtual_env.return_value = Path("/mock/venv")
    mock_create_pyodide_env.return_value = Path("/mock/pyodide-venv")

    vendor_file = tmp_path / "vendor.txt"
    requirements_file = tmp_path / "requirements.txt"
    vendor_dir = tmp_path / "vendor"

    # Run the command
    runner = TyperCliRunner()
    result = runner.invoke(
        app,
        [
            "auto-vendor",
            "--vendor-file",
            str(vendor_file),
            "--requirements-file",
            str(requirements_file),
            "--vendor-dir",
            str(vendor_dir),
        ],
    )

    # Check the command ran successfully
    assert result.exit_code == 0

    # Verify our mocks were called correctly
    mock_detect_packages.assert_called_once()
    mock_create_vendor_file.assert_called_once_with(
        ["jinja2", "markupsafe"], vendor_file
    )
    mock_generate_requirements.assert_called_once_with(requirements_file)
    mock_create_virtual_env.assert_called_once()
    mock_create_pyodide_env.assert_called_once_with(Path("/mock/venv"))
    mock_install_packages.assert_called_once_with(
        Path("/mock/pyodide-venv"), vendor_file, vendor_dir
    )

    # Check the output for expected content
    assert "Successfully vendored 2 packages" in result.stdout
    assert "Need Vendoring" in result.stdout
    assert "jinja2, markupsafe" in result.stdout
    assert "Built-in (No Vendoring Required)" in result.stdout
    assert "fastapi, requests" in result.stdout


@patch("vendorpy.cli.detect_packages_to_vendor")
@patch("vendorpy.cli.create_vendor_file")
def test_auto_vendor_no_packages(
    mock_create_vendor_file, mock_detect_packages, tmp_path
):
    """Test the auto-vendor command when no packages need vendoring."""
    # Mock the detection of packages - all are built-in
    mock_detect_packages.return_value = {
        "vendor": [],
        "built_in": ["fastapi", "requests"],
    }

    vendor_file = tmp_path / "vendor.txt"
    requirements_file = tmp_path / "requirements.txt"
    vendor_dir = tmp_path / "vendor"

    # Run the command
    runner = TyperCliRunner()
    result = runner.invoke(
        app,
        [
            "auto-vendor",
            "--vendor-file",
            str(vendor_file),
            "--requirements-file",
            str(requirements_file),
            "--vendor-dir",
            str(vendor_dir),
        ],
    )

    # Check the command ran successfully
    assert result.exit_code == 0

    # Verify create_vendor_file was not called
    mock_create_vendor_file.assert_not_called()

    # Check the output for expected content
    assert "No packages need to be vendored" in result.stdout
    # Check for partial text to avoid formatting issues with newlines/spaces
    assert "already built" in result.stdout
    assert "into Cloudflare Workers" in result.stdout


def test_isbuiltin_built_in_package():
    """Test the isbuiltin command with a built-in package."""
    runner = TyperCliRunner()
    result = runner.invoke(app, ["isbuiltin", "fastapi"])
    assert result.exit_code == 0
    assert "is a built-in package" in result.stdout
    assert "You can use it directly without vendoring" in result.stdout


def test_isbuiltin_non_built_in_package():
    """Test the isbuiltin command with a non-built-in package."""
    runner = TyperCliRunner()
    result = runner.invoke(app, ["isbuiltin", "flask"])
    assert result.exit_code == 0
    assert "is NOT a built-in package" in result.stdout
    assert "You need to vendor this package" in result.stdout
    assert "vendorpy isbuiltin flask --add" in result.stdout


def test_isbuiltin_with_add_flag(tmp_path):
    """Test the isbuiltin command with the --add flag."""
    # Create a temporary vendor.txt file
    vendor_file = tmp_path / "vendor.txt"

    # Run the command with the --add flag
    runner = TyperCliRunner()
    result = runner.invoke(
        app, ["isbuiltin", "flask", "--add", "--vendor-file", str(vendor_file)]
    )

    # Check the command output
    assert result.exit_code == 0
    assert "is NOT a built-in package" in result.stdout
    assert "Added flask to" in result.stdout

    # Check that the package was added to the vendor.txt file
    assert vendor_file.exists()
    with open(vendor_file, "r") as f:
        content = f.read()
        assert "flask" in content
