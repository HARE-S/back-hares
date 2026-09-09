# Historia de Usuario

## ID
[BE-11]

## Título
Alta de prueba en el catálogo

## Descripción
**Como** coordinador pedagógico
**Quiero** dar de alta un texto de control

**Para** poder aplicarlo a los alumnos del programa.

## Criterios de Aceptación

### Escenario 1: Alta correcta (POST /api/tests)
```gherkin
Dado un coordinador con sesión activa
Cuando envía code, name y words, opcionalmente level y type
Entonces el sistema crea la prueba
Y devuelve 201 Created con el recurso completo
```

### Escenario 2: Código duplicado
```gherkin
Dado una prueba existente con código "1AF"
Cuando se intenta crear otra con el mismo código
Entonces el sistema rechaza la petición
Y devuelve 409 Conflict
```

### Escenario 3: Número de palabras inválido
```gherkin
Dado un coordinador con sesión activa
Cuando envía words con valor cero, negativo o no numérico
Entonces el sistema rechaza la petición
Y devuelve 400 Bad Request indicando el campo
```

### Escenario 4: Campos obligatorios ausentes
```gherkin
Dado una petición sin code o sin name
Cuando se procesa
Entonces el sistema devuelve 400 Bad Request
```

### Escenario 5: Rol sin permiso
```gherkin
Dado un usuario con rol tutor
Cuando intenta crear una prueba
Entonces el sistema deniega la operación
Y devuelve 403 Forbidden
```

## Notas
* **`words` es crítico:** es el numerador del cálculo de PPM. Un valor mal introducido falsea todas las métricas de esa prueba sin que nada falle visiblemente.
* **Seguridad:** coordinador y administrador. Los tutores consultan el catálogo pero no lo modifican.
* **Contrato:** el endpoint declara `@blp.arguments` y `@blp.response`; sin ellos no entra en la especificación OpenAPI.
* **Testing:** escenarios 2, 3 y 5.

## Estimación
3 Puntos de Historia (CRUD sencillo con validación)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE11-01 | **Esquemas de prueba** `TestCreateSchema` con validación de `words` y `TestSchema` de respuesta. | Yeremi | Completado |
| T-BE11-02 | **TestRepository** Alta y comprobación de código único. | Yeremi | Completado |
| T-BE11-03 | **CatalogService** Regla de código duplicado y excepción de dominio. | Yeremi | Completado |
| T-BE11-04 | **Blueprint POST /api/tests** Con `@require_role` de coordinador. | Yeremi | Completado |
| T-BE11-05 | **Tests de alta** Escenarios 1 a 5. | Yeremi | Completado |
