# DTDCFDAB - DB

Esquema de base de datos MySQL y migraciones Alembic para el proyecto **Dashboard total de campaña FDA - Buho** (DTDCFDAB).

Las tablas residen en la base compartida `dmc-general` (Digital Ocean) y utilizan el prefijo reservado `dtdcfdab_*` para evitar colisiones con otros servicios de Búho.

---

## Características

- Modelado relacional con **SQLAlchemy 2.0**.
- Control de versiones y migraciones de esquema mediante **Alembic**.
- 6 tablas normalizadas:
  - `dtdcfdab_evento`: catálogo maestro de hitos FDA.
  - `dtdcfdab_campana`: registro de campañas operativas vinculadas a Claw.
  - `dtdcfdab_campana_evento`: hitos manuales/cargados por campaña.
  - `dtdcfdab_configuracion`: parámetros versionados de la Política D de cálculo.
  - `dtdcfdab_campana_snapshot`: resultados calculados del ETL (14 fechas y 13 métricas).
  - `dtdcfdab_job_ejecucion`: bitácora de ejecuciones y estado de Cloud Tasks.
- Pruebas de integración automatizadas con aislamiento transaccional (rollback automático).

---

## Instalación

### Prerrequisitos
- Python 3.11 o superior.
- Acceso de red y credenciales a la base de datos MySQL `dmc-general` en Digital Ocean.

### Pasos
1. Crear y activar el entorno virtual dentro de esta carpeta:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # En Windows PowerShell
   ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```
3. Configurar variables de entorno:
   Copiar `.env.example` como `.env` y completar los valores correspondientes:
   ```bash
   cp .env.example .env
   ```

---

## Configuración

Variables requeridas en `.env`:

| Variable | Descripción | Ejemplo / Default |
| :--- | :--- | :--- |
| `MYSQL_HOST_DMC_GENERAL` | Host del cluster MySQL en Digital Ocean | `db-mysql-nyc1-...ondigitalocean.com` |
| `MYSQL_PORT_DMC_GENERAL` | Puerto de conexión | `25060` |
| `MYSQL_USER_DMC_GENERAL` | Usuario de base de datos | `doadmin` |
| `MYSQL_PASSWORD_DMC_GENERAL` | Contraseña de acceso | `...` |
| `MYSQL_DB_DMC_GENERAL` | Nombre de la base de datos | `dmc-general` |

---

## Migraciones con Alembic

Todas las migraciones se encuentran en `alembic/versions/`.

- **Aplicar todas las migraciones pendientes a la base de datos:**
  ```bash
  alembic upgrade head
  ```
- **Revertir la última migración aplicada:**
  ```bash
  alembic downgrade -1
  ```
- **Generar una nueva revisión de migración vacía:**
  ```bash
  alembic revision -m "descripcion_del_cambio"
  ```
- **Ver historial de revisiones:**
  ```bash
  alembic history --verbose
  ```

---

## Testing

Las pruebas de integración validan restricciones de unicidad, integridad referencial, cascadas y semillas de configuración. Se ejecutan contra la base real de Digital Ocean dentro de transacciones aisladas que ejecutan rollback al finalizar:

```bash
pytest -v
```

> **Nota:** La configuración en `pytest.ini` (`pythonpath = src`, `testpaths = tests`) garantiza que el paquete `dtdcfdab_db` y las pruebas se descubran de forma aislada sin requerir flags adicionales.
