"""Tests para validación y detección de anómalos en resultados."""

import os
import pytest
from app.analytics.result_validation import (
    validate_result,
    is_result_anomalous,
    TIME_MIN_SECONDS,
    TIME_MAX_SECONDS,
    VEF_PLAUSIBLE_MAX,
)


class TestValidateResult:
    """Validación de rangos (RECHAZO si falla)."""

    def test_valid_result_typical(self):
        """Resultado típico válido: 120 seg, 15 aciertos, 2 errores."""
        is_valid, error = validate_result(120, 15, 2)
        assert is_valid
        assert error is None

    def test_valid_result_minimum(self):
        """Límite mínimo: tiempo mínimo, 0 aciertos, 0 errores."""
        is_valid, error = validate_result(TIME_MIN_SECONDS, 0, 0)
        assert is_valid
        assert error is None

    def test_valid_result_maximum(self):
        """Límite máximo: tiempo máximo, 20 aciertos, 0 errores."""
        is_valid, error = validate_result(TIME_MAX_SECONDS, 20, 0)
        assert is_valid
        assert error is None

    def test_valid_result_boundary_sum(self):
        """Límite de suma: 20 aciertos + errores."""
        is_valid, error = validate_result(120, 15, 5)
        assert is_valid
        assert error is None

        is_valid, error = validate_result(120, 10, 10)
        assert is_valid
        assert error is None

    def test_invalid_time_too_low(self):
        """Tiempo por debajo del mínimo."""
        is_valid, error = validate_result(TIME_MIN_SECONDS - 1, 10, 5)
        assert not is_valid
        assert "Tiempo fuera de rango" in error

    def test_invalid_time_too_high(self):
        """Tiempo por encima del máximo."""
        is_valid, error = validate_result(TIME_MAX_SECONDS + 1, 10, 5)
        assert not is_valid
        assert "Tiempo fuera de rango" in error

    def test_invalid_successes_negative(self):
        """Aciertos negativos."""
        is_valid, error = validate_result(120, -1, 5)
        assert not is_valid
        assert "Aciertos deben estar entre 0 y 20" in error

    def test_invalid_successes_too_high(self):
        """Aciertos por encima de 20."""
        is_valid, error = validate_result(120, 21, 0)
        assert not is_valid
        assert "Aciertos deben estar entre 0 y 20" in error

    def test_invalid_mistakes_negative(self):
        """Errores negativos."""
        is_valid, error = validate_result(120, 10, -1)
        assert not is_valid
        assert "Errores deben estar entre 0 y 20" in error

    def test_invalid_mistakes_too_high(self):
        """Errores por encima de 20."""
        is_valid, error = validate_result(120, 10, 21)
        assert not is_valid
        assert "Errores deben estar entre 0 y 20" in error

    def test_invalid_sum_exceeds(self):
        """Suma de aciertos + errores excede 20."""
        is_valid, error = validate_result(120, 15, 6)
        assert not is_valid
        assert "Suma de aciertos + errores no puede exceder 20" in error

        is_valid, error = validate_result(120, 20, 1)
        assert not is_valid
        assert "Suma" in error


class TestIsResultAnomalous:
    """Detección de anómalos (AVISO, no rechazo)."""

    def test_normal_result(self):
        """Resultado normal sin anomalías."""
        is_anomalous, warning = is_result_anomalous(120, 15, 2, vef=50.0)
        assert not is_anomalous
        assert warning is None

    def test_anomalous_vef_high(self):
        """VEF implausiblemente alto."""
        is_anomalous, warning = is_result_anomalous(120, 15, 2, vef=250.0)
        assert is_anomalous
        assert "implausiblemente alto" in warning

    def test_anomalous_vef_boundary(self):
        """VEF justo en el límite de plausibilidad."""
        is_anomalous, warning = is_result_anomalous(120, 15, 2, vef=VEF_PLAUSIBLE_MAX + 0.1)
        assert is_anomalous

    def test_anomalous_vef_negative(self):
        """VEF negativo (error de entrada)."""
        is_anomalous, warning = is_result_anomalous(120, 15, 2, vef=-10.0)
        assert is_anomalous
        assert "negativo" in warning

    def test_anomalous_vef_none(self):
        """VEF indeterminado (None)."""
        is_anomalous, warning = is_result_anomalous(120, 15, 2, vef=None)
        assert is_anomalous
        assert "indeterminado" in warning

    def test_valid_vef_zero(self):
        """VEF exactamente 0 (resultado marginal pero válido)."""
        is_anomalous, warning = is_result_anomalous(120, 0, 0, vef=0.0)
        assert not is_anomalous
        assert warning is None

    def test_valid_vef_at_max_boundary(self):
        """VEF exactamente en el límite de plausibilidad."""
        is_anomalous, warning = is_result_anomalous(120, 15, 2, vef=VEF_PLAUSIBLE_MAX)
        assert not is_anomalous
        assert warning is None

    def test_valid_vef_high_but_plausible(self):
        """VEF alto pero plausible (p.ej., alumno muy rápido y preciso)."""
        is_anomalous, warning = is_result_anomalous(120, 20, 0, vef=190.0)
        assert not is_anomalous
        assert warning is None


class TestValidationConfigurable:
    """Validación configurable por entorno (monkeypatch)."""

    def test_time_range_configurable(self, monkeypatch):
        """Los rangos de tiempo deben ser configurables por entorno."""
        monkeypatch.setenv("RESULT_TIME_MIN_SECONDS", "60")
        monkeypatch.setenv("RESULT_TIME_MAX_SECONDS", "300")

        # Reimportar módulo para que lea los nuevos valores
        import importlib
        import app.analytics.result_validation as rv
        importlib.reload(rv)

        is_valid, error = rv.validate_result(30, 10, 5)  # Por debajo del nuevo mínimo (60)
        assert not is_valid
        assert "Tiempo fuera de rango" in error

        is_valid, error = rv.validate_result(60, 10, 5)  # Exactamente el nuevo mínimo
        assert is_valid

    def test_vef_plausible_max_configurable(self, monkeypatch):
        """VEF_PLAUSIBLE_MAX debe ser configurable."""
        monkeypatch.setenv("RESULT_VEF_PLAUSIBLE_MAX", "100.0")

        import importlib
        import app.analytics.result_validation as rv
        importlib.reload(rv)

        is_anomalous, warning = rv.is_result_anomalous(120, 15, 2, vef=150.0)
        assert is_anomalous
        assert "implausiblemente alto" in warning

        is_anomalous, warning = rv.is_result_anomalous(120, 15, 2, vef=99.0)
        assert not is_anomalous
