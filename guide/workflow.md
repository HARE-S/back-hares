# workflow.md — Backend

> Programa de Gestión de Mejora de Comprensión Lectora (Peñascal).
> Cómo se pasa de una historia de usuario a código en `main`.
> El apartado 4 (Git) es **común a todo el equipo** y está duplicado en `frontend/guides/workflow.md`. Si cambia, se cambia en los dos ficheros **en el mismo commit**.

---

## 1. Principios

- **Agilidad y autonomía.** El equipo opera bajo Scrum con sprints de dos semanas, atendiendo daily, planning, review y retrospectiva.

- **Calidad garantizada.** Ninguna funcionalidad se da por terminada sin pruebas. Suelo global del 70% de cobertura, con objetivos por capa en `testing.md`: `analytics/` 95%, `auth/` 90%, `services/` 85%.

- **Seguridad por diseño.** Todo endpoint se evalúa contra la jerarquía de roles **antes** de implementarlo, no después. Manejamos datos de menores: añadir la comprobación de permisos al final es como se olvida en algún endpoint.

- **Colaboración humano-IA.** El agente actúa como experto técnico para arquitectura, generación de pruebas y validación de lógica. **Propone; no decide.** El reparto está en el apartado 5.

- **El contrato es sagrado.** La forma de la API es un compromiso con el equipo de interfaz. Se acuerda antes de escribir código y no se cambia sin avisar.

- **Reparto por historia completa, no por capa.** Quien coge US-19 escribe modelo, repositorio, servicio, endpoint y pruebas. Repartir por capas parece eficiente y no lo es: nadie termina nada sin esperar a los demás, y cada integración revela que los tres entendían la historia de forma distinta.

---

## 2. Proceso para una historia de usuario

### 2.1 Análisis

Leer la historia entera con sus criterios de aceptación **y sus notas del backlog**. Las notas contienen las trampas ya identificadas —la PK de `results`, el `;` final de `tests.csv`, el claim `hd`—. Ignorarlas es repetir un análisis ya hecho.

Identificar las pruebas de integración que validan el flujo completo, incluidos los escenarios de seguridad: acceso sin sesión, acceso con rol insuficiente, acceso a datos de otro centro.

| Quién | Qué hace |
|---|---|
| **Agente** | Propone el plan de pruebas y los escenarios de seguridad |
| **Humano** | Valida el plan. Añade lo que el agente no puede saber: reglas del cliente, decisiones previas |

### 2.2 Descomposición

Dividir la historia en tareas técnicas independientes, con identificador `BE-<historia>-T<n>`:

```
US-19 — Registrar una prueba realizada
├── BE-19-T1  Modelo Result y migración
├── BE-19-T2  ResultRepository con la consulta de histórico
├── BE-19-T3  ResultService: validación y regla de no duplicado
├── BE-19-T4  Endpoint POST /api/students/{id}/results
└── BE-19-T5  Auditoría del registro (US-49)
```

Una tarea debe caber en una jornada. Si no cabe, se parte.

| Quién | Qué hace |
|---|---|
| **Humano** | Descompone y prioriza en el backlog |
| **Agente** | Puede sugerir una descomposición; la decisión es del humano |

### 2.3 Ciclo por tarea

El humano define el inicio y el fin de cada tarea.

**a. Análisis técnico** — impacto en la API y en el modelo de datos. Qué tablas se tocan, qué migración hace falta, qué servicios existentes se reutilizan.

**b. Diseño del contrato** — verbo, ruta, esquema de entrada, esquema de salida, códigos de estado y rol requerido:

```
POST /api/students/{student_id}/results
Rol: tutor (solo sus secciones) | coordinador
Body: ResultCreate { test_id, section_id, test_date, time, successes, mistakes }
201 -> ResultResponse
400 -> valores negativos o referencias inexistentes
403 -> sección ajena al tutor
409 -> duplicado exacto de alumno + prueba + fecha
```

**c. Validación del diseño** — **el humano valida el contrato. No se escribe código sin esta aprobación.** Es el punto más importante del proceso: cambiar un contrato después de implementarlo obliga a rehacer código, pruebas e interfaz.

**d. Implementación**

