"""
Tests for the vendorpy CLI.
"""

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
