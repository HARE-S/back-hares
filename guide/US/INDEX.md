# Índice de Historias de Usuario — Backend

**Programa de Gestión de Mejora de Comprensión Lectora** (Peñascal)
Equipo: Marlen Álvarez, Santiago Patiño, Yeremi Peralta · Coordinación: Andrés Ocina
**Stack:** Flask + flask-smorest + SQLAlchemy 2.0 + Alembic + PostgreSQL + Gunicorn
51 historias · 227 puntos · Actualizado: 09/09/2026
**Reparto entre el equipo:** ver [REPARTO.md](REPARTO.md)

---

## Convenciones

- **IDs:** `BE-01` a `BE-49`, numeración consecutiva propia del backend.
- **Tareas:** `T-BE<historia>-<n>`, por ejemplo `T-BE18-03`.
- **Estados:** Pendiente · En curso · En revisión · Completado · Bloqueado
- Una historia nueva se crea a partir de `_PLANTILLA.md` y se añade a este índice.

---

## Listado completo

| ID | Título | Puntos | Prioridad | Estado |
| :--- | :--- | :---: | :--- | :--- |
| **Infraestructura** | | | | |
| [BE-01](BE-01-stack-contenedorizado.md) | Stack contenedorizado del backend | 5 | Crítica | Pendiente |
| [BE-02](BE-02-variables-entorno.md) | Configuración por variables de entorno | 3 | Alta | Completado |