1. **Migración primero**, si el esquema cambia:
   ```bash
   docker compose run --rm backend alembic revision --autogenerate -m "add results table"
   ```
   Revisar **siempre** lo generado. `--autogenerate` no detecta renombrados: los interpreta como borrar una columna y crear otra, lo que en producción significa perder esos datos.
2. **Modelo → repositorio → servicio → endpoint.** De dentro hacia fuera, respetando las reglas de importación de `structure.md`.
3. **Pruebas unitarias** de la lógica: servicios y `analytics/`.
4. **Pruebas de integración** en `tests/integration/`, usando las fixtures de `conftest.py`.

   Las pruebas se escriben **a la vez** que el código, no al final. Dejarlas para el final produce pruebas que confirman lo que hiciste en lugar de comprobar lo que debía hacer.

   Código, comentarios y nombres **en inglés**. Principios SOLID, con la responsabilidad de cada capa según `structure.md`.

   Todo endpoint lleva `@blp.arguments` y `@blp.response`: sin ellos no aparece en la especificación OpenAPI que consume el equipo de interfaz.

**e. Ejecución y depuración** — siempre dentro del contenedor, contra PostgreSQL:
```bash
docker compose --profile test run --rm backend pytest -x
```
La suite completa, no solo lo tuyo: la tarea no puede romper módulos anteriores.

**f. Validación final de la tarea** — el humano revisa código y resultados y da el visto bueno.

### 2.4 Validación final de la historia

- **Integración total:** suite completa en verde, verificando persistencia real en PostgreSQL y el correcto funcionamiento de **la sesión de servidor** (cookie `HttpOnly`; este proyecto **no usa JWT**, ver US-45).
- **Contrato publicado:** la especificación OpenAPI refleja los cambios. Si algo del contrato cambió respecto a lo acordado, se avisa al equipo de interfaz **antes** de fusionar.
- **Documentación:** si cambió algo de lo escrito en `guides/`, se actualiza en el mismo commit.
- **Sprint review:** se demuestra al cliente sobre el entorno levantado con Docker, no en local.

---

## 3. Definición de terminado

- [ ] Todos los criterios de aceptación se cumplen
- [ ] Pruebas escritas, incluidas las obligatorias de `testing.md` que apliquen
- [ ] Cobertura por encima del umbral de la capa tocada
- [ ] Migración incluida y revisada a mano
- [ ] Permisos comprobados en el servidor, no solo ocultos en la interfaz
- [ ] Especificación OpenAPI actualizada
- [ ] PR aprobada y fusionada a `develop`
- [ ] Funciona en el entorno Docker, no solo en local

Que compile no es que esté terminado. Que funcione en tu máquina, tampoco.

---

## 4. Git *(común a todo el equipo)*

### Ramas

| Rama | Uso |
|---|---|
| `main` | Solo código desplegado o desplegable. Protegida |
| `develop` | Integración del sprint |
| `feature/US-XX-descripcion` | Una rama por historia |
| `fix/descripcion` | Corrección sobre `develop` |
| `hotfix/descripcion` | Urgente: sale de `main` y vuelve a `main` y `develop` |

```bash
git checkout develop && git pull origin develop
git checkout -b feature/US-19-register-test-result
```

Siempre desde `develop` actualizado. Ramificar desde una rama vieja garantiza un conflicto que nadie ha causado.

### Commits

Conventional Commits, **en inglés**:

```
feat(results): add endpoint to register a test result
fix(importer): handle trailing semicolon in tests.csv
test(analytics): cover ppm calculation with zero time
docs(guides): update deployment steps for pgadmin
refactor(services): extract validation from result service
chore(deps): bump sqlalchemy to 2.0.36
```

Tipos: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`, `style`. Un commit, un cambio con sentido propio; nada de `wip`.

### Antes de la Pull Request

```bash
git fetch origin && git rebase origin/develop
ruff check . && ruff format --check .
docker compose --profile test run --rm backend pytest
git push -u origin feature/US-19-register-test-result
```

`rebase` sobre `develop` deja el historial legible y hace que los conflictos aparezcan en tu rama, donde solo te afectan a ti. **Nunca hacer `rebase` de una rama que otra persona ya haya descargado.**

### Plantilla de PR

```markdown
## Historia
US-19 — Registrar una prueba realizada

## Tareas incluidas
BE-19-T1, BE-19-T2, BE-19-T3, BE-19-T4

