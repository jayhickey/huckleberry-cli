"""Tests for huckleberry-cli."""


def test_version():
    """Test that we can import the package and get version."""
    from huckleberry_cli import __version__
    assert __version__ == "0.1.0"
