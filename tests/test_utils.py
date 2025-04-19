"""
Tests for the vendorpy utils module.
"""

from vendorpy.utils import CLOUDFLARE_BUILT_IN_PACKAGES


def test_cloudflare_built_in_packages():
    """Test that the CLOUDFLARE_BUILT_IN_PACKAGES list is not empty."""
    assert len(CLOUDFLARE_BUILT_IN_PACKAGES) > 0

    # Check that some expected packages are in the list
    assert "fastapi" in CLOUDFLARE_BUILT_IN_PACKAGES
    assert "requests" in CLOUDFLARE_BUILT_IN_PACKAGES
    assert "numpy" in CLOUDFLARE_BUILT_IN_PACKAGES
