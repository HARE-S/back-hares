# Historia de Usuario

## ID
[BE-26]

## Título
Consulta de lecturas por alumno y por libro

## Descripción
**Como** coordinador pedagógico
**Quiero** consultar qué ha leído un alumno y quién ha leído un libro

**Para** planificar la disponibilidad de ejemplares y el seguimiento individual.

## Criterios de Aceptación

### Escenario 1: Lecturas de un alumno
```gherkin
Dado un alumno con varias lecturas registradas
Cuando se consulta GET /api/students/{id}/books
Entonces se devuelven sus lecturas con el título y el nivel de cada libro
Y devuelve 200 OK
```

### Escenario 2: Alumnos que han leído un libro
```gherkin
Dado un libro leído por varios alumnos
Cuando se consulta GET /api/books/{id}/students
Entonces se devuelve la lista de alumnos con sus fechas de lectura
```

### Escenario 3: Filtro por estado
```gherkin
Dado un alumno con lecturas en curso y finalizadas
Cuando se consulta filtrando por estado "en curso"
Entonces se devuelven solo las que no tienen fecha de fin
```

### Escenario 4: Sin lecturas
```gherkin
Dado un alumno sin ninguna lectura registrada
Cuando se consulta su listado
Entonces se devuelve una lista vacía con 200 OK
```

### Escenario 5: Tutor sin permiso
```gherkin
Dado un tutor cuyas secciones no incluyen a ese alumno
Cuando consulta sus lecturas
Entonces el sistema devuelve 403 Forbidden
```

## Notas
* **Utilidad real:** la consulta por libro sirve para saber si hay ejemplares libres antes de asignarlo. Con `copies_note` guardado como texto, la decisión final es del coordinador, pero al menos ve quién lo tiene.
* **Decisiones:** título y nivel se incluyen en la respuesta para evitar una llamada por lectura.
* **Testing:** escenarios 3 y 5.

## Estimación
3 Puntos de Historia (Dos consultas con unión y filtro por estado)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE26-01 | **Consulta de lecturas por alumno** Con datos del libro incluidos. | - | Pendiente |
| T-BE26-02 | **Consulta de alumnos por libro** Con fechas de lectura. | - | Pendiente |
| T-BE26-03 | **Filtro por estado** En curso o finalizada. | - | Pendiente |
| T-BE26-04 | **Tests de consulta** Escenarios 1 a 5. | - | Pendiente |
