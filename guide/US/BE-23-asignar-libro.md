# Historia de Usuario

## ID
[BE-23]

## Título
Asignar un libro a un alumno

## Descripción
**Como** tutor
**Quiero** registrar que un alumno ha empezado un libro

**Para** llevar el control de sus lecturas.

## Criterios de Aceptación

### Escenario 1: Asignación correcta
```gherkin
Dado un tutor con la sección del alumno asignada
Cuando envía POST /api/students/{id}/books con book_id y start_date
Entonces se registra la lectura
Y devuelve 201 Created
```

### Escenario 2: Lectura sin fecha de fin
```gherkin
Dado una asignación sin end_date
Cuando se procesa
Entonces la lectura queda registrada como en curso
Y no se considera un error
```

### Escenario 3: Libro inexistente
```gherkin
Dado un book_id que no existe en el catálogo
Cuando se intenta asignar
Entonces el sistema devuelve 400 Bad Request
```

### Escenario 4: Libro deshabilitado
```gherkin
Dado un libro con disabled_at relleno
Cuando se intenta asignar a un alumno
Entonces el sistema devuelve 400 Bad Request
Y explica que el libro ya no está disponible
```

### Escenario 5: Tutor sin permiso
```gherkin
Dado un tutor cuyas secciones no incluyen a ese alumno
Cuando intenta asignarle un libro
Entonces el sistema devuelve 403 Forbidden
```

## Notas
* **Decisiones:** `end_date` opcional permite registrar la lectura al empezarla, que es cuando el tutor tiene la información delante. Exigir la fecha de fin obligaría a registrarlo todo al terminar, y entonces no se registraría.
* **Un libro deshabilitado no se puede asignar de nuevo**, pero las lecturas ya registradas de ese libro siguen siendo válidas y consultables.
* **Testing:** escenarios 3, 4 y 5.

## Estimación
3 Puntos de Historia (Alta con validación de referencias)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE23-01 | **Esquema de lectura** Alta con `book_id`, `start_date` y `end_date` opcional. | Yeremi | Hecho |
| T-BE23-02 | **ReadingService** Validar existencia y disponibilidad del libro. | Yeremi | Hecho |
| T-BE23-03 | **Blueprint POST de lecturas** Con comprobación de permiso sobre el alumno. | Yeremi | Hecho |
| T-BE23-04 | **Tests de asignación** Escenarios 1 a 5. | Yeremi | Hecho |
