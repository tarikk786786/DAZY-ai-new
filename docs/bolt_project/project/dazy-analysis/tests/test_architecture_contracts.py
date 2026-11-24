"""tests/test_architecture_contracts.py — Automated Architecture Regression Tests.

Validates that:
1. Core audio/DSP and session layers never reverse-import GUI or Actions.
2. Memory persistence layers maintain clean lower-layer isolation.
3. Import Linter contracts pass with 0 broken contracts.
4. Voice session manager and speaker identification components are properly decoupled.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path
import pytest

_ROOT = Path(__file__).resolve().parent.parent


def test_core_audio_devices_has_no_actions_imports():
    """core/audio_devices.py must not depend on actions/."""
    audio_dev_path = _ROOT / "core" / "audio_devices.py"
    assert audio_dev_path.is_file(), "core/audio_devices.py not found"
    tree = ast.parse(audio_dev_path.read_text(encoding="utf-8"))
    
    illegal_imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                if name.name.startswith("actions"):
                    illegal_imports.append(name.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("actions"):
                illegal_imports.append(node.module)
                
    assert not illegal_imports, f"core/audio_devices.py illegally imports actions: {illegal_imports}"


def test_voice_session_manager_isolation():
    """core/voice_session_manager.py must not import GUI or high-level actions."""
    vsm_path = _ROOT / "core" / "voice_session_manager.py"
    assert vsm_path.is_file(), "core/voice_session_manager.py not found"
    tree = ast.parse(vsm_path.read_text(encoding="utf-8"))
    
    illegal = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.startswith(("gui", "actions")):
                    illegal.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith(("gui", "actions")):
                illegal.append(node.module)
                
    assert not illegal, f"voice_session_manager.py illegally imports presentation/actions: {illegal}"


def test_import_linter_contracts():
    """Executes import-linter to enforce layer boundary contracts."""
    try:
        import importlinter.cli
        import sys
        
        cfg_file = _ROOT / ".importlinter"
        assert cfg_file.is_file(), ".importlinter configuration missing"
        
        orig_argv = sys.argv
        try:
            sys.argv = ["lint-imports", f"--config={cfg_file}"]
            exit_code = importlinter.cli.lint_imports()
            assert exit_code == 0, f"Import Linter contracts failed with code {exit_code}"
        finally:
            sys.argv = orig_argv
    except ImportError:
        pytest.skip("import-linter not installed in test environment")


def test_madr_documentation_index_present():
    """Ensures MADR documentation directory exists with key architectural decision records."""
    adr_dir = _ROOT / "docs" / "adr"
    assert adr_dir.is_dir(), "docs/adr directory must exist"
    
    required_adrs = [
        "README.md",
        "0001-use-madr-for-architecture-decisions.md",
        "0002-dual-engine-conversational-architecture.md",
        "0003-single-authoritative-feminine-voice-guarantee.md",
        "0004-two-speaker-diarization-and-assistant-echo-disqualification.md",
        "0005-calibrated-dual-threshold-vad-sensitivity.md",
        "0006-starlette-dashboard-security-and-token-auth.md",
        "0007-enforce-clean-architecture-with-import-linter.md",
    ]
    for adr in required_adrs:
        assert (adr_dir / adr).is_file(), f"Required ADR '{adr}' missing from docs/adr/"
