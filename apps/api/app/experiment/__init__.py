"""Experiment Tracking Module.

Provides MongoDB-backed experiment record storage and comparison
for Qlib model training and evaluation pipelines.
"""

from .tracker import ExperimentTracker

__all__ = [
    "ExperimentTracker",
]
