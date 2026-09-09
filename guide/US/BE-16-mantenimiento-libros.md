# Historia de Usuario

## ID
[BE-16]

## Título
Alta y mantenimiento del catálogo de libros

## Descripción
**Como** coordinador pedagógico
**Quiero** gestionar el catálogo de lecturas

**Para** que los tutores puedan asignar libros existentes.

## Criterios de Aceptación

### Escenario 1: Alta de libro (POST /api/books)
```gherkin
Dado un coordinador con sesión activa
Cuando envía title y level
Entonces el sistema crea el libro
Y devuelve 201 Created
```

### Escenario 2: Título duplicado
```gherkin
Dado un libro existente con el mismo título
Cuando se intenta crear otro igual
Entonces el sistema rechaza la petición
Y devuelve 409 Conflict
```

### Escenario 3: Consulta y modificación
```gherkin
Dado un libro existente
Cuando se consulta, reemplaza o modifica parcialmente
Entonces el sistema responde 200 OK
Y 422 si los datos de la modificación no son válidos
```

### Escenario 4: Baja lógica
```gherkin
Dado un libro activo
Cuando se envía DELETE
Entonces se rellena disabled_at
Y devuelve 204 No Content
Y las lecturas registradas de ese libro siguen siendo consultables
```

### Escenario 5: El catálogo no contiene alumnos
```gherkin
Dado el recurso de libros
Cuando se inspecciona su estructura
Entonces no contiene ninguna referencia a un alumno concreto
Y la relación entre alumno y libro vive únicamente en read_books
```

## Notas
* **Esta historia corrige otro error del esquema del cliente.** La tabla `books` traía un campo `student_id`, lo que mezclaba catálogo con relación: habría una fila de "El Lazarillo" por cada alumno que lo leyera, y el catálogo dejaría de ser catálogo. El escenario 5 lo verifica explícitamente.
* **Campos de inventario:** `copies_note` y `sessions_note` se guardan como texto libre. Los valores reales del centro no son numéricos.
* **Testing:** escenarios 2, 4 y 5.

## Estimación
3 Puntos de Historia (CRUD con borrado lógico)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE16-01 | **Esquemas de libro** Alta, actualización y respuesta, con el nivel validado por BE-15. | Yeremi | Hecho |
| T-BE16-02 | **BookRepository** Alta, consulta, actualización y baja lógica. | Yeremi | Hecho |
| T-BE16-03 | **Blueprint de libros** Colección e individual con todos los verbos de la especificación. | Yeremi | Hecho |
| T-BE16-04 | **Tests del catálogo** Escenarios 1 a 5. | Yeremi | Hecho |
