# Historia de Usuario

## ID
[BE-19]

## Título
Pruebas sucesivas del mismo texto

## Descripción
**Como** coordinador pedagógico
**Quiero** que un alumno pueda repetir la misma prueba en fechas distintas

**Para** poder medir su mejora sobre un texto que ya conoce.

## Criterios de Aceptación

### Escenario 1: Repetición en otra fecha
```gherkin
Dado un alumno con un resultado de la prueba 1AF el 10/03/2026
Cuando se registra otro resultado de la prueba 1AF el 24/03/2026
Entonces el sistema acepta el registro
Y devuelve 201 Created
Y el alumno pasa a tener dos resultados de esa misma prueba
```

### Escenario 2: Tercera repetición
```gherkin
Dado un alumno con dos resultados de la prueba 1AF en fechas distintas
Cuando se registra un tercero en una fecha nueva
Entonces el sistema lo acepta
Y no existe límite al número de repeticiones
```

### Escenario 3: Duplicado exacto rechazado
```gherkin
Dado un alumno con un resultado de la prueba 1AF el 10/03/2026
Cuando se envía otro con esa misma prueba y fecha
Entonces el sistema devuelve 409 Conflict
Y sigue existiendo un único resultado para esa combinación
```

### Escenario 4: Histórico ordenado
```gherkin
Dado un alumno con resultados el 24/03, el 10/03 y el 07/04
Cuando se consulta su histórico
Entonces se devuelven ordenados por fecha ascendente
Y cada uno incluye su PPM y su porcentaje de aciertos
```

### Escenario 5: Independencia entre alumnos
```gherkin
Dado dos alumnos distintos
Cuando ambos registran un resultado de la prueba 1AF con la misma fecha
Entonces el sistema acepta los dos registros
Y la restricción de unicidad no los considera duplicados
```

## Notas
* **Esta historia corrige el error más grave del esquema entregado.** La clave primaria original de `results` era `(student_id, section_id)`, es decir **un único resultado por alumno y sección**. Con esa clave, la segunda prueba de un alumno machaca a la primera y no hay evolución que medir — el objetivo entero del proyecto queda fuera de alcance. Probablemente era un copy-paste de la PK de `student_sections`, donde sí está bien.
* **Decisiones:** la unicidad incluye la fecha a propósito. Sin ella no se podría repetir un texto; con algo más laxo se podrían duplicar registros por error de tecleo en la misma sesión.
* **Prioridad de validación:** debe verificarse **antes que cualquier funcionalidad de análisis**. Si la restricción está mal, todo lo construido encima carece de datos.
* **Testing:** escenarios 1 y 3 son pruebas obligatorias. Contra PostgreSQL: SQLite no aplica igual las restricciones `UNIQUE` compuestas.
* **Dependencias:** requiere BE-03. Desbloquea BE-31 a BE-34.

## Estimación
3 Puntos de Historia (La implementación es una restricción; el valor está en las pruebas)

## Prioridad
Crítica — sin ella el proyecto no cumple su objetivo

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE19-01 | **Restricción de unicidad** PK subrogada y `UNIQUE(student_id, test_id, test_date)`. | Yeremi | Hecho |
| T-BE19-02 | **Detección de duplicado en servicio** Comprobar antes de insertar. | Yeremi | Hecho |
| T-BE19-03 | **Mapeo a 409** Excepción de dominio, no error crudo de base de datos. | Yeremi | Hecho |
| T-BE19-04 | **Orden del histórico** Por `test_date` ascendente en el repositorio. | Yeremi | Hecho |
| T-BE19-05 | **Tests de repetición** Escenarios 1, 2, 3 y 5 contra PostgreSQL real. | Yeremi | Hecho |
