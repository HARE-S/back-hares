# Historia de Usuario

## ID
[BE-04]

## Título
Borrado lógico de pruebas y libros

## Descripción
**Como** coordinador pedagógico
**Quiero** que dar de baja una prueba o un libro no borre el histórico

**Para** que los resultados de años anteriores sigan siendo consultables.

## Criterios de Aceptación

### Escenario 1: Baja de una prueba
```gherkin
Dado una prueba activa en el catálogo
Cuando se envía DELETE sobre esa prueba
Entonces el sistema rellena su campo disabled_at con la fecha actual
Y NO borra la fila de la base de datos
Y devuelve 204 No Content
```

### Escenario 2: La prueba desaparece del listado
```gherkin
Dado una prueba con disabled_at relleno
Cuando se consulta el listado de pruebas sin parámetros
Entonces esa prueba no aparece en los resultados
```

### Escenario 3: Consulta explícita de deshabilitadas
```gherkin
Dado una prueba con disabled_at relleno
Cuando se consulta el listado con include_disabled=true
Entonces esa prueba sí aparece en los resultados
Y se distingue por llevar fecha en disabled_at
```

### Escenario 4: El histórico se conserva
```gherkin
Dado resultados de alumnos asociados a una prueba deshabilitada
Cuando se consulta el histórico de esos alumnos
Entonces los resultados siguen siendo accesibles
Y muestran el nombre de la prueba con normalidad
```

### Escenario 5: Baja de una prueba inexistente
```gherkin
Dado un identificador de prueba que no existe
Cuando se envía DELETE
Entonces el sistema devuelve 404 Not Found
```

## Notas
* **Decisiones:** el borrado lógico es la única forma de retirar del uso diario un texto obsoleto sin destruir años de seguimiento. Un borrado físico rompería todos los resultados asociados.
* **Seguridad:** operación restringida a coordinador y administrador; queda en auditoría.
* **Alcance:** aplica a `tests` y `books`. Alumnos, secciones y centros vienen de Alexia y su baja se gestiona allí.
* **Testing:** escenarios 2 y 4 son pruebas obligatorias — el segundo garantiza que el borrado lógico no rompe el histórico.

## Estimación
3 Puntos de Historia (Filtro por defecto y parámetro de inclusión en dos recursos)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE04-01 | **Campo disabled_at** Presente en `tests` y `books` desde la migración de BE-03. | Yeremi | Completado |
| T-BE04-02 | **Filtro por defecto en repositorios** Excluir deshabilitados salvo petición explícita. | Yeremi | Completado |
| T-BE04-03 | **Parámetro include_disabled** Aceptado en los listados de pruebas y libros. | Yeremi | Completado |
| T-BE04-04 | **DELETE lógico en los endpoints** Rellenar fecha y devolver `204`; `404` si no existe. | Yeremi | Completado |
| T-BE04-05 | **Tests de borrado lógico** Escenarios 1 a 5. | Yeremi | Completado |
