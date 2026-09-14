# Seguimiento de Tareas — Yeremi (Bloque B)

**Bloque B — El aula: catálogos, registro y salidas**
* **Responsable:** Yeremi (22 historias · 76 puntos · 100% completado).
* **Propósito:** Todo lo que el profesorado usa en el aula en el día a día y los reportes hacia pedagogía y dirección.
* **Tablas asignadas:** `tests`, `results`, `books`, `readed_books`.
* **Módulos y servicios:** `app/services/catalog_service.py`, `app/services/result_service.py`, `app/services/reading_service.py`, `app/analytics/`, `app/exports/`.

---

## 🏷️ Convenciones de Commits en Inglés por Apartado

Para mantener consistencia en Git y un historial limpio y estructurado, los commits en inglés se organizan según los 4 apartados:

| Apartado | Rama sugerida | Scope del Commit | Formato / Ejemplos |
| :--- | :--- | :--- | :--- |
| **1. Catálogos y Modelo Base** | `catalogs` | `catalogs` / `books` | `feat(catalogs): import test catalog from csv (BE-12)`<br>`feat(books): add book maintenance endpoints (BE-16)` |
| **2. Registro de Pruebas y Resultados** | `results` | `results` | `feat(results): record student test result (BE-18)`<br>`feat(results): handle batch result registration (BE-22)` |
| **3. Registro de Lecturas** | `readings` | `readings` | `feat(readings): assign book reading to student (BE-23)`<br>`feat(readings): get reading history by student and book (BE-26)` |
| **4. Informes y Salidas** | `reports` | `reports` / `exports` / `students` | `feat(reports): implement student individual report (BE-36)`<br>`feat(reports): implement group and center aggregated reports (BE-37)`<br>`feat(students): implement detection of students without progress (BE-34)` |

---

## 📂 Estado Detallado por Apartado (22 / 22 Completadas)

### 1. Catálogos y Modelo Base (Pruebas y Libros) — [Rama: `catalogs`]
* [x] **[BE-04]** [Borrado lógico de pruebas y libros](guide/US/BE-04-borrado-logico.md) (3 pts) — `tests/test_be04_borrado_logico.py`
* [x] **[BE-11]** [Alta de prueba en el catálogo](guide/US/BE-11-alta-prueba.md) (3 pts) — `tests/test_be11_alta_prueba.py`
* [x] **[BE-12]** [Importar catálogo de pruebas](guide/US/BE-12-importar-catalogo-pruebas.md) (5 pts) — `tests/test_be12_importar_catalogo.py`
* [x] **[BE-13]** [Edición y baja de pruebas](guide/US/BE-13-edicion-baja-pruebas.md) (3 pts) — `tests/test_be13_edicion_baja_pruebas.py`
* [x] **[BE-14]** [Listado paginado y filtrado de pruebas](guide/US/BE-14-listado-pruebas.md) (3 pts) — `tests/test_be14_listado_pruebas.py`
* [x] **[BE-15]** [Modelo de niveles de libro](guide/US/BE-15-niveles-libro.md) (3 pts) — `tests/test_be15_book_levels.py`
* [x] **[BE-16]** [Alta y mantenimiento del catálogo de libros](guide/US/BE-16-mantenimiento-libros.md) (3 pts) — `tests/test_be16_mantenimiento_libros.py`

### 2. Registro de Pruebas y Resultados (Núcleo del aula) — [Rama: `results`]
* [x] **[BE-18]** [Registrar el resultado de una prueba](guide/US/BE-18-registrar-resultado.md) (5 pts, **Crítica**) — `tests/test_be18_registrar_resultado.py`
* [x] **[BE-19]** [Pruebas sucesivas del mismo texto](guide/US/BE-19-pruebas-sucesivas.md) (3 pts, **Crítica**) — `tests/test_be19_pruebas_sucesivas.py`
* [x] **[BE-20]** [Consultar resultados de un alumno](guide/US/BE-20-consultar-resultados-alumno.md) (3 pts, **Crítica**) — `tests/test_be20_consultar_resultados.py`
* [x] **[BE-21]** [Corregir y anular un resultado](guide/US/BE-21-corregir-anular-resultado.md) (3 pts) — `tests/test_be21_corregir_anular.py`
* [x] **[BE-22]** [Endpoint de registro en lote](guide/US/BE-22-registro-lote.md) (5 pts) — `tests/test_be22_registro_lote.py`
* [x] **[BE-51]** [Historial de pruebas por sección](guide/US/BE-51-historial-por-seccion.md) (3 pts) — `tests/test_be51_historial_seccion.py`

### 3. Registro de Lecturas de Libros — [Rama: `readings`]
* [x] **[BE-23]** [Asignar un libro a un alumno](guide/US/BE-23-asignar-libro.md) (3 pts) — `tests/test_be23_asignar_libro.py`
* [x] **[BE-24]** [Cerrar una lectura](guide/US/BE-24-cerrar-lectura.md) (2 pts) — `tests/test_be24_cerrar_lectura.py`
* [x] **[BE-25]** [Relectura de un libro](guide/US/BE-25-relectura.md) (2 pts) — `tests/test_be25_relectura.py`
* [x] **[BE-26]** [Lecturas por alumno y por libro](guide/US/BE-26-lecturas-por-alumno-y-libro.md) (3 pts) — `tests/test_be26_lecturas_por_alumno_y_libro.py`

### 4. Vistas Agregadas, Detección y Salidas (Informes y Excel) — [Rama: `reports`]
* [x] **[BE-28]** [Endpoint agregado de la ficha del alumno](guide/US/BE-28-ficha-alumno-agregada.md) (3 pts) — `tests/test_be28_ficha_alumno_agregada.py`
* [x] **[BE-34]** [Detección de alumnos sin progreso](guide/US/BE-34-alumnos-sin-progreso.md) (5 pts) — `tests/test_be34_alumnos_sin_progreso.py`
* [x] **[BE-35]** [Exportación a Excel](guide/US/BE-35-exportacion-excel.md) (5 pts) — `tests/test_be35_exportacion_excel.py`
* [x] **[BE-36]** [Datos del informe individual de alumno](guide/US/BE-36-datos-informe-alumno.md) (3 pts) — `tests/test_be36_informe_individual_alumno.py`
* [x] **[BE-37]** [Informe agregado de grupo y centro](guide/US/BE-37-informe-grupo.md) (5 pts) — `tests/test_be37_informe_agregado_grupo.py`

---

## 🧪 Resumen de Calidad y Pruebas
* **Total historias Bloque B:** 22 de 22 completadas (76 de 76 puntos).
* **Batería de tests propia del Bloque B:** 174 tests pasando (1 skipped).
* **Regresión global de la aplicación (`pytest` en Docker):** 266 tests pasando (1 skipped).