# Admin — Dashboard total de campaña FDA - Buho (DTDCFDAB)

Monorepo del sistema de seguimiento y análisis de campañas operativas FDA de Búho.

Sustituye por completo el pipeline y dashboard legacy basado en Google Sheets (`[Direccion] Reporte proceso total de campaña`), ofreciendo persistencia relacional en MySQL, cálculo automatizado mediante una API asíncrona en Cloud Run y visualización interactiva en Streamlit.

---

## 🏛️ Arquitectura del Monorepo

El proyecto está organizado en tres submódulos desacoplados:

| Módulo | Directorio | Tecnología | Propósito |
| :--- | :--- | :--- | :--- |
| **DB** | `DTDCFDAB - DB/` | MySQL, SQLAlchemy 2.0, Alembic | Esquema relacional en `dmc-general` (Digital Ocean) con tablas con prefijo `dtdcfdab_*`. |
| **API** | `DTDCFDAB - API/` | FastAPI, Pydantic, Pandas, Cloud Tasks | Backend REST y motor de cálculo de la Política D. Consume Retool y Claw, y persiste snapshots en DB. |
| **Dashboard** | `DTDCFDAB - Dashboard/` | Streamlit, Plotly | Interfaz de usuario interactiva y cliente delgado sin acceso directo a base de datos. |

```text
               ┌─────────────┐       ┌─────────────┐
               │ Retool APIs │       │ Claw WMS    │
               └──────┬──────┘       └──────┬──────┘
                      │                     │
                      ▼                     ▼
               ┌───────────────────────────────────┐
               │        DTDCFDAB - API             │ ◄─────── Cloud Tasks
               │      (FastAPI en Cloud Run)       │          (Jobs asíncronos)
               └──────┬─────────────────────┬──────┘
                      │                     │
                      ▼                     ▼
          ┌───────────────────────┐   ┌───────────────────────────┐
          │     DTDCFDAB - DB     │   │   DTDCFDAB - Dashboard    │
          │ (MySQL `dmc-general`) │   │ (Streamlit Community Cl.) │
          └───────────────────────┘   └───────────────────────────┘
```

---

## 🚀 Inicio Rápido por Submódulo

Cada submódulo cuenta con su propio entorno virtual y dependencias independientes:

### 1. Base de Datos (`DTDCFDAB - DB`)
```bash
cd "DTDCFDAB - DB"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
cp .env.example .env
alembic upgrade head
pytest -v
```
*Detalle completo en:* [`DTDCFDAB - DB/README.md`](file:///C:/Users/Karim%20Acuna/OneDrive/Desktop/Programs/2026/%5BAdmin%5D%20Dashboard%20total%20de%20campa%C3%B1a%20FDA%20-%20Buho/DTDCFDAB%20-%20DB/README.md).

### 2. Backend API (`DTDCFDAB - API`)
```bash
cd "DTDCFDAB - API"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
python main.py
pytest -v
```
*Detalle completo en:* [`DTDCFDAB - API/README.md`](file:///C:/Users/Karim%20Acuna/OneDrive/Desktop/Programs/2026/%5BAdmin%5D%20Dashboard%20total%20de%20campa%C3%B1a%20FDA%20-%20Buho/DTDCFDAB%20-%20API/README.md).

### 3. Dashboard Web (`DTDCFDAB - Dashboard`)
```bash
cd "DTDCFDAB - Dashboard"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
pytest -v
```
*Detalle completo en:* [`DTDCFDAB - Dashboard/README.md`](file:///C:/Users/Karim%20Acuna/OneDrive/Desktop/Programs/2026/%5BAdmin%5D%20Dashboard%20total%20de%20campa%C3%B1a%20FDA%20-%20Buho/DTDCFDAB%20-%20Dashboard/README.md).

---

## 🧪 Pruebas Automatizadas

El monorepo cuenta con una suite integral de **253 pruebas automatizadas**:

- **Dashboard (101 tests):** Pruebas funcionales de renderizado de vistas (`AppTest`), componentes Plotly y resiliencia ante errores de red.
- **API (139 tests):** Cobertura exhaustiva de routers, validación Pydantic, cálculo de los 14 hitos y 13 métricas de la Política D con mocks SQLite y fixtures.
- **DB (13 tests):** Pruebas de integración sobre MySQL real verificando constraints, cascadas y semillas de configuración bajo aislamiento transaccional.

---

## 📚 Especificaciones y Diseño Técnico

Todo el diseño de arquitectura, requerimientos y planes de ejecución se encuentra documentado bajo el estándar Superpowers:

- **Diseño de la API:** `docs/superpowers/specs/2026-09-08-api-design.md`
- **Diseño del Snapshot (Política D):** `docs/superpowers/specs/2026-09-09-snapshot-campana-design.md`
- **Diseño del Dashboard:** `docs/superpowers/specs/2026-09-09-dtdcfdab-dashboard-design.md`
- **Gate de PIN y Vistas Seguras:** `docs/superpowers/specs/2026-09-13-gate-login-dashboard-design.md`
- **Fusión Unificada de Campañas:** `docs/superpowers/specs/2026-09-13-campana-unificada-design.md`
- **Hitos FDA y Día del Mes:** `docs/superpowers/specs/2026-09-13-campana-ajustes-fechas-milestones-design.md`

---

## 📏 Estándares del Proyecto

El desarrollo de este monorepo se rige bajo los estándares organizacionales de Búho:
- **Estándares locales:** `C:\Users\Karim Acuna\OneDrive\Desktop\Programs\CLAUDE\Standards`
- **Orquestación y reglas globales:** [`AGENTS.md`](file:///C:/Users/Karim%20Acuna/OneDrive/Desktop/Programs/2026/%5BAdmin%5D%20Dashboard%20total%20de%20campa%C3%B1a%20FDA%20-%20Buho/AGENTS.md)
- **Convenciones de código:** Comillas simples en Python, docstrings Google-style obligatorios, nombres descriptivos sin abreviar y autoría humana estricta en Git.
