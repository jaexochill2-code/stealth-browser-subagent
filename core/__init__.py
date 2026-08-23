"""
Core engine modules for stealth browser automation, perception, human kinematics, and compliance reading.
"""

from .stealth_browser import StealthBrowserLauncher
from .human_dynamics import HumanKinematics
from .perception import VisualPerceptionEngine
from .waf_solver import WAFChallengeSolver
from .form_agent import FormFillEngine
from .fast_client import FastHarvestClient
from .compliance_reader import ComplianceReadingSimulator

__all__ = [
    "StealthBrowserLauncher",
    "HumanKinematics",
    "VisualPerceptionEngine",
    "WAFChallengeSolver",
    "FormFillEngine",
    "FastHarvestClient",
    "ComplianceReadingSimulator",
]
