# tests/test_basic.py
import pytest
from dealflow import DealFlow

def test_dealflow_exists():
    """Test that the DealFlow class exists."""
    assert hasattr(DealFlow, "__init__")

def test_version():
    """Test that the version is defined."""
    import dealflow
    assert hasattr(dealflow, "__version__")