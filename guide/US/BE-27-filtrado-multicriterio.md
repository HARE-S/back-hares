# Historia de Usuario

## ID
[BE-27]

## Título
Filtrado multicriterio del alumnado

## Descripción
**Como** coordinador pedagógico
**Quiero** segmentar el alumnado por edad, género, situación académica y sector

**Para** comparar la evolución entre perfiles distintos.

## Criterios de Aceptación

### Escenario 1: Filtro por un criterio
```gherkin
Dado un conjunto de alumnos con sus datos informados
Cuando se filtra por un único criterio
Entonces se devuelven solo los alumnos que lo cumplen
Y devuelve 200 OK
```

### Escenario 2: Criterios combinados
```gherkin
Dado un conjunto de alumnos
Cuando se filtra por sector y situación académica a la vez
Entonces se aplican ambos criterios conjuntamente
```

### Escenario 3: Filtro por centro y sección
```gherkin
Dado alumnos de varios centros
Cuando se filtra por centro o por sección
Entonces se devuelven solo los del ámbito indicado
```

### Escenario 4: Edad derivada de la fecha de nacimiento
```gherkin
Dado un alumno con fecha de nacimiento registrada
Cuando se filtra por un rango de edad
Entonces la edad se calcula a partir de la fecha de nacimiento
Y no se consulta ningún campo de edad almacenado
```

### Escenario 5: Alumnos sin el dato informado
```gherkin
Dado alumnos cuyo sector no está informado
Cuando se filtra por sector
Entonces esos alumnos se pueden consultar agrupados como "sin datos"
Y no desaparecen silenciosamente del conjunto
```

### Escenario 6: Tutor limitado a sus secciones
```gherkin
Dado un tutor con dos secciones asignadas
Cuando aplica cualquier filtro
Entonces los resultados se limitan a su alumnado
```

## Notas
* **BLOQUEADA.** Ninguno de los cuatro campos —edad, género, situación académica y sector— existe hoy en el volcado de Alexia ni en el esquema entregado. **Esta historia no se puede completar** hasta que el cliente amplíe la exportación. Entretanto, entregar la infraestructura de filtrado funcionando sobre centro y sección, con los campos nullable ya en el esquema.
* **Decisiones:** la edad se **deriva** de `birth_date`, nunca se almacena. Una edad almacenada queda desactualizada al día siguiente del cumpleaños.
* **Seguridad:** género y situación académica son datos sensibles de menores. Su uso queda en auditoría y no aparecen en logs.
* **Escenario 5 importa:** ocultar sin avisar a los alumnos sin dato haría que una media pareciera calculada sobre todo el grupo cuando no lo está.

## Estimación
5 Puntos de Historia (Consulta con filtros combinables; el bloqueo es de datos, no técnico)

## Prioridad
Alta — bloqueada por el cliente

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE27-01 | **Esquema de filtros** En `schemas/common.py`, reutilizable. | - | Pendiente |
| T-BE27-02 | **Filtros por centro y sección** Parte no bloqueada, entregable ya. | - | Pendiente |
| T-BE27-03 | **Cálculo de edad desde birth_date** En la consulta, no almacenado. | - | Bloqueado |
| T-BE27-04 | **Filtros por género, situación y sector** Pendiente de que el cliente amplíe el volcado. | - | Bloqueado |
| T-BE27-05 | **Agrupación "sin datos"** Alumnos sin el campo informado. | - | Pendiente |
| T-BE27-06 | **Tests de filtrado** Escenarios 1, 2, 3 y 6. | - | Pendiente |
