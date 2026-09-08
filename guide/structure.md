# Estructura del proyecto

> Estructura del **backend** — Programa de Gestión de Mejora de Comprensión Lectora (Peñascal).
> Define dónde vive cada cosa y qué puede importar qué. Ante la duda sobre dónde colocar un fichero nuevo, manda este documento. Si hay que crear una carpeta que no aparece aquí, primero se añade aquí y luego se crea.
> La estructura de la interfaz está en `frontend/guides/structure.md`.

---

## 1. Principio de organización

El proyecto se organiza en **capas**, no por tipo de fichero suelto. Cada capa tiene una responsabilidad y solo puede depender de las que están por debajo.

```
API (endpoints)     ->  recibe peticiones, valida formato, devuelve respuestas
    |
Servicios           ->  lógica de negocio: reglas, cálculos, decisiones
    |
Repositorios        ->  acceso a datos: consultas a la base
    |
Modelos             ->  definición de tablas
```

**La regla que no se rompe:** una capa nunca importa de una capa superior. Un endpoint puede llamar a un servicio; un servicio jamás importa un endpoint.

El motivo es práctico, no académico. Cuando la lógica de cálculo del PPM vive en un servicio, se puede probar con `pytest` sin levantar la API ni la base de datos. Cuando vive dentro del endpoint, para probarla hay que montar una petición HTTP completa — y entonces se deja de probar.

---

## 2. Árbol de directorios

El repositorio tiene dos áreas independientes, `backend/` y `frontend/`, cada una con su propio `Dockerfile` y sus propias guías. Este documento cubre `backend/`.

```
comprension-lectora/
├── docker-compose.yml
├── docker-compose.override.yml
├── .env.example
├── scripts/
├── pgadmin/
├── proxy/
├── frontend/                       # ver frontend/guides/structure.md
│
└── backend/
    ├── Dockerfile
    ├── pyproject.toml
    ├── requirements.txt
    ├── requirements-dev.txt
    ├── alembic.ini
    ├── guides/                     # esta documentación
    │   ├── deployment.md
    │   ├── structure.md
    │   ├── testing.md
    │   └── workflow.md
    ├── migrations/
    │   ├── env.py
    │   └── versions/               # una migración por cambio de esquema
    ├── src/
    │   └── app/
    │       ├── __init__.py
    │       ├── main.py             # creación de la app y montaje de routers
    │       ├── config.py           # lectura y validación de variables de entorno
    │       ├── database.py         # motor y sesiones de SQLAlchemy
    │       ├── dependencies.py     # dependencias comunes (sesión, usuario actual)
    │       │
    │       ├── api/
    │       │   ├── router.py       # agrega todos los routers de v1
    │       │   └── v1/
    │       │       ├── auth.py
    │       │       ├── centers.py
    │       │       ├── sections.py
    │       │       ├── students.py
    │       │       ├── tests.py
    │       │       ├── books.py
    │       │       ├── results.py
    │       │       ├── readings.py
    │       │       ├── reports.py
    │       │       └── users.py
    │       │
    │       ├── models/             # tablas (SQLAlchemy)
    │       │   ├── base.py
    │       │   ├── center.py
    │       │   ├── section.py
    │       │   ├── student.py
    │       │   ├── student_section.py
    │       │   ├── test.py
    │       │   ├── result.py
    │       │   ├── book.py
    │       │   ├── read_book.py
    │       │   ├── user.py
    │       │   └── audit_log.py
    │       │
    │       ├── schemas/            # entrada y salida de la API (Pydantic)
    │       │   ├── center.py
    │       │   ├── section.py
    │       │   ├── student.py
    │       │   ├── test.py
    │       │   ├── result.py
    │       │   ├── book.py
    │       │   ├── reading.py
    │       │   ├── user.py
    │       │   └── common.py       # paginación, filtros, errores
    │       │
    │       ├── repositories/       # consultas a la base de datos
    │       │   ├── base.py
    │       │   ├── student_repository.py
    │       │   ├── result_repository.py
    │       │   ├── book_repository.py
    │       │   └── user_repository.py
    │       │
    │       ├── services/           # lógica de negocio
    │       │   ├── student_service.py
    │       │   ├── result_service.py
    │       │   ├── reading_service.py
    │       │   ├── catalog_service.py
    │       │   └── user_service.py
    │       │
    │       ├── analytics/          # métricas y evolución (EP-09)
    │       │   ├── metrics.py      # PPM, porcentaje de aciertos
    │       │   ├── evolution.py    # series temporales
    │       │   └── projection.py   # tendencia y proyección
    │       │
    │       ├── exports/            # salidas (EP-10)
    │       │   ├── excel.py
    │       │   └── report.py
    │       │
    │       ├── importer/           # carga de datos maestros (EP-03)
    │       │   ├── __main__.py     # punto de entrada del servicio "import"
    │       │   ├── parser.py       # lectura y validación del CSV
    │       │   └── loader.py       # alta y actualización idempotente
    │       │
    │       ├── auth/               # autenticación (EP-12)
    │       │   ├── google.py       # flujo OIDC y validación del ID token
    │       │   ├── session.py      # sesiones de servidor
    │       │   └── permissions.py  # comprobación de roles
    │       │
    │       └── core/
    │           ├── exceptions.py   # excepciones propias del dominio
    │           ├── logging.py
    │           └── audit.py        # registro de auditoría (US-49)
    │
    └── tests/
        ├── conftest.py
        ├── unit/
        ├── integration/
        └── fixtures/
```

