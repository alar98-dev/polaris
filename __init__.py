"""Delegator module: expose PolarisAgent from agent_core and app instance.

Keep this file small so other imports like `from polaris.agent import PolarisAgent`
keep working while the core implementation lives in `agent_core.py`.
"""

from .agent_core import PolarisAgent
from .app import app

__all__ = ["PolarisAgent", "app"]