"""
🛡️ SENTINEL-DEV Agent Module
============================

Autonomous Dev Server Health Monitoring & Auto-Repair

Components:
- health_monitors.py: Health check implementations
- repair_workflows.py: Auto-repair procedures

Usage:
    from agents.sentinel import HealthMonitor, RepairWorkflow
"""

from .health_monitors import HealthMonitor, HealthCheckConfig
from .repair_workflows import RepairWorkflow, RepairConfig

__all__ = [
    "HealthMonitor",
    "HealthCheckConfig",
    "RepairWorkflow",
    "RepairConfig",
]

# SENTINEL Agent Configuration
SENTINEL_CONFIG = {
    "id": "SENTINEL",
    "name": "SENTINEL-DEV",
    "version": "1.0.0",
    "model": "claude-sonnet-4-20250514",
    "role": "DevOps Guardian & Auto-Repair",
    "expertise": [
        "Server Health Monitoring",
        "Build Pipeline Diagnosis",
        "Database Integrity",
        "Process Management",
        "Log Analysis",
        "Automated Recovery"
    ],
    "emoji": "🛡️",
    "personality": "Vigilant, proactive, fixes issues before escalation",
    "token_budget": {
        "daily_limit": 10000,
        "quick_check": 0,
        "smart_check": 500,
        "deep_check": 2000,
        "repair": 3000
    }
}
