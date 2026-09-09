# Reparto de historias — Backend

**Programa de Gestión de Mejora de Comprensión Lectora** (Peñascal)
51 historias · 227 puntos · 3 personas
Actualizado: 09/09/2026

---

## 1. Cómo está hecho el reparto

**Por bloques verticales, no por capas.** Cada persona hace su historia entera: modelo, repositorio, servicio, endpoint y pruebas.

Repartir por capas —uno hace modelos, otro servicios, otro endpoints— parece más eficiente y es lo peor que se puede hacer con tres personas: nadie termina nada sin esperar a los demás, todo el mundo bloquea a todo el mundo, y cada integración descubre que los tres entendían la historia de forma distinta.

Cada bloque agrupa historias que comparten tablas y servicios, para que dos personas toquen los mismos ficheros lo menos posible.

---

## 2. Los tres bloques

### Bloque A — Datos, ingesta y segmentación
**Marlen** · 14 historias · 74 puntos

Todo lo que entra al sistema y todo lo que sirve para localizar y agrupar alumnado.

| ID | Título | Pts |
| :--- | :--- | :---: |
| BE-01 | Stack contenedorizado | 5 |
| BE-03 | Esquema inicial versionado | 8 |
| BE-05 | Datos de prueba anónimos | 3 |
| BE-06 | Importar alumnado desde Alexia | 8 |
| BE-07 | Importación idempotente | 5 |
| BE-08 | Informe de errores de importación | 3 |
| BE-09 | Endpoint de subida de fichero | 5 |
| BE-10 | Consulta de centros, secciones y alumnado | 3 |
| BE-17 | Carga inicial del catálogo de libros | 8 |
| BE-27 | Filtrado multicriterio | 5 |
| BE-29 | Búsqueda de alumnos | 3 |
| BE-32 | Comparativa de evolución por grupos | 8 |
| BE-49 | Manual de uso | 2 |
| BE-50 | Alta y modificación manual de alumnado | 8 |

**Tablas propias:** `centers`, `sections`, `students`, `student_sections`
**Módulos propios:** `importer/`, `repositories/student_repository.py`

---

### Bloque B — El aula: catálogos, registro y salidas
**Yeremi** · 22 historias · 76 puntos

Lo que el profesorado usa cada día y lo que sale del sistema hacia pedagogía.

| ID | Título | Pts |
| :--- | :--- | :---: |
| BE-04 | Borrado lógico | 3 |
| BE-11 | Alta de prueba | 3 |
| BE-12 | Importar catálogo de pruebas | 5 |
| BE-13 | Edición y baja de pruebas | 3 |
| BE-14 | Listado paginado de pruebas | 3 |
| BE-15 | Modelo de niveles de libro | 3 |
| BE-16 | Mantenimiento del catálogo de libros | 3 |
| BE-18 | Registrar el resultado de una prueba | 5 |
| BE-19 | Pruebas sucesivas del mismo texto | 3 |
| BE-20 | Consultar resultados de un alumno | 3 |
| BE-21 | Corregir y anular un resultado | 3 |
| BE-22 | Registro en lote | 5 |
| BE-23 | Asignar un libro | 3 |
| BE-24 | Cerrar una lectura | 2 |
| BE-25 | Relectura | 2 |
| BE-26 | Lecturas por alumno y por libro | 3 |
| BE-28 | Ficha del alumno agregada | 3 |
| BE-34 | Detección de alumnos sin progreso | 5 |
| BE-35 | Exportación a Excel | 5 |
| BE-36 | Datos del informe de alumno | 3 |
| BE-37 | Informe de grupo | 5 |
| BE-51 | Historial de pruebas por sección | 3 |

**Tablas propias:** `tests`, `results`, `books`, `read_books`
**Módulos propios:** `services/catalog_service.py`, `result_service.py`, `reading_service.py`, `exports/`

---

### Bloque C — Plataforma: seguridad, análisis y calidad
**Santiago** · 15 historias · 77 puntos

La infraestructura transversal: quién entra, qué puede hacer, y los cálculos.

