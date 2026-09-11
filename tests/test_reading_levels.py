"""Tests para clasificación de nivel lector."""

import os
import pytest
from app.analytics.reading_levels import classify_reading_level


def test_reading_level_low():
    """VEF < 25 debe ser "bajo"."""
    assert classify_reading_level(0.0) == "bajo"
    assert classify_reading_level(10.5) == "bajo"
    assert classify_reading_level(24.99) == "bajo"


def test_reading_level_boundary_low():
    """VEF = 25 (límite) debe ser "normal"."""
    assert classify_reading_level(25.0) == "normal"


def test_reading_level_normal():
    """25 <= VEF <= 85 debe ser "normal"."""
    assert classify_reading_level(25.01) == "normal"
    assert classify_reading_level(50.0) == "normal"
    assert classify_reading_level(85.0) == "normal"


def test_reading_level_boundary_high():
    """VEF > 85 debe ser "alto"."""
    assert classify_reading_level(85.01) == "alto"
    assert classify_reading_level(100.0) == "alto"
    assert classify_reading_level(150.0) == "alto"


def test_reading_level_none():
    """VEF = None debe devolver None."""
    assert classify_reading_level(None) is None


def test_reading_level_negative():
    """VEF negativo debe ser "bajo" (por debajo de 25)."""
    assert classify_reading_level(-10.0) == "bajo"
    assert classify_reading_level(-0.5) == "bajo"


def test_reading_level_configurable_thresholds(monkeypatch):
    """Los umbrales deben ser configurables por entorno."""
    # Cambiar umbrales: bajo < 50, normal 50-100, alto > 100
    monkeypatch.setenv("READING_LEVEL_THRESHOLD_LOW", "50.0")
    monkeypatch.setenv("READING_LEVEL_THRESHOLD_HIGH", "100.0")

    # Reimportar el módulo para que lea los nuevos valores
    import importlib
    import app.analytics.reading_levels as rl
    importlib.reload(rl)

    assert rl.classify_reading_level(30.0) == "bajo"
    assert rl.classify_reading_level(50.0) == "normal"
    assert rl.classify_reading_level(75.0) == "normal"
    assert rl.classify_reading_level(100.0) == "normal"
    assert rl.classify_reading_level(150.0) == "alto"