| **Modelo de datos** | | | | |
| [BE-03](BE-03-esquema-inicial.md) | Esquema inicial versionado con migraciones | 8 | Crítica | Pendiente |
| [BE-04](BE-04-borrado-logico.md) | Borrado lógico de pruebas y libros | 3 | Alta | Completado |
| [BE-05](BE-05-datos-anonimos.md) | Datos de prueba anónimos | 3 | Alta | Pendiente |
| **Importación de datos maestros** | | | | |
| [BE-06](BE-06-importar-alumnado.md) | Importar alumnado desde el volcado de Alexia | 8 | Crítica | Pendiente |
| [BE-07](BE-07-importacion-idempotente.md) | Importación idempotente | 5 | Crítica | Pendiente |
| [BE-08](BE-08-informe-errores-importacion.md) | Informe de errores de importación | 3 | Media | Pendiente |
| [BE-09](BE-09-endpoint-subida-fichero.md) | Endpoint de subida del fichero | 5 | Alta | Pendiente |
| [BE-10](BE-10-consulta-centros-secciones.md) | Consulta de centros, secciones y alumnado | 3 | Alta | Pendiente |
| **Catálogo de pruebas** | | | | |
| [BE-11](BE-11-alta-prueba.md) | Alta de prueba en el catálogo | 3 | Alta | Completado |
| [BE-12](BE-12-importar-catalogo-pruebas.md) | Importar el catálogo de pruebas | 5 | Alta | Pendiente |
| [BE-13](BE-13-edicion-baja-pruebas.md) | Edición y baja de pruebas | 3 | Media | Pendiente |
| [BE-14](BE-14-listado-pruebas.md) | Listado paginado y filtrado de pruebas | 3 | Media | Pendiente |
| **Catálogo de libros** | | | | |
| [BE-15](BE-15-niveles-libro.md) | Modelo de niveles de libro | 3 | Alta | Completado |
| [BE-16](BE-16-mantenimiento-libros.md) | Alta y mantenimiento del catálogo de libros | 3 | Alta | Pendiente |
| [BE-17](BE-17-carga-inicial-libros.md) | Carga inicial del catálogo de libros | 8 | Media | Pendiente |
| **Registro de resultados** | | | | |
| [BE-18](BE-18-registrar-resultado.md) | Registrar el resultado de una prueba | 5 | **Crítica** | Completado |
| [BE-19](BE-19-pruebas-sucesivas.md) | Pruebas sucesivas del mismo texto | 3 | **Crítica** | Completado |
| [BE-20](BE-20-consultar-resultados-alumno.md) | Consultar los resultados de un alumno | 3 | Crítica | Completado |
| [BE-21](BE-21-corregir-anular-resultado.md) | Corregir y anular un resultado | 3 | Alta | Completado |
| [BE-22](BE-22-registro-lote.md) | Endpoint de registro en lote | 5 | Alta | Completado |
| **Registro de lecturas** | | | | |
| [BE-23](BE-23-asignar-libro.md) | Asignar un libro a un alumno | 3 | Alta | Completado |
| [BE-24](BE-24-cerrar-lectura.md) | Cerrar una lectura | 2 | Alta | Completado |
| [BE-25](BE-25-relectura.md) | Relectura de un libro | 2 | Media | Completado |
| [BE-26](BE-26-lecturas-por-alumno-y-libro.md) | Consulta de lecturas por alumno y por libro | 3 | Media | Completado |
| **Consulta y filtrado** | | | | |
| [BE-27](BE-27-filtrado-multicriterio.md) | Filtrado multicriterio del alumnado | 5 | Alta | **Bloqueada** |
| [BE-28](BE-28-ficha-alumno-agregada.md) | Endpoint agregado de la ficha del alumno | 3 | Alta | Completado |
| [BE-29](BE-29-busqueda-alumnos.md) | Búsqueda de alumnos | 3 | Media | Pendiente |
| **Análisis y evolución** | | | | |
| [BE-30](BE-30-metricas-derivadas.md) | Métricas derivadas de comprensión lectora | 3 | Crítica | Completado |
| [BE-31](BE-31-evolucion-individual.md) | Evolución individual de un alumno | 5 | Alta | Completado |
| [BE-32](BE-32-comparativa-grupos.md) | Comparativa de evolución por grupos | 8 | Media | Pendiente |
| [BE-33](BE-33-proyeccion-evolucion.md) | Proyección de evolución | 8 | Media | En revisión |
| [BE-34](BE-34-alumnos-sin-progreso.md) | Detección de alumnos sin progreso | 5 | Baja | Pendiente |
| **Exportación e informes** | | | | |
| [BE-35](BE-35-exportacion-excel.md) | Exportación de datos a Excel | 5 | Alta | Pendiente |
| [BE-36](BE-36-datos-informe-alumno.md) | Datos del informe individual de alumno | 3 | Media | Pendiente |
| [BE-37](BE-37-informe-grupo.md) | Informe agregado de grupo | 5 | Media | Pendiente |
| **Seguridad y acceso** | | | | |
| [BE-38](BE-38-login-google.md) | Inicio de sesión con cuenta de Google | 8 | Crítica | Pendiente |
| [BE-39](BE-39-restriccion-dominio.md) | Restricción al dominio corporativo | 5 | **Crítica** | Pendiente |
| [BE-40](BE-40-sesion-servidor.md) | Sesión de servidor | 5 | Crítica | Pendiente |
| [BE-41](BE-41-alta-primer-acceso.md) | Alta de usuario en el primer acceso | 5 | Alta | Pendiente |
| [BE-42](BE-42-perfiles-permisos.md) | Perfiles de permisos por rol | 8 | Alta | Pendiente |
| [BE-43](BE-43-gestion-usuarios-roles.md) | Gestión de usuarios y asignación de roles | 5 | Alta | Pendiente |
| [BE-44](BE-44-revocacion-auditoria.md) | Revocación de acceso y auditoría | 5 | Media | Pendiente |
| [BE-45](BE-45-acceso-desarrollo.md) | Acceso en entorno de desarrollo | 3 | Alta | Completado |
| [BE-46](BE-46-proyecto-google-cloud.md) | Configuración del proyecto en Google Cloud | 3 | Crítica | **Bloqueada** |
| **Calidad y entrega** | | | | |
| [BE-47](BE-47-pruebas-automatizadas.md) | Batería de pruebas automatizadas | 8 | Alta | Pendiente |
| [BE-48](BE-48-documentacion-api.md) | Documentación de la API | 3 | Alta | Pendiente |
| [BE-49](BE-49-manual-usuario.md) | Manual de uso de las funciones de servidor | 2 | Media | Pendiente |
| **Añadidas tras revisión del cliente (09/09)** | | | | |
| [BE-50](BE-50-crud-manual-alumnado.md) | Alta y modificación manual de alumnado | 8 | Alta | Pendiente |
| [BE-51](BE-51-historial-por-seccion.md) | Historial de pruebas por sección | 3 | Media | Completado |
| | **Total** | **227** | | |

---

## Equivalencia con el backlog compartido

La numeración `BE-XX` es propia del backend. El backlog que ve el cliente y el de la interfaz usan la numeración `US-XX` original. Esta tabla mantiene la trazabilidad:

| BE | US | | BE | US | | BE | US |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BE-01 | US-01 | | BE-18 | US-19 | | BE-35 | US-36 |
| BE-02 | US-03 | | BE-19 | US-20 | | BE-36 | US-37 |
| BE-03 | US-04 | | BE-20 | US-21 | | BE-37 | US-38 |
| BE-04 | US-05 | | BE-21 | US-22 | | BE-38 | US-43 |
| BE-05 | US-06 | | BE-22 | US-23 | | BE-39 | US-44 |
| BE-06 | US-07 | | BE-23 | US-24 | | BE-40 | US-45 |
| BE-07 | US-08 | | BE-24 | US-25 | | BE-41 | US-46 |
| BE-08 | US-09 | | BE-25 | US-26 | | BE-42 | US-47 |
| BE-09 | US-10 | | BE-26 | US-27 | | BE-43 | US-48 |
| BE-10 | US-11 | | BE-27 | US-28 | | BE-44 | US-49 |
| BE-11 | US-12 | | BE-28 | US-29 | | BE-45 | US-50 |
| BE-12 | US-13 | | BE-29 | US-30 | | BE-46 | US-51 |
| BE-13 | US-14 | | BE-30 | US-31 | | BE-47 | US-52 |
| BE-14 | US-15 | | BE-31 | US-32 | | BE-48 | US-53 |
| BE-15 | US-16 | | BE-32 | US-33 | | BE-49 | US-54 |
| BE-16 | US-17 | | BE-33 | US-34 | | | |
| BE-17 | US-18 | | BE-34 | US-35 | | | |

