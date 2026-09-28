# Especificación de Diseño: Vinculación de Lecturas a Pruebas (read_books -> tests)

**Fecha:** 2026-09-28  
**Estado:** Propuesta aprobada por el usuario (Opción A)  
**Alcance:** Backend HARES (`back-hares`)  

---

## 1. Contexto y Justificación

Actualmente, el sistema gestiona los libros evaluables a través de la tabla `tests` (catálogo oficial de lecturas evaluables con `code`, `name`, `words`, `course`, `test_letter`, `type`).
Sin embargo, las lecturas asignadas a los alumnos (`read_books`) guardaban el nombre del libro como texto libre (`book_title`), provocando:
1. Desconexión entre lo que el alumno lee y las pruebas que realiza (`results.test_id`).
2. Riesgo de inconsistencias en títulos, faltas de ortografía o duplicados.
3. Imposibilidad de saber con precisión si un alumno ya ha completado la lectura de la prueba que va a rendir.

El usuario ha seleccionado la **Opción A**: Vincular la lectura directamente a la prueba oficial del centro (`read_books.test_id`).

---

## 2. Objetivos del Diseño

1. **Catálogo Único:** `tests` es el catálogo canónico de lecturas y pruebas evaluables del centro.
2. **Relación Directa:** Cada registro de lectura en `read_books` apunta mediante clave foránea a un `test_id` (`tests.id`).
3. **Consistencia de Datos:** El título y los metadatos del libro se derivan directamente de la prueba (`test.name`, `test.code`, etc.).
4. **Independencia de Aulas y Alumnos:** Cada lectura y cada resultado corresponden a un alumno individual (`student_id`), permitiendo que múltiples alumnos de distintas aulas lean y rindan la misma prueba simultáneamente sin interferencias.
5. **Compatibilidad con Frontend:** La API seguirá exponiendo `title` / `book_title` en los payloads de lectura para no romper los componentes visuales existentes.

---

## 3. Modelo de Datos y Esquema

### 3.1. Cambios en la tabla `read_books` (PostgreSQL)

```sql
-- Clave foránea hacia tests
ALTER TABLE read_books 
  ADD COLUMN test_id UUID NOT NULL REFERENCES tests(id) ON DELETE CASCADE;

-- Eliminación de la restricción anterior por título
ALTER TABLE read_books 
  DROP CONSTRAINT IF EXISTS uq_read_books_student_title_start;

-- Nueva restricción única por alumno, prueba y fecha de inicio
ALTER TABLE read_books 
  ADD CONSTRAINT uq_read_books_student_test_start 
  UNIQUE (student_id, test_id, start_date);

-- Índice para búsquedas rápidas por prueba
CREATE INDEX ix_read_books_test_id ON read_books(test_id);
```

### 3.2. Modelo SQLAlchemy (`ReadBook` en `app/models/book.py`)

* Atributos de base de datos:
  * `id`: UUID (v7).
  * `student_id`: UUID, FK a `students.id`.
  * `test_id`: UUID, FK a `tests.id`.
  * `start_date`: Date, obligatorio.
  * `end_date`: Date, opcional (lectura en curso si es null).
  * `copies_note`: String(255), opcional.
  * `sessions_note`: String(255), opcional.
* Relaciones:
  * `student`: `relationship("Student", back_populates="read_books")`
  * `test`: `relationship("Test", back_populates="read_books", lazy="joined")`
* Propiedades de compatibilidad:
  * `title`: Retorna `self.test.name`.
  * `book_title`: Retorna `self.test.name`.
  * `level`: Retorna el nivel pedagógico asociado a la prueba (o derivado de su código).
  * `status`: `"finalizada"` si `end_date` está informado, `"en_curso"` en caso contrario.

---

## 4. Capa de Servicios y API

### 4.1. Asignación de Lectura (`ReadingService.assign_book`)
* Recibe: `student_id`, `test_id` (o `test_code`), `start_date`, notas opcionales.
* Valida:
  1. Que el alumno exista.
  2. Que la prueba exista en `tests` y no esté deshabilitada (`disabled_at is None`).
  3. Que no exista una lectura activa idéntica en la misma fecha de inicio (`uq_read_books_student_test_start`).
* Crea y retorna la lectura serializada con los datos de la prueba asociada.

### 4.2. Cierre de Lectura (`ReadingService.close_or_update_reading`)
* Permite informar `end_date` para marcar la lectura como finalizada.
* Valida que `end_date >= start_date`.

### 4.3. Serialización (`ReadingSchema`)
Salida del objeto lectura:
```json
{
  "id": "018f...uuid",
  "student_id": "018f...uuid",
  "test_id": "018f...uuid",
  "test_code": "0IF",
  "title": "Normativa piscinas",
  "book_title": "Normativa piscinas",
  "start_date": "2026-09-01",
  "end_date": "2026-09-15",
  "status": "finalizada",
  "copies_note": "Ejemplar 1",
  "sessions_note": "Leído en aula"
}
```

---

## 5. Pruebas y Criterios de Aceptación

1. **BE-23 (Asignar lectura):** Se asigna un libro mediante su `test_id`. La lectura queda vinculada y expone el título y código de la prueba.
2. **BE-24 (Cerrar lectura):** Se cierra con `end_date`. Estado pasa a `finalizada`.
3. **BE-25 (Relectura):** El mismo alumno puede volver a leer el mismo `test_id` con otra fecha de inicio.
4. **BE-26 (Lecturas por alumno y por prueba):**
   * Listar lecturas de un alumno devolviendo datos del `test`.
   * Listar qué alumnos han leído una prueba determinada (`/api/v1/readings/test/<test_id>/students`).
5. **No interferencia entre alumnos:** Múltiples alumnos pueden leer el mismo `test_id` de forma independiente.
6. **Regresión completa:** Todos los tests del proyecto deben seguir pasando.
