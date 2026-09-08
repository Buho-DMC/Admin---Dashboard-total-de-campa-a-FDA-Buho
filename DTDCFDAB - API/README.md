# DTDCFDAB - API

API interna del proyecto de campañas FDA: hace el ETL (Política D), habla con Retool/Claw/MySQL,
y expone endpoints para que el Dashboard (Streamlit, cliente delgado) los consuma.

## Instalación

### Prerrequisitos
- Python 3.12
- Los 5 secrets `MYSQL_*_DMC_GENERAL` (ver `.env.example`)

### Pasos
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env  # llenar con las credenciales reales
```

## Uso

```bash
python main.py
```

Corre en `http://localhost:8080`. Todos los endpoints salvo `GET /health` requieren el header
`X-API-Key`.

## Configuración

Ver `.env.example` — todas las variables son obligatorias salvo que se indique lo contrario en
`src/config.py`.

## Testing

```bash
pytest -v
```
