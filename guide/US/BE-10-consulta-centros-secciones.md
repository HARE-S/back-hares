# Historia de Usuario

## ID
[BE-10]

## Título
Consulta de centros, secciones y su alumnado

## Descripción
**Como** tutor
**Quiero** navegar por centros y sus secciones

**Para** llegar al grupo con el que trabajo.

## Criterios de Aceptación

### Escenario 1: Listado de centros
```gherkin
Dado un usuario con sesión activa y rol asignado
Cuando consulta GET /api/centers
Entonces recibe la lista de centros activos
Y devuelve 200 OK
```

### Escenario 2: Secciones de un centro
```gherkin
Dado un centro existente
Cuando consulta GET /api/centers/{id}/sections
Entonces recibe las secciones de ese centro
Y devuelve 200 OK
```

### Escenario 3: Alumnado de una sección
```gherkin
Dado una sección existente
Cuando consulta GET /api/sections/{id}/students
Entonces recibe el alumnado matriculado en esa sección
Y devuelve 200 OK
```

### Escenario 4: Recurso inexistente
```gherkin
Dado un identificador que no corresponde a ningún centro o sección
Cuando se consulta
Entonces el sistema devuelve 404 Not Found
```

### Escenario 5: Recursos de solo lectura
```gherkin
Dado un usuario con cualquier rol
Cuando intenta un POST, PUT o DELETE sobre centros o secciones
Entonces el sistema no ofrece esa operación
Y devuelve 405 Method Not Allowed
```

### Escenario 6: Tutor limitado a sus secciones
```gherkin
Dado un tutor con una sección asignada
Cuando consulta el alumnado de una sección que no tiene asignada
Entonces el sistema deniega la operación
Y devuelve 403 Forbidden
```

## Notas
* **Decisiones:** centros, secciones y alumnado **son de solo lectura**. Su origen es Alexia y se mantienen allí; permitir su edición aquí crearía dos fuentes de verdad. Coincide con la especificación de API entregada por el cliente, donde esos recursos solo declaran `GET`.
* **Seguridad:** escenario 6 es obligatorio — es el aislamiento entre centros.
* **Testing:** escenarios 4 y 6.

## Estimación
3 Puntos de Historia (Consultas sencillas; el coste está en el filtrado por permisos)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE10-01 | **Esquemas de centro, sección y alumno** Marshmallow para las respuestas. | - | Pendiente |
| T-BE10-02 | **Repositorios de consulta** Listados y detalle, excluyendo deshabilitados. | - | Pendiente |
| T-BE10-03 | **Blueprints de centros y secciones** Solo `GET`; rutas anidadas de la especificación. | - | Pendiente |
| T-BE10-04 | **Filtrado por secciones asignadas** El tutor solo ve las suyas. | - | Pendiente |
| T-BE10-05 | **Tests de consulta y permisos** Escenarios 1 a 6. | - | Pendiente |