`US-02` (proxy), `US-39` a `US-42` (navegación, formularios, gráficos, tableta) son exclusivas de la interfaz y no tienen equivalente aquí.

---

## Planificación por sprints

| Sprint | Historias | Puntos | Objetivo demostrable |
| :--- | :--- | :---: | :--- |
| **1 — Cimientos** | BE-01, BE-02, BE-03, BE-04, BE-05, BE-46 | 25 | El stack levanta con datos anónimos |
| **2 — Identidad** | BE-38, BE-39, BE-40, BE-41, BE-45, BE-48 | 29 | La API rechaza a quien no sea del dominio |
| **3 — Datos maestros** | BE-06, BE-07, BE-08, BE-09, BE-10 | 24 | Se importa el CSV de Alexia |
| **4 — Catálogos y permisos** | BE-11 a BE-17, BE-42, BE-43 | 41 | Pruebas y libros con roles operativos |
| **5 — Núcleo** | BE-18 a BE-26, BE-30 | 32 | Resultados y lecturas con métricas |
| **6 — Análisis** | BE-27, BE-28, BE-29, BE-31, BE-32 | 24 | Filtrado y evolución |
| **7 — Salidas** | BE-33, BE-35, BE-36, BE-37, BE-47 | 29 | Exportación e informes |
| **8 — Cierre** | BE-34, BE-44, BE-49, BE-51 | 15 | Auditoría, historial de grupo y documentación |

**BE-50** se sitúa en el Sprint 3 o 4, junto a la importación y los permisos, en cuanto el cliente confirme la política de conflictos.

**La autenticación va en el Sprint 2 a propósito.** Cada endpoint escrito después nace ya protegido. Dejarla para el final obliga a repasar todos los endpoints uno a uno, y ahí es donde se cuela el que se quedó abierto.

---

## Historias que corrigen errores del esquema entregado

Cuatro historias existen porque el modelo de datos del cliente tenía defectos que impedían cumplir el objetivo del proyecto:

| Historia | Qué corrige |
| :--- | :--- |
| **BE-19** | PK de `results` era `(student_id, section_id)` → impedía pruebas sucesivas. **Sin esta corrección el proyecto no cumple su objetivo.** |
| **BE-25** | PK de `read_books` era `(student_id, book_id)` → impedía releer un libro |
| **BE-16** | `books` traía `student_id` → mezclaba catálogo con relación |
| **BE-15** | `level int not null` → los niveles reales no son enteros |

Y dos existen por ausencias en el esquema: **BE-07** (sin `external_id` no hay reimportación posible) y **BE-27** (sin los campos de perfil no hay filtrado).

---

## Historias que desbloquean la interfaz

| Backend | Desbloquea |
| :--- | :--- |
| BE-48 (OpenAPI) | **Todo.** Es la fuente de tipos del frontend |
| BE-40 (sesión, `401`) | Manejo de sesión caducada |
| BE-10 (centros/secciones) | Navegación |
| BE-28 (ficha agregada) | Pantalla de ficha del alumno |
| BE-22 (lote) | Pantalla de registro en lote |
| BE-31 a BE-33 (análisis) | Gráficos de evolución y comparativa |
| BE-35 (Excel) | Botón de exportación |

---

## Bloqueos vigentes

| Historia | Bloqueo | Quién lo resuelve |
| :--- | :--- | :--- |
| **BE-46** | Acceso a la consola de Google Cloud. **Bloquea toda la épica de seguridad** | Administrador de Workspace del centro |
| **BE-27** | Los campos de perfil no existen en el volcado de Alexia | Cliente |
| BE-17 | El Excel de libros necesita limpieza manual previa | Cliente |
| BE-33 | "Proyecciones de evolución" sin definir | Equipo de pedagogía |
| BE-01 | Suscripción a imágenes DHI sin confirmar | Cliente |
| BE-09 | `import` como job puntual o mecanismo permanente | Cliente |
| BE-12 | Significado de F/L en los códigos de prueba | Equipo de pedagogía |
| **BE-50** | Contradicción entre el papel (pide CRUD manual) y la especificación de API (solo `GET`). Falta definir qué prevalece ante conflicto con Alexia | Cliente |

Los bloqueos que dependen del cliente se escalan a Andrés Ocina.

---

*Ver `guides/structure.md`, `guides/testing.md`, `guides/deployment.md` y `guides/workflow.md`*