---

## 3. Decisión importante: el importador no es un proyecto aparte

El diagrama del cliente muestra el servicio `import` con su propio `Dockerfile`. **Recomendación: usar la misma imagen del backend con un comando distinto.**

```yaml
import:
  build: ./backend
  command: ["python", "-m", "app.importer"]
  profiles: ["tools"]
  networks: [db-network]
```

El motivo es directo: el importador y el endpoint de subida de US-10 tienen que validar exactamente igual. Si son dos proyectos con dos copias del código de validación, divergirán — no es una posibilidad, es cuestión de tiempo. Alguien corregirá un caso raro en un sitio y no en el otro, y acabaréis con datos que entran por una vía y son rechazados por la otra.

Con esta estructura, `app/importer/` es un módulo más del backend que reutiliza `services/` y `repositories/`. Un solo sitio donde arreglar las cosas.

Si el cliente exige mantener el contenedor separado, entonces la validación debe extraerse a un paquete compartido; lo que no es aceptable es copiar y pegar.

---

## 4. Qué va en cada capa

### `models/` — las tablas

Definición de tablas con SQLAlchemy. Un fichero por tabla, en singular (`student.py` define `Student`).

Aquí **no** hay lógica de negocio ni cálculos. Un modelo describe cómo se guarda un dato, no qué significa.

### `schemas/` — la frontera de la API

Los objetos Pydantic que entran y salen por HTTP. Separados de los modelos a propósito.

**Nunca devolver un modelo de SQLAlchemy directamente en una respuesta.** Parece un atajo cómodo y es un agujero de seguridad: el día que se añada un campo interno a la tabla `users`, ese campo aparecerá en la respuesta de la API sin que nadie lo decida. El esquema es la lista explícita de lo que sale.

Convención de nombres por operación:

```python
StudentCreate    # lo que se recibe al crear
StudentUpdate    # lo que se recibe al modificar (campos opcionales)
StudentResponse  # lo que se devuelve
StudentDetail    # respuesta ampliada, con relaciones
```

### `repositories/` — el acceso a datos

Todas las consultas viven aquí. Es el único sitio del proyecto donde aparece `select()`, `session.query()` o SQL.

Los repositorios devuelven modelos o datos crudos, y **no deciden nada**: no aplican reglas de negocio ni comprueban permisos.

### `services/` — la lógica de negocio

Aquí vive lo que hace que la aplicación sea esta aplicación y no otra: que un resultado no se pueda duplicar en la misma fecha, que un alumno pendiente de asignación no vea datos, que una prueba con resultados no cambie de código.

Los servicios reciben datos ya validados en formato y devuelven datos o lanzan excepciones de dominio. **No conocen HTTP:** no manejan códigos de estado ni objetos de petición.

### `api/v1/` — los endpoints

Ficheros finos. Un endpoint hace tres cosas: recibir, delegar en un servicio, devolver.

```python
@router.post("/students/{student_id}/results", status_code=201)
async def create_result(
    student_id: UUID,
    payload: ResultCreate,
    service: ResultService = Depends(get_result_service),
    user: User = Depends(require_role("tutor")),
) -> ResultResponse:
    return service.register_result(student_id, payload, user)
```

Si un endpoint pasa de unas quince líneas, es que tiene lógica que pertenece a un servicio.

### `analytics/` — separado a propósito

Métricas, evolución y proyecciones tienen su propia carpeta porque son la parte más propensa a cambiar y la que más necesita pruebas unitarias. Aisladas, se prueban con listas de números, sin base de datos.

---

## 5. Reglas de importación

| Capa | Puede importar de | Nunca importa de |
|---|---|---|
| `api/` | `schemas`, `services`, `dependencies`, `auth` | `repositories`, `models` (para lógica) |
| `services/` | `repositories`, `models`, `analytics`, `core` | `api`, `schemas` |
| `repositories/` | `models`, `database` | `services`, `api`, `schemas` |
| `analytics/` | nada del proyecto salvo `core` | todo lo demás |
| `models/` | `database`, otros `models` | todo lo demás |

