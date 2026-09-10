# Historia de Usuario

## ID
[BE-22]

## Título
Endpoint de registro de resultados en lote

## Descripción
**Como** tutor
**Quiero** enviar de una vez los resultados de todo el grupo tras una sesión

**Para** no repetir veinte veces la misma petición.

## Criterios de Aceptación

### Escenario 1: Lote correcto
```gherkin
Dado un tutor con la sección asignada
Cuando envía una prueba, una fecha y una lista de resultados por alumno
Entonces se registran todos los resultados en una sola transacción
Y devuelve 201 Created con el resumen de lo registrado
```

### Escenario 2: Alumnos ausentes omitidos
```gherkin
Dado un lote donde tres alumnos vienen sin datos
Cuando se procesa
Entonces esos tres alumnos no generan ningún resultado
Y no se registran con valores a cero
```

### Escenario 3: Una fila inválida
```gherkin
Dado un lote de veinte filas donde una tiene un tiempo negativo
Cuando se procesa
Entonces el sistema indica qué fila ha fallado y por qué
Y la respuesta permite a la interfaz señalar esa fila concreta
```

### Escenario 4: Atomicidad
```gherkin
Dado un lote que falla a mitad de proceso
Cuando se produce el error
Entonces no queda ningún resultado del lote registrado a medias
```

### Escenario 5: Duplicado dentro del lote
```gherkin
Dado un lote donde un alumno ya tiene esa prueba en esa fecha
Cuando se procesa
Entonces esa fila se rechaza indicando el conflicto
Y el resto se informa según la política de atomicidad definida
```

### Escenario 6: Tutor sin permiso
```gherkin
Dado un tutor sin la sección asignada
Cuando envía el lote
Entonces el sistema devuelve 403 Forbidden
```

## Notas
* **Decisiones:** dejar un alumno en blanco significa **ausente**, no cero. Registrar ceros falsearía todas las medias del grupo y arrastraría a ese alumno a la lista de "sin progreso" de BE-34 sin motivo.
* **Contrato con la interfaz:** la respuesta debe permitir identificar la fila fallida por su alumno, para que la pantalla la señale sin perder lo tecleado en las demás. Es la razón de ser de esta historia.
* **Esta es la pantalla que más uso real tendrá**, así que el endpoint merece más cuidado del que sugiere su tamaño.
* **Testing:** escenarios 2, 3 y 4.

## Estimación
5 Puntos de Historia (Transacción con informe de errores por fila)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE22-01 | **Esquema del lote** Prueba, fecha y lista de resultados por alumno, con filas opcionales. | Yeremi | Hecho |
| T-BE22-02 | **Servicio de registro en lote** Validación previa de todas las filas antes de escribir. | Yeremi | Hecho |
| T-BE22-03 | **Manejo transaccional** Todo o nada, sin resultados a medias. | Yeremi | Hecho |
| T-BE22-04 | **Respuesta con errores por fila** Identificando el alumno afectado. | Yeremi | Hecho |
| T-BE22-05 | **Tests del lote** Escenarios 1 a 6. | Yeremi | Hecho |
