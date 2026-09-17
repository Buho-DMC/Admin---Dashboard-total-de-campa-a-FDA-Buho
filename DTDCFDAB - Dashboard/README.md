# DTDCFDAB - Dashboard

Cliente web en **Streamlit** para el proyecto **Dashboard total de campaña FDA - Buho** (DTDCFDAB).

Diseñado como un cliente delgado (*thin client*): no contiene lógica de negocio del ETL ni credenciales de base de datos de producción; delega todos los cálculos, mutaciones y consultas a `DTDCFDAB - API`.

---

## Características

- **Navegación moderna y segura:** Implementada con `st.navigation` y `st.Page` en `views/`, protegida por un gate de PIN de acceso (`app_password`).
- **Vista unificada de Campañas (`views/campanas.py`):**
  - Selector por nombre real de campaña.
  - Tarjetas de KPIs (folios, ODPs, envíos, % alcanzado, tiempos de respuesta Búho/FDA).
  - Gráfica de línea de tiempo por actividad con marcadores de hitos FDA.
  - Gráfica de distribución de tiempos por responsable.
  - Análisis detallado de fechas (duración de etapas, offset respecto a inicio y desviación vs. promedio histórico de día del mes).
- **Alta de Campañas (`views/alta_de_campana.py`):** Formulario para registrar campañas operativas desde Claw y encolar el job de cálculo inicial.
- **Monitoreo de Jobs (`views/jobs.py`):** Visualización en tiempo real de jobs activos, fallidos y exitosos, con reintento masivo de jobs fallidos en un clic.
- **Metodología y Parámetros (`views/metodologia.py`):** Explicación didáctica de las 7 etapas de la Política D y simulador de parámetros configurables.

---

## Instalación

### Prerrequisitos
- Python 3.11 o superior.
- Instancia en ejecución de `DTDCFDAB - API` (local o en Cloud Run).

### Pasos
1. Crear y activar el entorno virtual dentro de esta carpeta:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # En Windows PowerShell
   ```
2. Instalar dependencias (ubicadas en la raíz del monorepo):
   ```bash
   pip install -r ../requirements.txt
   ```
3. Configurar secretos locales:
   Copiar `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml`:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

---

## Configuración

Variables requeridas en `.streamlit/secrets.toml`:

```toml
api_base_url = "https://dtdc-fda-buho-api-xxxxxxxx.a.run.app"  # O http://localhost:8080 para desarrollo
api_key = "reemplaza-con-el-valor-real-de-API_KEY_DTDC_FDA_BUHO"
app_password = "reemplaza-con-un-pin-de-acceso"
```

---

## Uso

Para iniciar el servidor local de Streamlit:

```bash
streamlit run app.py
```

La aplicación abrirá automáticamente en tu navegador por defecto en `http://localhost:8501`.

---

## Estructura del Código

```text
DTDCFDAB - Dashboard/
├── app.py                  # Punto de entrada, layout wide, gate de PIN y navegación
├── config.py               # Lector tipado de st.secrets
├── api_client.py           # Cliente HTTP hacia DTDCFDAB - API con auth X-API-Key
├── charts.py               # Generación de visualizaciones Plotly (fondo transparente y gridlines)
├── analisis_de_fechas.py   # Métricas de duración, offset y promedio de día del mes
├── views/                  # Páginas registradas en st.navigation (fuera de pages/ para aislar el PIN)
│   ├── campanas.py
│   ├── alta_de_campana.py
│   ├── jobs.py
│   └── metodologia.py
├── tests/                  # Pruebas con streamlit.testing.v1.AppTest y unittest.mock
└── pytest.ini              # Configuración de pruebas (testpaths = tests)
```

---

## Testing

Las pruebas automatizadas validan el renderizado de cada vista, el manejo de errores de la API, el aislamiento del gate de autenticación y las transformaciones de gráficas:

```bash
pytest -v
```