`analytics/` sin dependencias es intencional: las funciones de cálculo reciben números y devuelven números. Eso permite probar la proyección de US-34 con una lista de valores inventados y comprobar el resultado a mano.

---

## 6. El layout `src/` y su trampa

Poner el código bajo `backend/src/app/` en lugar de `backend/app/` tiene una ventaja concreta: **las pruebas no pueden importar el código por accidente desde el directorio de trabajo**. Importan el paquete tal y como quedará instalado. Si algo falta en el empaquetado, las pruebas fallan en local, no en producción.

El precio es que hay que configurarlo. En `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "comprension-lectora"
version = "0.1.0"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Y en el `Dockerfile`:

```dockerfile
WORKDIR /app
COPY pyproject.toml requirements.txt ./
RUN apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev \
 && pip install --no-cache-dir -r requirements.txt \
 && apk del .build-deps
COPY src/ ./src/
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**El error habitual con este layout:** `ModuleNotFoundError: No module named 'app'` al ejecutar los tests. La causa casi siempre es que falta `pythonpath = ["src"]` en la configuración de pytest o `PYTHONPATH` en el contenedor. No es un problema de imports mal escritos.

---

## 7. Convenciones de nombres

| Elemento | Convención | Ejemplo |
|---|---|---|
| Ficheros y carpetas | `snake_case` | `result_service.py` |
| Clases | `PascalCase` | `ResultService` |
| Funciones y variables | `snake_case` | `calculate_ppm()` |
| Constantes | `MAYUSCULAS` | `MIN_TESTS_FOR_PROJECTION` |
| Tablas | plural, `snake_case` | `read_books` |
| Modelos | singular | `ReadBook` |
| Rutas de la API | plural, minúscula | `/api/students` |
| Ramas de Git | `feature/US-XX-descripcion` | `feature/US-19-registro-resultados` |

**Idioma:** código, comentarios, nombres de variables y mensajes de commit **en inglés**. Documentación de `guides/`, mensajes de interfaz e informes al cliente **en castellano**. Sin mezclas dentro de un mismo fichero.

Nombres del dominio en inglés, según el esquema que ya entregó el cliente: `student`, `section`, `center`, `test`, `result`, `book`, `read_book`.

---

## 8. Dónde se implementa cada historia

Referencia rápida para no dispersar el trabajo de una historia por medio proyecto:

| Historia | Ficheros principales |
|---|---|
| US-04 Esquema | `models/`, `migrations/versions/` |
| US-07, US-08 Importación | `importer/parser.py`, `importer/loader.py` |
| US-12 a US-15 Pruebas | `api/v1/tests.py`, `services/catalog_service.py` |
| US-16 a US-18 Libros | `api/v1/books.py`, `services/catalog_service.py` |
| US-19 a US-23 Resultados | `api/v1/results.py`, `services/result_service.py` |
| US-24 a US-27 Lecturas | `api/v1/readings.py`, `services/reading_service.py` |
| US-28 Filtrado | `repositories/student_repository.py`, `schemas/common.py` |
| US-31 a US-35 Análisis | `analytics/` |
| US-36 a US-38 Exportación | `exports/`, `api/v1/reports.py` |
| US-43 a US-46 Login | `auth/google.py`, `auth/session.py`, `api/v1/auth.py` |
| US-47, US-48 Permisos | `auth/permissions.py`, `api/v1/users.py` |
| US-49 Auditoría | `core/audit.py`, `models/audit_log.py` |

---

## 9. Contrato con el frontend

El backend expone una única frontera, y esa frontera es un compromiso:

- **Prefijo `/api`** para todo. Nada de la API cuelga fuera de él.
- **Esquemas de respuesta explícitos.** Lo que devuelve un endpoint es lo declarado en `schemas/`, ni un campo más.
- **`401` cuando no hay sesión**, nunca una redirección al login. Redirigir desde el backend rompe cualquier petición hecha por JavaScript.
- **`403` cuando hay sesión pero falta permiso.** Son situaciones distintas y el frontend reacciona distinto a cada una.
- **Errores con forma estable**, definida en `schemas/common.py`, para que la interfaz pueda mostrarlos sin adivinar.

Cambiar cualquiera de estos puntos rompe la interfaz. Se avisa antes de fusionar.

---

## 10. Qué no va al repositorio

```gitignore
.env
*.env
!.env.example
backups/
__pycache__/
*.pyc
.pytest_cache/
.venv/
node_modules/
dist/
*.dump
```

Recordatorio del documento de despliegue: si un secreto llega a subirse, borrarlo en el commit siguiente no sirve de nada. Queda en el historial. **Hay que rotarlo.**

---

*Última actualización: 08/09/2026 · Ver también `deployment.md`, `testing.md` y `workflow.md` de esta carpeta.*