## Contrato de la API
POST /api/students/{id}/results -> 201 | 400 | 403 | 409

## Criterios de aceptación cubiertos
- [x] Se registran alumno, sección, prueba, fecha, tiempo, aciertos y errores
- [x] Devuelve 201
- [x] Valores negativos devuelven 400

## Cómo probarlo
docker compose --profile test run --rm backend pytest tests/integration/test_results_endpoints.py

## Notas
La sección se guarda en el resultado a propósito (foto del momento).
```

Condiciones para fusionar: tests en verde, `ruff` limpio, cobertura sobre el umbral, migración incluida si toca, sin secretos en el diff, y **aprobada por otra persona**.

**Nadie fusiona su propia PR sin revisión.** Aunque sea una línea, aunque haya prisa. La revisión no está para desconfiar de quien escribe: está para que al menos dos personas conozcan cada parte del sistema.

### Etiquetas

```bash
git tag -a v1.4.0 -m "Sprint 5: registro de resultados y lecturas"
git push origin v1.4.0
```

---

## 5. Colaboración humano-IA

El agente recibe como contexto los cuatro ficheros de `guides/`.

### Reparto de responsabilidad

| Decisión | Quién |
|---|---|
| Contrato de la API (ruta, esquemas, códigos, rol) | **Humano** |
| Modelo de datos y migraciones | **Humano** aprueba; agente propone |
| Descomposición y prioridad de tareas | **Humano** |
| Reglas de permisos por rol | **Humano** |
| Generación de código a partir del contrato | Agente |
| Generación de casos de prueba y escenarios de seguridad | Agente propone; humano valida |
| Refactorización interna sin cambio de contrato | Agente |

La línea es sencilla: **el agente no decide nada que afecte a la seguridad, al esquema o al contrato.**

### Reglas

- **Estas guías mandan sobre lo que proponga el agente.** Si sugiere JWT, `localStorage`, probar contra SQLite, Flask-SQLAlchemy o la sesión por defecto de Flask, está contradiciendo decisiones ya documentadas. Se corrige.
- **Revisar antes de aceptar.** Fallos habituales del código generado: SQL dentro del endpoint, devolver el modelo de SQLAlchemy en lugar del esquema, y saltarse la comprobación de permisos.
- **Nunca pegar datos reales de alumnado en un prompt.** Son datos de menores; para ejemplos están los datos anónimos de US-06.
- **Nunca pegar el `.env`** ni credenciales.
- **Lo que no entiendes, no se fusiona.** Si nadie sabe explicar por qué funciona un fragmento, nadie podrá arreglarlo cuando falle. Y fallará.

Cuando una decisión se toma en conversación con el agente y resulta acertada, se escribe en la guía correspondiente. Si no, se pierde al cerrar la sesión.

---

## 6. Ceremonias

| Cuándo | Qué |
|---|---|
| Diario, 15 min | Qué hice, qué haré, qué me bloquea. Solo eso |
| Inicio de sprint | Selección de historias y estimación conjunta |
| Fin de sprint | Review: demostración al cliente sobre el entorno Docker |
| Fin de sprint | Retrospectiva: qué cambiar la próxima vez |

En la estimación, cuando alguien dice «eso no son 5 puntos, son 13», casi siempre ha visto algo que los demás no. Ese desacuerdo es el motivo de estimar en grupo, y resolverlo antes de programar sale más barato que descubrirlo a mitad de sprint.

---

## 7. Bloqueos

Si algo bloquea más de medio día, se comunica. No se arrastra en silencio hasta la daily del día siguiente.

| Bloqueo | Impacto | Quién lo resuelve |
|---|---|---|
| Acceso a la consola de Google Cloud | EP-12 entera | Cliente / administrador de Workspace |
| Campos de filtrado ausentes en el volcado | US-28 | Cliente |
| Excel de libros sin limpiar | US-18 | Cliente |
| Suscripción a imágenes DHI | Despliegue | Cliente |

Un bloqueo que depende del cliente se escala a Andrés Ocina. No se resuelve inventando una solución provisional que luego nadie recuerda que era provisional.

---

*Última actualización: 08/09/2026 · Ver también `deployment.md`, `structure.md` y `testing.md` de esta carpeta.*
