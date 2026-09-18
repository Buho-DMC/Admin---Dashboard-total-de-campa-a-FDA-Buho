# MATRIZ DE BRECHAS Y CUMPLIMIENTO DE ESTÁNDARES (STANDARDS_GAP)
**Proyecto:** Dashboard Total de Campaña FDA - Buho  
**Fecha de auditoría:** 2026-09-18  
**Repositorio de estándares base:** `Standards/` (v1.0)

---

## 1. Resumen Ejecutivo de Cumplimiento

La auditoría técnica integral del monorepo `[Admin] Dashboard total de campaña FDA - Buho` arrojó un **alto nivel de alineación arquitectónica y de calidad** (259/259 pruebas automatizadas pasando exitosamente). Los tres módulos (`DTDCFDAB - DB`, `DTDCFDAB - API` y `DTDCFDAB - Dashboard`) respetan la separación estricta de responsabilidades, cuarentena de secretos, tipado estricto y convenciones de base de datos.

Las pocas desviaciones identificadas fueron formalmente documentadas, justificadas técnicamente y aprobadas durante la compuerta de alineación de la Fase 2.

```
Total de Estándares Evaluados: 11
- Cumple Plenamente:             8 (72.7%)
- Desviación Justificada:        3 (27.3%)
- Brechas Críticas Pendientes:   0 (0.0%)
```

---

## 2. Matriz de Cumplimiento por Estándar

| Estándar | Categoría | Estado | Resumen / Hallazgos |
| :--- | :--- | :---: | :--- |
| `general/project-audit.md` | General | **Cumple** | Proceso de auditoría ejecutado rigurosamente en 5 fases: Discovery objetivo (`discovery.md`), auditoría emparejada, compuerta de alineación (`preguntas_proyecto.txt`), refactor cosmético seguro (<120 caracteres) y documentación maestra (`docs/ARQUITECTURA.md`). |
| `general/documentation.md` | General | **Cumple** | `README.md` exhaustivo y sincronizado, `SKILL.md` normalizados en los tres submódulos y `docs/ARQUITECTURA.md` con las 7 secciones canónicas y diagramas Mermaid válidos. |
| `general/security.md` | General | **Cumple** | Cuarentena total de credenciales. No existen contraseñas, URLs de bases de datos ni llaves de API hardcodeadas en código fuente. Solo existen `.env.example` y `secrets.toml.example` en Git. |
| `general/git-workflow.md` | General | **Desviación Justificada** | (1) Rama única `main` sin `develop` (proyecto mantenido por un único ingeniero). (2) Exclusiones de IA en `.git/info/exclude` en vez de `.gitignore` para invisibilidad absoluta hacia clones públicos. |
| `general/database.md` | General | **Cumple** | Nombres canónicos de tablas (`dtdcfdab_*`), claves primarias explícitas `id_<entidad>`, campos en snake_case sin abreviaciones crípticas, migraciones Alembic deterministas y modelos SQLAlchemy 2.0 tipados. |
| `general/deployment.md` | General | **Cumple** | Despliegue en Cloud Run orquestado por Cloud Build con triggers filtrados por ruta, secretos inyectados desde Secret Manager y salida de red por NAT con IP estática fija. |
| `general/skill-template.md` | General | **Cumple** | Archivos `SKILL.md` estandarizados en `DTDCFDAB - DB`, `DTDCFDAB - API` y `DTDCFDAB - Dashboard` bajo la plantilla corporativa oficial. |
| `python/code-standards.md` | Python | **Desviación Justificada** | Uso estricto y consistente de comillas simples (`'`) en lugar de comillas dobles (decisión de equipo documentada en `AGENTS.md` §9). Líneas de código limitadas a <= 120 caracteres tras refactor cosmético. |
| `python/functions.md` | Python | **Cumple** | Tipado estricto con `typing`, type hints en argumentos y retornos, docstrings Google-style obligatorios en funciones públicas y no utilización de variables de una sola letra ni abreviaciones crípticas. |
| `python/fastapi.md` | Python | **Cumple** | Routers modulares (`APIRouter`), esquemas Pydantic V2 para validación de entrada/salida, inyección de dependencias (`Depends`), códigos HTTP semánticos (201, 404, 409, 422) y autenticación mediante middleware/dependencia API Key. |
| `python/pytest.md` | Python | **Desviación Justificada** | El módulo `DTDCFDAB - Dashboard` no posee un `requirements.txt` local propio; depende del `requirements.txt` ubicado en la raíz del monorepo para no quebrar el build de Streamlit Community Cloud (Commit `7e2035d`). |

