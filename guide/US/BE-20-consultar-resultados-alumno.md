# Historia de Usuario

## ID
[BE-20]

## Título
Consultar los resultados de un alumno

## Descripción
**Como** tutor
**Quiero** ver todas las pruebas realizadas por un alumno

**Para** valorar su evolución de un vistazo.

## Criterios de Aceptación

### Escenario 1: Histórico completo
```gherkin
Dado un alumno con varios resultados registrados
Cuando se consulta GET /api/students/{id}/results
Entonces se devuelven todos sus resultados ordenados por fecha
Y devuelve 200 OK
```

### Escenario 2: Datos de la prueba incluidos
```gherkin
Dado un resultado de la prueba 1AF
Cuando se consulta el histórico
Entonces cada resultado incluye el nombre y el número de palabras de la prueba
Y no hace falta una segunda llamada para obtenerlos
```

### Escenario 3: Métricas calculadas
```gherkin
Dado un resultado con tiempo, aciertos y errores
Cuando se consulta el histórico
Entonces cada resultado incluye su PPM
Y su porcentaje de aciertos
```

### Escenario 4: Alumno sin resultados
```gherkin
Dado un alumno sin ninguna prueba registrada
Cuando se consulta su histórico
Entonces se devuelve una lista vacía
Y devuelve 200 OK, no 404
```

### Escenario 5: Alumno inexistente
```gherkin
Dado un identificador de alumno que no existe
Cuando se consulta su histórico
Entonces el sistema devuelve 404 Not Found
```

### Escenario 6: Tutor sin permiso
```gherkin
Dado un tutor cuyas secciones no incluyen a ese alumno
Cuando consulta su histórico
Entonces el sistema devuelve 403 Forbidden
```

## Notas
* **Decisiones:** los datos de la prueba se incluyen en la respuesta para evitar que la interfaz encadene una llamada por resultado. Un alumno con quince pruebas generaría dieciséis peticiones.
* **Distinción importante:** lista vacía (`200`) frente a alumno inexistente (`404`). Son situaciones distintas y la interfaz reacciona distinto a cada una.
* **Seguridad:** escenario 6 obligatorio. La consulta queda en auditoría (BE-44).
* **Testing:** escenarios 3, 4 y 6.

## Estimación
3 Puntos de Historia (Consulta con unión y métricas derivadas)

## Prioridad
Crítica

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE20-01 | **Consulta con datos de prueba** Unión en el repositorio para evitar consultas repetidas. | Yeremi | Hecho |
| T-BE20-02 | **Enriquecimiento con métricas** PPM y porcentaje de aciertos en el esquema de respuesta. | Yeremi | Hecho |
| T-BE20-03 | **Blueprint GET de resultados** Con comprobación de permiso sobre el alumno. | Yeremi | Hecho |
| T-BE20-04 | **Tests de consulta** Escenarios 1 a 6. | Yeremi | Hecho |
