# Historia de Usuario

## ID
[BE-31]

## Título
Evolución individual de un alumno

## Descripción
**Como** tutor
**Quiero** ver la progresión de un alumno a lo largo del tiempo

**Para** saber si el programa está funcionando con él.

## Criterios de Aceptación

### Escenario 1: Serie temporal
```gherkin
Dado un alumno con cinco resultados en fechas distintas
Cuando se consulta su evolución
Entonces se devuelve una serie de PPM ordenada por fecha
Y una serie de porcentaje de aciertos ordenada por fecha
```

### Escenario 2: Acotación por fechas
```gherkin
Dado un alumno con resultados de dos cursos
Cuando se consulta su evolución acotada a un rango de fechas
Entonces solo se incluyen los resultados de ese rango
```

### Escenario 3: Variación entre extremos
```gherkin
Dado un alumno con resultados desde marzo hasta junio
Cuando se consulta su evolución
Entonces se indica la variación entre la primera y la última prueba
Y se expresa tanto en valor absoluto como en porcentaje
```

### Escenario 4: Datos insuficientes
```gherkin
Dado un alumno con una sola prueba registrada
Cuando se consulta su evolución
Entonces se devuelve un indicador de datos insuficientes
Y devuelve 200 OK, no un error
Y la serie no se presenta como si fuera una tendencia
```

### Escenario 5: Sin resultados
```gherkin
Dado un alumno sin ninguna prueba
Cuando se consulta su evolución
Entonces se devuelve una serie vacía con el indicador correspondiente
```

## Notas
* **Decisiones:** con menos de dos puntos no hay evolución, hay un dato. Devolver una serie de un elemento invitaría a la interfaz a dibujar un gráfico que sugiere una tendencia inexistente. Por eso el indicador explícito.
* **Depende de BE-19:** si la restricción de pruebas sucesivas está mal, esta historia recibe un único resultado por alumno y sección y no tiene nada que representar.
* **Contrato con la interfaz:** el indicador de datos insuficientes es lo que permite a la pantalla mostrar un mensaje en vez de un gráfico vacío.
* **Testing:** escenarios 3 y 4.

## Estimación
5 Puntos de Historia (Series temporales con acotación y casos de datos escasos)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE31-01 | **Construcción de la serie** En `analytics/evolution.py`, a partir de una lista de resultados. | - | Pendiente |
| T-BE31-02 | **Acotación por rango de fechas** Parámetros opcionales de inicio y fin. | - | Pendiente |
| T-BE31-03 | **Cálculo de la variación** Absoluta y porcentual entre extremos. | - | Pendiente |
| T-BE31-04 | **Indicador de datos insuficientes** Con el umbral documentado. | - | Pendiente |
| T-BE31-05 | **Endpoint de evolución** Con comprobación de permiso sobre el alumno. | - | Pendiente |
| T-BE31-06 | **Tests de evolución** Escenarios 1 a 5 con series conocidas. | - | Pendiente |
