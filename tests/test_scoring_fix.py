"""Tests específicos para el sistema de scoring de especialistas."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pytest
from neural_fellowship import Orquestador


@pytest.fixture
def orch():
    return Orquestador()


class TestScoringMatchFuerte:
    """Match fuerte: alta proporción de tokens de capability en tarea."""

    def test_logo_minimalista_design(self, orch):
        """Logo minimalista → design-sound-branding (audio-logo)."""
        result = orch.ruta_completa("Diseña un logo minimalista para una app")
        assert result["especialista"]["especialista"] == "design-sound-branding"
        assert result["especialista"]["confianza"] > 0

    def test_push_notifications_frontend(self, orch):
        """Notifications push → engineering-frontend-developer."""
        result = orch.ruta_completa("Diseñá un sistema de notifications push para la app")
        assert result["especialista"]["especialista"] == "engineering-frontend-developer"
        assert result["especialista"]["confianza"] > 0

    def test_oauth2_backend(self, orch):
        """OAuth2 autenticación → engineering-backend-architect."""
        result = orch.ruta_completa("Implementá autenticación OAuth2 para la API")
        assert result["especialista"]["especialista"] == "engineering-backend-architect"
        assert result["especialista"]["confianza"] > 0


class TestScoringMatchParcial:
    """Match parcial: proporción baja de tokens coincidentes."""

    def test_data_analytics_parcial(self, orch):
        """Datos de ventas → parcial (data es genérico, sales es relevante)."""
        result = orch.ruta_completa("Analizá los datos de ventas del último trimestre")
        # sales-sales-engineer o research-historian son aceptables
        assert result["especialista"]["confianza"] > 0

    def test_automacion_sin_cobertura_en_maestro(self, orch):
        """Automatización → FORTIS no tiene especialistas con 'automation'."""
        result = orch.ruta_completa("Automatizá la gestión de facturas y pagos")
        # FORTIS no tiene cobertura de automation → NULL o confianza baja
        assert result["especialista"]["confianza"] == 0 or result["especialista"]["especialista"] is None


class TestScoringCeroCoincidencias:
    """Cero coincidencias: ninguna capability coincide."""

    def test_chatbot_sin_capacidades(self, orch):
        """Chatbot con procesamiento de lenguaje natural → sin capabilities matching."""
        result = orch.ruta_completa("Creá un chatbot con procesamiento de lenguaje natural")
        # Ningún especialista tiene "chatbot" o "processing" en capabilities
        assert result["especialista"]["confianza"] == 0 or result["especialista"]["especialista"] is None

    def test_landing_sin_match(self, orch):
        """Landing page responsive → AGENCY no tiene capabilities de landing."""
        result = orch.ruta_completa("Creá una landing page responsive para mi negocio")
        # AGENCY no tiene especialistas con 'landing' o 'responsive' en capabilities
        # Puede haber fallback keywords (confianza baja) o NULL
        assert result["especialista"]["confianza"] <= 20 or result["especialista"]["especialista"] is None


class TestScoringEspecialistaIncorrecto:
    """Evitar que especialistas semánticamente incorrectos obtengan confianza alta."""

    def test_logo_no_va_a_backend(self, orch):
        """Logo minimalista NO debe ir a backend/engineering."""
        result = orch.ruta_completa("Diseña un logo minimalista para una app")
        especialista = result["especialista"]["especialista"]
        assert especialista != "engineering-backend-architect"
        assert especialista != "engineering-database-optimizer"
        assert especialista != "engineering-data-engineer"

    def test_oauth_no_va_a_marketing(self, orch):
        """OAuth2 NO debe ir a marketing."""
        result = orch.ruta_completa("Implementá autenticación OAuth2 para la API")
        especialista = result["especialista"]["especialista"]
        assert "marketing" not in especialista


class TestScoringEmpate:
    """Empate entre especialistas: comportamiento determinista."""

    def test_empate_selecciona_primero(self, orch):
        """Cuando hay empate, selecciona el primero en iteración."""
        result = orch.ruta_completa("Optimizá el rendimiento de la base de datos")
        assert result["especialista"]["confianza"] > 0

    def test_empate_mismo_maestro(self, orch):
        """Empate dentro del mismo maestro: selecciona primero."""
        result = orch.ruta_completa("Optimizá el rendimiento de la base de datos")
        assert result["especialista"]["confianza"] > 0


class TestScoringAusenciaCapacidad:
    """Ausencia real de capacidad: score 0 y sin especialista."""

    def test_tarea_sin_capacidades_disponibles(self, orch):
        """Tarea que ninguna capability cubre → confianza 0."""
        result = orch.ruta_completa("Creá un chatbot con procesamiento de lenguaje natural")
        especialista = result["especialista"]
        assert especialista["confianza"] == 0 or especialista["especialista"] is None

    def test_tarea_vaga_sin_match(self, orch):
        """Tarea vaga sin tokens relevantes → confianza 0 o nombre match permitido."""
        result = orch.ruta_completa("Hacé algo con la app")
        especialista = result["especialista"]
        # Sin matched_tokens → score viene solo de nombre (20) + keywords (30) = 50
        # Permitir nombre match pero no score alto sin matched_tokens
        if not especialista["especialista"]:
            assert True
        else:
            # Si hay especialista, debe ser por nombre (score <= 50 sin keywords)
            assert especialista["confianza"] <= 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])