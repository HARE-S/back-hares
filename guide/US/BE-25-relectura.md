# Historia de Usuario

## ID
[BE-25]

## Título
Relectura de un libro

## Descripción
**Como** coordinador pedagógico
**Quiero** que un alumno pueda leer el mismo libro en cursos distintos

**Para** no perder el registro cuando se repite una lectura.

## Criterios de Aceptación

### Escenario 1: Segunda lectura en otro curso
```gherkin
Dado un alumno que leyó "El Lazarillo" con inicio 05/10/2025
Cuando se registra otra lectura del mismo libro con inicio 12/09/2026
Entonces el sistema acepta el registro
Y el alumno tiene dos lecturas de ese libro
```

### Escenario 2: Duplicado exacto rechazado
```gherkin
Dado una lectura de "El Lazarillo" con inicio 12/09/2026
Cuando se registra otra del mismo libro con esa misma fecha de inicio
Entonces el sistema devuelve 409 Conflict
```

### Escenario 3: Histórico completo
```gherkin
Dado un alumno con dos lecturas del mismo libro
Cuando se consulta su listado de lecturas
Entonces aparecen ambas
Y se distinguen por su fecha de inicio
```

### Escenario 4: Independencia entre alumnos
```gherkin
Dado dos alumnos distintos
Cuando ambos registran el mismo libro con la misma fecha de inicio
Entonces el sistema acepta los dos registros
```

## Notas
* **Esta historia corrige otro error del esquema del cliente.** La clave primaria original de `read_books` era `(student_id, book_id)`, lo que **impide releer un libro** en otro curso. Es el mismo tipo de error que la PK de `results`, y la corrección es análoga: PK subrogada más `UNIQUE(student_id, book_id, start_date)`.
* **Testing:** escenarios 1 y 2 son pruebas obligatorias.
* **Dependencias:** requiere BE-03.

## Estimación
2 Puntos de Historia (Restricción en la migración más su prueba)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE25-01 | **Restricción de unicidad** PK subrogada y `UNIQUE(student_id, book_id, start_date)`. | Yeremi | Completado |
| T-BE25-02 | **Detección de duplicado** En el servicio, con mapeo a `409`. | Yeremi | Completado |
| T-BE25-03 | **Tests de relectura** Escenarios 1, 2 y 4. | Yeremi | Completado |
