"""Router de snapshots: por campaña y vista agregada vigente."""

from fastapi import APIRouter, Depends, HTTPException, status

from src import clients
from src.models.snapshots import SnapshotOut
from src.security import require_api_key
from src.services import configuracion, snapshots

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get('/campanas/{id_campana}/snapshot', response_model=SnapshotOut)
def get_campana_snapshot(id_campana: int) -> dict:
    """Obtiene el snapshot vigente de una campaña.

    Args:
        id_campana: id de la campaña.

    Returns:
        `SnapshotOut` calculado con la configuración vigente.

    Raises:
        HTTPException: 404 si no hay configuración vigente, o si el snapshot
            todavía no se calculó para esa combinación.
    """
    engine = clients.get_db_engine()
    try:
        configuracion_vigente = configuracion.get_vigente(engine)
        if configuracion_vigente is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Sin configuracion vigente')
        snapshot_encontrado = snapshots.get_snapshot(
            engine, id_campana=id_campana, id_configuracion=configuracion_vigente['id_configuracion']
        )
    finally:
        engine.dispose()
    if snapshot_encontrado is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Snapshot no calculado todavia')
    return snapshot_encontrado


@router.get('/snapshots', response_model=list[SnapshotOut])
def get_snapshots(vigente: bool = False) -> list[dict]:
    """Lista todos los snapshots calculados con la configuración vigente.

    Args:
        vigente: debe mandarse como `true` explícitamente — es el único modo soportado.

    Returns:
        Lista de `SnapshotOut` — alimenta la vista global "Todas" del dashboard.

    Raises:
        HTTPException: 400 si `vigente` no se manda como `true`.
    """
    if not vigente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Falta ?vigente=true')
    engine = clients.get_db_engine()
    try:
        return snapshots.list_snapshots_vigentes(engine)
    finally:
        engine.dispose()
