# Historia de Usuario

## ID
[BE-03]

## Título
Esquema inicial versionado con migraciones

## Descripción
**Como** desarrollador
**Quiero** que el esquema se cree mediante migraciones versionadas

**Para** poder evolucionarlo sin perder datos ni descuadrar entornos.

## Criterios de Aceptación

### Escenario 1: Creación del esquema desde cero
```gherkin
Dado un contenedor de PostgreSQL vacío
Cuando se ejecuta "alembic upgrade head"
Entonces se crean las once tablas del modelo
Y todas las claves foráneas declaran su política ON DELETE
Y existen índices sobre results(student_id, test_date) y read_books(student_id)
```

### Escenario 2: Reversión de la migración
```gherkin
Dado un esquema ya migrado
Cuando se ejecuta "alembic downgrade -1"
Entonces el esquema vuelve al estado anterior sin errores
Y no quedan tablas ni restricciones huérfanas
```

### Escenario 3: Un alumno registra dos resultados de la misma prueba
```gherkin
Dado un alumno con un resultado de la prueba 1AF el 10/03/2026
Cuando se inserta otro resultado de la prueba 1AF el 24/03/2026
Entonces la inserción se completa correctamente
Y el alumno tiene dos resultados de esa prueba
```

### Escenario 4: Duplicado exacto rechazado por la base de datos
```gherkin
Dado un alumno con un resultado de la prueba 1AF el 10/03/2026
Cuando se inserta otro con esa misma prueba y fecha
Entonces la base de datos rechaza la inserción
Y se viola la restricción UNIQUE(student_id, test_id, test_date)
```

### Escenario 5: Un alumno relee un libro en otro curso
```gherkin
Dado un alumno que leyó "El Lazarillo" con inicio 05/10/2025
Cuando se registra otra lectura del mismo libro con inicio 12/09/2026
Entonces la inserción se completa correctamente
```

### Escenario 6: Identificación de un registro procedente de Alexia
```gherkin
Dado un alumno importado con external_id "STU01"
Cuando se consulta por ese external_id
Entonces devuelve exactamente un registro
Y no es posible crear otro alumno con el mismo external_id
```

## Notas

* **Correcciones obligatorias sobre el esquema entregado por el cliente:**

| Tabla | Cambio | Motivo |
| :--- | :--- | :--- |
| `centers`, `sections`, `students` | + `external_id varchar unique` | Sin código de origen la reimportación duplica |
| `students` | + `birth_date`, `gender`, `academic_status`, `sector` (nullable) | Criterios de filtrado de BE-27 |
| `sections` | + `academic_year` | Requisito del papel |
| `tests` | + `level`, `type`; `code` unique | El código `0IF` esconde nivel y tipo |
| `results` | **PK → `id uuid`** + `UNIQUE(student_id, test_id, test_date)` | La PK original impide pruebas sucesivas |
| `books` | **quitar `student_id`**; `level` a varchar | Es catálogo, no relación. Niveles reales: `0`, `0-I`, `I`, `II`, `I/II` |
| `read_books` | renombrada desde `reaeded_books`; **PK → `id uuid`** + `UNIQUE(student_id, book_id, start_date)` | Permitir relectura |
| `users`, `user_sections`, `audit_log` | nuevas | No existían |

* **Decisiones:** `results.section_id` se conserva **a propósito**. Es la foto del momento: si un alumno cambia de grupo, el histórico debe seguir diciendo dónde estaba al hacer cada prueba.
* **Testing:** escenarios 3, 4 y 5 son pruebas obligatorias. **Contra PostgreSQL, nunca SQLite**: SQLite no aplica igual las restricciones `UNIQUE` compuestas y pasarían en falso.

## Estimación
8 Puntos de Historia (Once tablas, restricciones compuestas y reversibilidad)

## Prioridad
Crítica — bloquea todo el desarrollo posterior

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE03-01 | **Configuración de Alembic** `alembic.ini` y `env.py` apuntando a la metadata y a `DATABASE_URL`. | - | Pendiente |
| T-BE03-02 | **Modelos de datos maestros** `Center`, `Section`, `Student`, `StudentSection` con `external_id` y `disabled_at`. | - | Pendiente |
| T-BE03-03 | **Modelos de pruebas y resultados** `Test` con `level` y `type`; `Result` con PK subrogada y unicidad por fecha. | - | Pendiente |
| T-BE03-04 | **Modelos de libros y lecturas** `Book` como catálogo puro; `ReadBook` con PK subrogada. | - | Pendiente |
| T-BE03-05 | **Modelos de usuarios y auditoría** `User` con `google_sub` único, `UserSection`, `AuditLog`. | - | Pendiente |
| T-BE03-06 | **Migración inicial e índices** Generar, **revisar a mano** lo autogenerado y verificar el `downgrade`. | - | Pendiente |
| T-BE03-07 | **Tests de restricciones** Escenarios 3 a 6 contra PostgreSQL real. | - | Pendiente |
