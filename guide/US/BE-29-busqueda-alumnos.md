# Historia de Usuario

## ID
[BE-29]

## Título
Búsqueda de alumnos

## Descripción
**Como** tutor
**Quiero** buscar un alumno escribiendo parte de su nombre

**Para** llegar a su ficha sin recorrer listados.

## Criterios de Aceptación

### Escenario 1: Búsqueda por fragmento
```gherkin
Dado un conjunto de alumnos
Cuando se busca "stud"
Entonces se devuelven los alumnos cuyo nombre contiene ese fragmento
Y devuelve 200 OK
```

### Escenario 2: Insensible a mayúsculas y acentos
```gherkin
Dado un alumno cuyo nombre contiene acentos
Cuando se busca ese nombre sin tildes y en minúsculas
Entonces el alumno aparece en los resultados
```

### Escenario 3: Búsqueda corta
```gherkin
Dado una búsqueda de dos caracteres
Cuando se envía la consulta
Entonces el sistema devuelve resultados
Y no exige un mínimo de tres caracteres
```

### Escenario 4: Desambiguación de homónimos
```gherkin
Dado dos alumnos con el mismo nombre en centros distintos
Cuando se buscan
Entonces cada resultado incluye su centro y su sección
Y se pueden distinguir sin abrir la ficha
```

### Escenario 5: Ámbito del tutor
```gherkin
Dado un tutor con dos secciones asignadas
Cuando busca un alumno de otra sección
Entonces ese alumno no aparece en sus resultados
```

## Notas
* **Los homónimos son reales:** en los datos de ejemplo hay nombres repetidos. Sin centro y sección en el resultado, el tutor tendría que abrir fichas hasta acertar.
* **Insensible a acentos:** el profesorado no va a teclear tildes al buscar. Se resuelve en la consulta, no normalizando los datos almacenados, que deben conservar su ortografía.
* **Seguridad:** escenario 5 obligatorio. La búsqueda no puede ser una vía para enumerar alumnado de otros centros.
* **Testing:** escenarios 2, 4 y 5.

## Estimación
3 Puntos de Historia (Consulta con normalización y filtro por ámbito)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE29-01 | **Consulta insensible a acentos** Normalización en la consulta, no en los datos. | - | Pendiente |
| T-BE29-02 | **Respuesta con centro y sección** Para desambiguar homónimos. | - | Pendiente |
| T-BE29-03 | **Filtro por ámbito del usuario** El tutor solo busca en sus secciones. | - | Pendiente |
| T-BE29-04 | **Tests de búsqueda** Escenarios 1 a 5. | - | Pendiente |