| ID | Título | Pts |
| :--- | :--- | :---: |
| BE-02 | Configuración por variables de entorno | 3 |
| BE-30 | Métricas derivadas (PPM, eficacia) | 3 |
| BE-31 | Evolución individual | 5 |
| BE-33 | Proyección de evolución | 8 |
| BE-38 | Login con Google (OIDC) | 8 |
| BE-39 | Restricción al dominio corporativo | 5 |
| BE-40 | Sesión de servidor | 5 |
| BE-41 | Alta en el primer acceso | 5 |
| BE-42 | Perfiles de permisos | 8 |
| BE-43 | Gestión de usuarios y roles | 5 |
| BE-44 | Revocación y auditoría | 5 |
| BE-45 | Acceso en entorno de desarrollo | 3 |
| BE-46 | Proyecto en Google Cloud | 3 |
| BE-47 | Pruebas automatizadas | 8 |
| BE-48 | Documentación de la API | 3 |

**Tablas propias:** `users`, `user_sections`, `audit_log`
**Módulos propios:** `auth/`, `analytics/`, `core/audit.py`, `config.py`

> El bloque de seguridad y OIDC es el más cercano a un perfil DevSecOps: validación de tokens, gestión de sesiones, permisos y auditoría. Si a alguien del equipo le interesa esa dirección, es el bloque donde más va a aprender.

---

## 3. Los cuatro contratos de las primeras 48 horas

Aquí está la clave de que nadie se bloquee. **Cuatro piezas que se entregan antes que nada**, aunque estén a medias por dentro, para que los otros dos programen contra ellas.

### Contrato 1 — El esquema (día 1, sesión conjunta)

BE-03 toca tablas de los tres bloques. **No lo hace una persona sola de espaldas a los demás.**

- **Media jornada los tres juntos** revisando el modelo corregido de BE-03: las once tablas, las correcciones al esquema del cliente y las claves foráneas.
- Marlen escribe la migración inicial ese mismo día y la sube.
- A partir de ahí, cada uno crea sus propias migraciones sobre sus tablas.

Sin esta sesión, en la semana 2 descubriréis que dos personas esperaban campos distintos en la misma tabla.

### Contrato 2 — El decorador de permisos (Santiago, día 1)

`@require_role("tutor")` y el objeto de usuario actual, **con una implementación provisional** basada en BE-45: devuelve un usuario simulado con el rol que se le pida.

Marlen y Yeremi lo usan desde el primer endpoint. Cuando Santiago termine BE-40 y BE-42 de verdad, **no tendrán que cambiar una sola línea**: el decorador ya estaba puesto y solo cambia lo que hay dentro.

Sin este contrato, los dos escribirían endpoints sin permisos y habría que repasarlos uno a uno al final — que es exactamente donde se cuela el que se queda abierto.

### Contrato 3 — Las funciones de métricas (Santiago, día 1)

`calculate_ppm()` y `calculate_accuracy()` de BE-30. Son unas veinte líneas sin dependencias, y Yeremi las necesita en cuanto empiece BE-18.

Se entregan el primer día aunque las pruebas se refinen después.

### Contrato 4 — La forma de los errores (los tres, día 1)

`schemas/common.py`: la estructura de la respuesta de error, la de paginación y la de filtros. Un fichero pequeño que los tres van a importar constantemente.

Se acuerda una vez y no se toca sin avisar.

---

## 4. Plan de la primera semana

| Día | Marlen (A) | Yeremi (B) | Santiago (C) |
| :--- | :--- | :--- | :--- |
| **1 mañana** | Sesión conjunta: esquema de BE-03, contratos 2, 3 y 4 | | |
| **1 tarde** | Migración inicial de BE-03 | BE-15 niveles de libro (sin BD) | Contratos 2 y 3 + BE-46 (llamada a Workspace) |
| **2** | BE-01 Docker | BE-11 alta de prueba | BE-02 configuración |
| **3-5** | BE-05, BE-06 | BE-12, BE-16, BE-04 | BE-30, BE-31, BE-38 |

Fíjate en la tarde del día 1: **nadie está parado esperando la migración**. Yeremi trabaja en la enumeración de niveles, que es lógica pura. Santiago entrega los contratos y hace la gestión de Google Cloud, que no es código.

---

## 5. Dependencias que quedan y cómo se sortean

