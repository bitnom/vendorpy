"""
Tests for the vendorpy utils module.
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

from vendorpy.utils import (
    CLOUDFLARE_BUILT_IN_PACKAGES,
    add_vendor_rule_to_config,
    configure_wrangler_for_vendor,
    create_vendor_file,
    detect_packages_to_vendor,
    extract_project_dependencies,
    find_wrangler_config,
    is_vendor_rule_present,
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


def test_find_wrangler_config(tmp_path):
    """Test the find_wrangler_config function."""
    # Create a temporary directory for testing
    os.chdir(tmp_path)

    # Test with no wrangler files
    assert find_wrangler_config() is None

    # Test with wrangler.toml
    wrangler_toml = Path("wrangler.toml")
    wrangler_toml.touch()
    assert find_wrangler_config() == (wrangler_toml, "toml")

    # Test with both files (should prefer toml)
    wrangler_jsonc = Path("wrangler.jsonc")
    wrangler_jsonc.touch()
    assert find_wrangler_config() == (wrangler_toml, "toml")

    # Test with only jsonc
    wrangler_toml.unlink()
    assert find_wrangler_config() == (wrangler_jsonc, "jsonc")


def test_is_vendor_rule_present_toml():
    """Test the is_vendor_rule_present function with TOML data."""
    # Test with empty config
    config_data = {}
    assert not is_vendor_rule_present(config_data, "toml")

    # Test with rules but no vendor rule
    config_data = {"rules": [{"globs": ["src/**/*.py"], "type": "ESModule"}]}
    assert not is_vendor_rule_present(config_data, "toml")

    # Test with the vendor rule present
    config_data = {
        "rules": [{"globs": ["vendor/**"], "type": "Data", "fallthrough": True}]
    }
    assert is_vendor_rule_present(config_data, "toml")

    # Test with multiple rules including the vendor rule
    config_data = {
        "rules": [
            {"globs": ["src/**/*.py"], "type": "ESModule"},
            {"globs": ["vendor/**"], "type": "Data", "fallthrough": True},
        ]
    }
    assert is_vendor_rule_present(config_data, "toml")


def test_is_vendor_rule_present_jsonc():
    """Test the is_vendor_rule_present function with JSONC content."""
    # Test with no vendor rule
    jsonc_content = """
    {
        "name": "my-worker",
        "main": "src/worker.py",
        "compatibility_date": "2025-03-16"
    }
    """
    assert not is_vendor_rule_present(jsonc_content, "jsonc")

    # Test with the vendor rule present
    jsonc_content = """
    {
        "name": "my-worker",
        "main": "src/worker.py",
        "compatibility_date": "2025-03-16",
        "rules": [
            {
                "globs": ["vendor/**"],
                "type": "Data",
                "fallthrough": true
            }
        ]
    }
    """
    assert is_vendor_rule_present(jsonc_content, "jsonc")


@patch("builtins.open", new_callable=mock_open)
@patch("tomli.load")
@patch("tomli_w.dump")
@patch("vendorpy.utils.is_vendor_rule_present")
def test_add_vendor_rule_to_config_toml(
    mock_is_present, mock_tomli_dump, mock_tomli_load, mock_file
):
    """Test adding vendor rule to a TOML config."""
    # Mock the TOML loading
    mock_tomli_load.return_value = {
        "name": "my-worker",
        "main": "src/worker.py",
        "compatibility_date": "2025-03-16",
    }

    # Mock that the rule is not already present
    mock_is_present.return_value = False

    # Call the function
    result = add_vendor_rule_to_config(Path("wrangler.toml"), "toml")

    # Check that the function returned success
    assert result is True

    # Check that the TOML was loaded and dumped
    mock_tomli_load.assert_called_once()
    mock_tomli_dump.assert_called_once()

    # The config should have been updated with the rules
    updated_config = mock_tomli_dump.call_args[0][0]
    assert "rules" in updated_config
    assert len(updated_config["rules"]) == 1
    assert updated_config["rules"][0]["globs"] == ["vendor/**"]
    assert updated_config["rules"][0]["type"] == "Data"
    assert updated_config["rules"][0]["fallthrough"] is True


@patch("builtins.open", new_callable=mock_open)
@patch("vendorpy.utils.is_vendor_rule_present")
def test_add_vendor_rule_to_config_jsonc(mock_is_present, mock_file):
    """Test adding vendor rule to a JSONC config."""
    # Mock the file content
    jsonc_content = """
    {
        "name": "my-worker",
        "main": "src/worker.py",
        "compatibility_date": "2025-03-16"
    }
    """
    mock_file.return_value.__enter__.return_value.read.return_value = jsonc_content

    # Mock that the rule is not already present
    mock_is_present.return_value = False

    # Call the function
    result = add_vendor_rule_to_config(Path("wrangler.jsonc"), "jsonc")

    # Check that the function returned success
    assert result is True

    # Check that the file was written with the updated content
    mock_file.return_value.__enter__.return_value.write.assert_called_once()

    # The content should include the vendor rule
    written_content = mock_file.return_value.__enter__.return_value.write.call_args[0][
        0
    ]
    assert '"rules"' in written_content
    assert '"globs": ["vendor/**"]' in written_content
    assert '"type": "Data"' in written_content
    assert '"fallthrough": true' in written_content


@patch("vendorpy.utils.find_wrangler_config")
@patch("vendorpy.utils.add_vendor_rule_to_config")
def test_configure_wrangler_for_vendor(mock_add_rule, mock_find_config):
    """Test the configure_wrangler_for_vendor function."""
    # Test when no wrangler config is found
    mock_find_config.return_value = None
    assert configure_wrangler_for_vendor() is None

    # Test when wrangler.toml is found and successfully configured
    mock_find_config.return_value = (Path("wrangler.toml"), "toml")
    mock_add_rule.return_value = True

    result = configure_wrangler_for_vendor()
    assert result is not None
    assert result[0] is True  # Success
    assert "Successfully configured" in result[1]  # Message

    # Test when wrangler.jsonc is found but configuration fails
    mock_find_config.return_value = (Path("wrangler.jsonc"), "jsonc")
    mock_add_rule.return_value = False

    result = configure_wrangler_for_vendor()
    assert result is not None
    assert result[0] is False  # Failed
    assert "Failed to configure" in result[1]  # Message
