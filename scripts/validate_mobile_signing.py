"""Compatibility command; validates the canonical plugin endpoints."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("validate_plugin_rpc.py")), run_name="__main__")
