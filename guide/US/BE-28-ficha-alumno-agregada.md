# Historia de Usuario

## ID
[BE-28]

## Título
Endpoint agregado de la ficha del alumno

## Descripción
**Como** tutor
**Quiero** obtener en una sola llamada todo lo relativo a un alumno

**Para** que la ficha se cargue de una vez y no en cinco peticiones encadenadas.

## Criterios de Aceptación

### Escenario 1: Ficha completa
```gherkin
Dado un alumno con resultados y lecturas registrados
Cuando se consulta GET /api/students/{id}
Entonces la respuesta incluye sus datos personales
Y sus secciones actuales e históricas
Y sus resultados con PPM y porcentaje de aciertos
Y sus lecturas con su estado
```

### Escenario 2: Una sola petición
```gherkin
Dado la carga de una ficha de alumno
Cuando se cuentan las peticiones necesarias
Entonces basta con una
Y no hace falta llamar a resultados y lecturas por separado
```

### Escenario 3: Secciones históricas
```gherkin
Dado un alumno que cambió de sección entre cursos
Cuando se consulta su ficha
Entonces se distinguen sus secciones actuales de las anteriores
```

### Escenario 4: Alumno sin datos
```gherkin
Dado un alumno recién importado sin resultados ni lecturas
Cuando se consulta su ficha
Entonces se devuelven sus datos con listas vacías
Y devuelve 200 OK
```

### Escenario 5: Alumno inexistente o sin permiso
```gherkin
Dado un identificador inexistente
Cuando se consulta
Entonces devuelve 404 Not Found
Y si el alumno existe pero el tutor no tiene su sección, devuelve 403 Forbidden
```

## Notas
* **Decisiones:** un endpoint agregado va contra la ortodoxia REST de un recurso por llamada, pero aquí la pantalla de ficha necesita cuatro conjuntos de datos a la vez. Encadenar peticiones en la interfaz produce cargas escalonadas y estados intermedios feos. La alternativa —que la interfaz haga cinco llamadas— traslada complejidad al lado equivocado.
* **Contrato:** es la fuente de la pantalla de ficha del alumno. Cualquier cambio en su forma se avisa al equipo de interfaz.
* **Testing:** escenarios 1, 4 y 5.

## Estimación
3 Puntos de Historia (Composición de consultas ya existentes)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE28-01 | **Esquema StudentDetail** Con secciones, resultados y lecturas anidados. | - | Pendiente |
| T-BE28-02 | **Composición en el servicio** Reutilizando repositorios existentes, sin consultas nuevas duplicadas. | - | Pendiente |
| T-BE28-03 | **Distinción de secciones actuales e históricas** A partir de `student_sections`. | - | Pendiente |
| T-BE28-04 | **Tests de la ficha** Escenarios 1 a 5. | - | Pendiente |