| Quién espera | A quién | Cómo se evita el bloqueo |
| :--- | :--- | :--- |
| Todos | BE-03 esquema | Sesión conjunta el día 1; migración disponible esa tarde |
| Yeremi, Marlen | BE-40/BE-42 permisos | **Contrato 2**: decorador provisional desde el día 1 |
| Yeremi | BE-30 métricas | **Contrato 3**: funciones puras el día 1 |
| Yeremi (BE-18) | BE-10 alumnos | Marlen entrega el `GET` de alumnos en la semana 1; hasta entonces Yeremi usa datos de BE-05 |
| Yeremi (BE-28 ficha) | BE-10 | Compone sobre lo suyo y añade lo de Marlen cuando exista |
| Marlen (BE-32 comparativa) | BE-31 evolución de Santiago | Es de las últimas de Marlen; para entonces BE-31 estará |
| Santiago (BE-47 pruebas) | Todo | Va al final por naturaleza; monta la infraestructura antes |
| Santiago (BE-38/39) | **BE-46 Google Cloud** | **Bloqueo real, externo.** Llamada el día 1 |

**Solo hay un bloqueo que no depende de vosotros: BE-46.** Sin acceso a la consola de Google Cloud del centro, nueve historias de Santiago se paran. Esa llamada se hace el primer día, no la segunda semana.

---

## 6. Puntos de fricción en el repositorio

Trabajando a la vez, estos ficheros los van a tocar los tres. Sin acuerdo, os pasaréis el sprint resolviendo conflictos.

| Fichero | Riesgo | Acuerdo |
| :--- | :--- | :--- |
| `api/__init__.py` | Los tres registran blueprints | Una línea por blueprint, en orden alfabético. Commits pequeños y frecuentes |
| `models/__init__.py` | Los tres añaden modelos | Igual: una línea por modelo, orden alfabético |
| `migrations/versions/` | **El peor.** Alembic encadena revisiones por `down_revision` | Ver abajo |
| `schemas/common.py` | Forma de errores y paginación | Contrato 4: se acuerda el día 1 y no se toca sin avisar |
| `requirements.txt` | Tres personas añadiendo dependencias | Ordenado alfabéticamente; una dependencia por línea |

### Migraciones de Alembic

Es la fricción más molesta y conviene tener la regla clara: **`git pull` justo antes de generar una migración**. Alembic encadena cada revisión con la anterior; si dos personas generan a partir de la misma cabeza, la cadena se bifurca.

Si aun así pasa: **no se arregla el fichero a mano**. Se borra la migración propia, se hace `pull` y se regenera. Editar los identificadores de revisión a mano acaba en un esquema que funciona en una máquina y no en otra.

---

## 7. Reglas para que el reparto funcione

**Nadie toca el bloque de otro sin avisar.** Si Yeremi necesita un cambio en `student_repository.py`, lo pide; no lo hace él. Dos personas editando el mismo servicio a la vez es garantía de conflicto.

**Los contratos son sagrados.** Si Santiago cambia la firma de `@require_role`, rompe el código de los otros dos a la vez. Cualquier cambio en las cuatro piezas del apartado 3 se avisa antes de fusionar.

**Fusionar a `develop` a diario**, aunque la historia no esté terminada, mientras las pruebas pasen. Una rama que vive dos semanas acumula conflictos que ya no se resuelven, se rehacen.

**Revisión cruzada.** Nadie fusiona su propia PR. Y conviene rotar quién revisa a quién, o cada uno acabará conociendo solo su tercio del sistema.

---

## 8. Equilibrio del reparto

| Persona | Historias | Puntos | Reparto |
| :--- | :---: | :---: | :---: |
| Marlen (A) | 14 | 74 | 32,6% |
| Yeremi (B) | 22 | 76 | 33,5% |
| Santiago (C) | 15 | 77 | 33,9% |
| **Total** | **51** | **227** | |

El bloque B tiene más historias porque las suyas son más pequeñas. En puntos, los tres están a menos de tres de diferencia.

**Los puntos son una estimación previa, no un reparto de trabajo garantizado.** Revisadlo en la retrospectiva del primer sprint: si alguien va muy por delante o muy por detrás, se mueven historias entre bloques. Las que menos cuesta mover son las de análisis y salidas (BE-31 a BE-37), porque dependen poco del resto.

---

*Ver `US/INDEX.md` para el detalle de cada historia y `guides/workflow.md` para el proceso de trabajo.*
