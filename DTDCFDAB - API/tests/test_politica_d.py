import pytest

from src.services.politica_d import calcular


def test_calcular_no_esta_implementado_todavia():
    """Politica D (14 fechas Buho + 13 metadatos) vive hoy en etl.ipynb / AUDITORIA_ETL.txt, en el
    repo "[Direccion] Reporte proceso total de campana" — no leido en esta sesion de diseno.
    Portarlo es una sesion de brainstorming + plan separada (requiere ademas las credenciales de
    Claw, aun sin confirmar). Este test documenta el limite de alcance."""
    with pytest.raises(NotImplementedError):
        calcular(id_claw=229, configuracion={}, claw_picks_client=None, claw_tracking_client=None, retool_engine=None)
