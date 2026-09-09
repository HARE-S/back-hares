# Historia de Usuario

## ID
[BE-14]

## Título
Listado paginado y filtrado de pruebas

## Descripción
**Como** tutor
**Quiero** buscar una prueba por nivel o por nombre

**Para** encontrarla rápido al registrar un resultado.

## Criterios de Aceptación

### Escenario 1: Listado paginado
```gherkin
Dado un catálogo con 34 pruebas
Cuando se consulta con page=1 y limit=10
Entonces se devuelven 10 pruebas
Y la respuesta incluye el total de elementos y el número de páginas
```

### Escenario 2: Búsqueda por texto
```gherkin
Dado un catálogo de pruebas
Cuando se consulta con filter="Warner"
Entonces se devuelven las pruebas cuyo código o nombre contienen ese texto
```

### Escenario 3: Filtro por nivel y tipo
```gherkin
Dado un catálogo con pruebas de varios niveles
Cuando se consulta con level=1 y type=F
Entonces se devuelven solo las pruebas de nivel 1 y tipo F
```

### Escenario 4: Filtros combinados
```gherkin
Dado un catálogo de pruebas
Cuando se consulta con filter, level y page a la vez
Entonces los tres criterios se aplican conjuntamente
```

### Escenario 5: Deshabilitadas excluidas
```gherkin
Dado una prueba con disabled_at relleno
Cuando se consulta el listado sin parámetros adicionales
Entonces esa prueba no aparece
```

## Notas
* **Decisiones:** la paginación devuelve el total y el número de páginas para que la interfaz pueda construir el paginador sin una segunda llamada.
* **Búsqueda insensible a acentos**, igual que en BE-29: el profesorado no va a teclear tildes al buscar.
* **Testing:** escenarios 1, 3 y 5.

## Estimación
3 Puntos de Historia (Consulta con filtros combinables y metadatos de paginación)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE14-01 | **Esquema de paginación** En `schemas/common.py`, reutilizable por todos los listados. | - | Pendiente |
| T-BE14-02 | **Filtros en el repositorio** Texto, nivel y tipo, combinables. | - | Pendiente |
| T-BE14-03 | **Respuesta con metadatos** Total de elementos y número de páginas. | - | Pendiente |
| T-BE14-04 | **Tests de listado** Escenarios 1 a 5. | - | Pendiente |
