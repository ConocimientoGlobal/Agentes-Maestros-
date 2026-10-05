"""Tests para la corrección del mecanismo de routing."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import unittest
from neural_fellowship import Orquestador

class TestRoutingCorrection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o = Orquestador()

    def test_fallback_sin_capability_no_routing(self):
        """SMTP no tiene capability → no routing."""
        r = self.o.ruta_completa("Automatizá el envío de correos por SMTP")
        self.assertIsNone(r["especialista"])

    def test_empate_fallbacks_no_routing(self):
        """Vago sin match → no routing."""
        r = self.o.ruta_completa("Necesito ayuda con esto")
        self.assertIsNone(r["especialista"])

    def test_capability_real_gana(self):
        """Logo con capability real → design-sound-branding."""
        r = self.o.ruta_completa("Diseñá un logo minimalista para una marca")
        self.assertIsNotNone(r["especialista"])
        self.assertEqual(r["especialista"]["especialista"], "design-sound-branding")
        self.assertIn("logo", r["especialista"]["matched_tokens"])

    def test_linux_no_va_a_motion(self):
        """Servidor Linux → no debe ir a motion-designer."""
        r = self.o.ruta_completa("Repará un servidor Linux que no inicia")
        if r["especialista"]:
            self.assertNotEqual(r["especialista"]["especialista"], "design-motion-designer")

    def test_marketing_no_va_a_frontend(self):
        """Estrategia marketing → no debe ir a frontend."""
        r = self.o.ruta_completa("Creá una estrategia de marketing para un restaurante")
        if r["especialista"]:
            self.assertNotEqual(r["especialista"]["especialista"], "engineering-frontend-developer")

    def test_legal_no_va_a_customer_success(self):
        """Contrato legal → no debe ir a customer-success."""
        r = self.o.ruta_completa("Traducí un contrato legal del inglés al japonés")
        if r["especialista"]:
            self.assertNotEqual(r["especialista"]["especialista"], "specialized-customer-success-manager")

    def test_match_fuerte_confianza_alta(self):
        """Logo con match fuerte → confianza >= 80."""
        r = self.o.ruta_completa("Diseñá un logo minimalista para una marca")
        self.assertGreaterEqual(r["especialista"]["confianza"], 80)

    def test_sinonimo_produce_capability_real(self):
        """Sinónimo 'marketing' → matched_tokens contiene marketing."""
        r = self.o.ruta_completa("Creá una estrategia de marketing para un restaurante")
        if r["especialista"]:
            self.assertIn("marketing", r["especialista"]["matched_tokens"])

    def test_ausencia_real_de_capacidad(self):
        """3D game: no existe capability → no routing."""
        r = self.o.ruta_completa("Creá una animación 3D para un videojuego")
        self.assertIsNone(r["especialista"])

    def test_logo_landing_cafeteria(self):
        """Logo + landing → design-sound-branding."""
        r = self.o.ruta_completa("Diseñá un logo y una landing page para una cafetería")
        self.assertIsNotNone(r["especialista"])
        self.assertEqual(r["especialista"]["especialista"], "design-sound-branding")

if __name__ == "__main__":
    unittest.main(verbosity=2)