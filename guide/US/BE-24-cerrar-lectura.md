# Historia de Usuario

## ID
[BE-24]

## Título
Cerrar una lectura

## Descripción
**Como** tutor
**Quiero** marcar la fecha en que un alumno termina un libro

**Para** saber cuánto ha tardado y cuántos lleva completados.

## Criterios de Aceptación

### Escenario 1: Cierre correcto
```gherkin
Dado una lectura en curso con fecha de inicio 12/09/2026
Cuando se envía PATCH con end_date 03/10/2026
Entonces la lectura queda registrada como finalizada
Y devuelve 200 OK
```

### Escenario 2: Fecha de fin anterior al inicio
```gherkin
Dado una lectura con inicio 12/09/2026
Cuando se envía PATCH con end_date 01/09/2026
Entonces el sistema rechaza la modificación
Y devuelve 422 Unprocessable Entity
```

### Escenario 3: Distinción de estados
```gherkin
Dado un alumno con una lectura cerrada y otra en curso
Cuando se consulta su listado de lecturas
Entonces cada una indica claramente su estado
Y las finalizadas muestran su fecha de fin
```

### Escenario 4: Reapertura
```gherkin
Dado una lectura ya cerrada por error
Cuando se envía PATCH poniendo end_date a nulo
Entonces la lectura vuelve a considerarse en curso
```

### Escenario 5: Lectura inexistente
```gherkin
Dado un identificador de lectura que no existe
Cuando se envía PATCH
Entonces el sistema devuelve 404 Not Found
```

## Notas
* **Decisiones:** se permite reabrir una lectura cerrada por error. Es más sencillo y menos destructivo que borrarla y volver a crearla, y conserva la fecha de inicio original.
* **Testing:** escenarios 2 y 3.

## Estimación
2 Puntos de Historia (Modificación parcial con una validación de coherencia)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE24-01 | **Validación de coherencia de fechas** Fin nunca anterior a inicio. | - | Pendiente |
| T-BE24-02 | **PATCH de la lectura** Permitiendo fijar y limpiar `end_date`. | - | Pendiente |
| T-BE24-03 | **Estado derivado** En curso o finalizada según `end_date`. | - | Pendiente |
| T-BE24-04 | **Tests de cierre** Escenarios 1 a 5. | - | Pendiente |
