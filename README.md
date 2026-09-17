# back-hares

Backend de la aplicación HARE-S (Gestión y Catálogo de Pruebas de Lectura y Rendimiento Escolar).

**Stack:** Flask + flask-smorest + SQLAlchemy 2.0 + Alembic + PostgreSQL.

> Este repositorio contiene **solo el backend** (API, modelos, servicios, tests y su `Dockerfile`).
> La orquestación Docker vive en el repo hermano **`../infra-hares`**, el frente web en
> **`../front-hares`** y el proxy de entrada en **`../proxy-hares`**.

## Requisitos para el stack completo

Los 4 repos deben estar como carpetas hermanas:

```text
HARE-S/
├── back-hares/        # este repo
├── front-hares/
├── proxy-hares/
└── infra-hares/       # docker-compose, despliegue
```

## Desarrollo local (con Docker)

La orquestación se ejecuta desde `infra-hares`:

```bash
cd ../infra-hares
cp .env.example .env
docker compose up -d
```

> ⚠️ **No existe `docker compose` en `back-hares`.** Si ejecutas `docker compose ps` aquí verás
> `no configuration file provided`. Para ver los contenedores desde cualquier carpeta usa `docker ps`.
> Guía de comandos: `../infra-hares/guide/comandos.md`.

Documentación del backend: `guide/` (structure, testing, workflow). Despliegue: `../infra-hares/guide/deployment.md`.

## Scripts

| Script | Descripción |
| :--- | :--- |
| `scripts/init_db.py` | Bootstrap del esquema basado en los modelos (dentro del contenedor) |
| `scripts/seed_data.py` | Datos de prueba anónimos |
| `scripts/import_tests.py` | Importación de pruebas desde CSV |

El script orquestador de tests (`run_tests.sh`) vive en `../infra-hares/scripts/`.

## Tecnologías

- [Flask](https://flask.palletsprojects.com/) + [flask-smorest](https://flask-smorest.readthedocs.io/) (API/OpenAPI)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) + [Alembic](https://alembic.sqlalchemy.org/)
- [Gunicorn](https://gunicorn.org/) como servidor WSGI