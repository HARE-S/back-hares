# Historia de Usuario

## ID
[BE-21]

## Título
Corregir y anular un resultado

## Descripción
**Como** tutor
**Quiero** rectificar un resultado mal introducido

**Para** que los análisis no arrastren un error de tecleo.

## Criterios de Aceptación

### Escenario 1: Corrección parcial
```gherkin
Dado un resultado registrado con un tiempo erróneo
Cuando se envía PATCH modificando solo el tiempo
Entonces el resultado se actualiza
Y su PPM se recalcula en la respuesta
Y devuelve 200 OK
```

### Escenario 2: Datos inválidos
```gherkin
Dado un resultado existente
Cuando se envía PATCH con aciertos negativos
Entonces el sistema devuelve 422 Unprocessable Entity
Y el resultado no se modifica
```

### Escenario 3: Anulación
```gherkin
Dado un resultado registrado por error
Cuando se envía DELETE sobre él
Entonces el resultado se elimina
Y devuelve 204 No Content
```

### Escenario 4: Resultado inexistente
```gherkin
Dado un identificador de resultado que no existe
Cuando se envía PATCH o DELETE
Entonces el sistema devuelve 404 Not Found
```

### Escenario 5: Tutor sin permiso
```gherkin
Dado un tutor cuyas secciones no incluyen al alumno del resultado
Cuando intenta modificarlo o eliminarlo
Entonces el sistema devuelve 403 Forbidden
```

### Escenario 6: Traza de la modificación
```gherkin
Dado una corrección o anulación completada
Cuando termina la operación
Entonces queda registrada en auditoría con el usuario y el valor anterior
```

## Notas
* **Decisiones:** aquí el borrado **sí es físico**, a diferencia de pruebas y libros. Un resultado anulado es un dato que nunca debió existir, no un registro histórico que retirar del uso. Lo que se conserva es la traza en auditoría.
* **Seguridad:** escenarios 5 y 6 obligatorios. Con datos de menores, un cambio sin rastro es justo lo que no se puede permitir — y es la razón por la que las correcciones se hacen por la aplicación y nunca con un `UPDATE` desde pgAdmin.
* **Testing:** escenarios 2, 4 y 5.

## Estimación
3 Puntos de Historia (Verbos estándar más auditoría del valor anterior)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE21-01 | **Esquema de actualización de resultado** Todos los campos opcionales, con validación. | Yeremi | Hecho |
| T-BE21-02 | **PATCH y DELETE del recurso** En el `MethodView` del resultado individual. | Yeremi | Hecho |
| T-BE21-03 | **Auditoría con valor anterior** Registrar qué cambió y desde qué valor. | Yeremi | Hecho |
| T-BE21-04 | **Tests de corrección** Escenarios 1 a 6. | Yeremi | Hecho |
