# Historia de Usuario

## ID
[BE-51]

## Título
Historial de pruebas por sección

## Descripción
**Como** coordinador pedagógico
**Quiero** consultar todas las pruebas realizadas en una sección

**Para** ver el estado del grupo completo sin abrir la ficha de cada alumno.

## Criterios de Aceptación

### Escenario 1: Histórico del grupo
```gherkin
Dado una sección con alumnado y resultados registrados
Cuando se consulta su historial de pruebas
Entonces se devuelven los resultados de todos sus alumnos
Y cada uno indica a qué alumno y a qué prueba corresponde
Y devuelve 200 OK
```

### Escenario 2: Agrupación por prueba
```gherkin
Dado una sección donde se ha aplicado la misma prueba a todo el grupo
Cuando se consulta el historial agrupado por prueba
Entonces se ven juntos los resultados de esa aplicación
Y se puede comparar a los alumnos entre sí
```

### Escenario 3: Acotación por fechas
```gherkin
Dado una sección con resultados de todo el curso
Cuando se consulta acotando a un rango de fechas
Entonces solo se devuelven los resultados de ese periodo
```

### Escenario 4: Resultados de alumnos que cambiaron de grupo
```gherkin
Dado un alumno que hizo una prueba estando en la sección A
Y que después pasó a la sección B
Cuando se consulta el historial de la sección A
Entonces ese resultado sigue apareciendo en la sección A
Y no se traslada a la B
```

### Escenario 5: Sección sin resultados
```gherkin
Dado una sección sin ninguna prueba registrada
Cuando se consulta su historial
Entonces se devuelve una lista vacía con 200 OK
```

### Escenario 6: Tutor sin la sección asignada
```gherkin
Dado un tutor cuyas secciones no incluyen la consultada
Cuando pide su historial
Entonces el sistema devuelve 403 Forbidden
```

## Notas

* **Escenario 4 es la razón por la que `results` guarda `section_id`.** Ese campo, que parece redundante con `student_sections`, es lo que permite que el historial de un grupo siga siendo fiel años después aunque el alumnado se haya movido. Sin él, un cambio de grupo reescribiría retroactivamente el historial de las dos secciones.

* **Uso previsto:** es la vista de trabajo del coordinador y del tutor tras una sesión de pruebas. Complementa el histórico individual de BE-20, que sirve para la tutoría con un alumno concreto.

* **Relación con BE-22:** tras un registro en lote, esta consulta es la que permite comprobar de un vistazo que se ha guardado todo bien.

* **Seguridad:** escenario 6 obligatorio. La consulta queda en auditoría por contener datos de varios menores a la vez.

* **Testing:** escenarios 4 y 6.

## Estimación
3 Puntos de Historia (Consulta con agrupación y acotación sobre datos ya modelados)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE51-01 | **Consulta por sección** Filtrando por `results.section_id`, no por la matrícula actual. | Yeremi | Hecho |
| T-BE51-02 | **Agrupación por prueba** Opcional, mediante parámetro. | Yeremi | Hecho |
| T-BE51-03 | **Acotación por rango de fechas** Parámetros opcionales. | Yeremi | Hecho |
| T-BE51-04 | **Endpoint del historial de sección** Con comprobación de permiso. | Yeremi | Hecho |
| T-BE51-05 | **Tests del historial** Escenarios 1, 4, 5 y 6. | Yeremi | Hecho |