---

## 3. Catálogo Detallado de Desviaciones Justificadas

### Desviación 1: Rama Única `main` y Flujo Git Simplificado
- **Estándar:** `Standards/general/git-workflow.md` §2 (Flujo de ramas `main` / `develop` / `feature/*`).
- **Estado:** Desviación Justificada.
- **Razón Técnica:** Proyecto operado y mantenido por un único desarrollador líder en producción directa. Mantener ramas de sincronización intermedias (`develop`) agregaba fricción innecesaria sin aportar beneficios de concurrencia de equipo.
- **Mitigación:** Cada cambio pasa por una compuerta estricta de ejecución de tests unitarios locales (259 tests) y validación de sintaxis antes de mergear a `main`.

### Desviación 2: Aislamiento de Artefactos IA en `.git/info/exclude`
- **Estándar:** `Standards/general/git-workflow.md` §7 (Uso de `.gitignore` para exclusiones globales).
- **Estado:** Desviación Justificada (Decisión explícita en `AGENTS.md` §1 y §9).
- **Razón Técnica:** Se busca invisibilidad absoluta de las herramientas de orquestación de IA (`AGENTS.md`, `SKILL.md`, `discovery.md`, `preguntas_proyecto.txt`, etc.) para que el repositorio público y compartido no contenga rastros ni menciones en `.gitignore`.
- **Trade-off:** `.git/info/exclude` es local y no viaja al clonar. Si se clona en otra máquina, se debe regenerar el bloque de exclusiones localmente.

### Desviación 3: Ubicación Centralizada de `requirements.txt` para el Dashboard
- **Estándar:** `Standards/general/project-audit.md` y estructura de submódulos independientes.
- **Estado:** Desviación Justificada (Decisión de Alineación 3A).
- **Razón Técnica:** Streamlit Community Cloud requiere que el archivo de dependencias resida en la raíz del repositorio cuando el archivo principal se especifica como ruta relativa (`DTDCFDAB - Dashboard/app.py`). En el commit `7e2035d` se eliminó el archivo interno duplicado para erradicar conflictos de resolución de paquetes durante el despliegue automático.
- **Mitigación:** El `requirements.txt` de la raíz está rigurosamente documentado y sincronizado con las dependencias exactas que utiliza el Dashboard.

### Desviación 4: Convención de Comillas Simples en Python
- **Estándar:** `Standards/python/code-standards.md` (recomienda comillas dobles al estilo Black).
- **Estado:** Desviación Justificada (Decisión explícita en `AGENTS.md` §9).
- **Razón Técnica:** Consistencia estilística preexistente en todo el backend y pruebas del proyecto. Se estandarizó el 100% del código a comillas simples (`'`) para uniformidad estética.

---

## 4. Acciones y Mejoras Continuas Recomendadas (Roadmap)

1. **Migración de Event Handlers en FastAPI:**
   - Actualmente `main.py` en `DTDCFDAB - API` utiliza `@app.on_event('startup')`, lo cual emite un `DeprecationWarning` en versiones recientes de FastAPI.
   - *Recomendación:* Migrar a la sintaxis moderna de `lifespan` context manager (`asynccontextmanager`) en el próximo ciclo de mantenimiento técnico.
2. **Reemplazo del Adapter Datetime en SQLite (Tests):**
   - Python 3.12+ emite advertencias sobre el adaptador por defecto de datetime en SQLite utilizado en tests en memoria.
   - *Recomendación:* Registrar un converter/adapter explícito de ISO 8601 en `conftest.py`.
3. **Mapeo Tipado de Percentiles en Frontend:**
   - Mantener actualizada la definición de llaves del JSON de `distribucion_percentiles` si se incorporan nuevas etapas operativas más allá de Pick & Pack y Entregas.
