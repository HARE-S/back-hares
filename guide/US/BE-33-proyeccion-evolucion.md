# Historia de Usuario

## ID
[BE-33]

## Título
Proyección de evolución

## Descripción
**Como** coordinador pedagógico
**Quiero** una estimación de hacia dónde va la progresión de un alumno

**Para** anticipar si alcanzará el nivel objetivo del curso.

## Criterios de Aceptación

### Escenario 1: Proyección con datos suficientes
```gherkin
Dado un alumno con cinco resultados en fechas distintas
Cuando se solicita su proyección
Entonces se devuelve una tendencia calculada sobre su histórico
Y se indica el número de pruebas en que se basa
```

### Escenario 2: Datos insuficientes
```gherkin
Dado un alumno con dos resultados
Cuando se solicita su proyección
Entonces no se devuelve ninguna proyección
Y se indica que hacen falta al menos tres pruebas
Y devuelve 200 OK, no un error
```

### Escenario 3: Marcado explícito como estimación
```gherkin
Dado una proyección calculada
Cuando se consulta la respuesta
Entonces los valores proyectados están marcados como estimación
Y son distinguibles de los valores medidos
```

### Escenario 4: Tendencia plana
```gherkin
Dado un alumno cuyos resultados no varían
Cuando se solicita su proyección
Entonces se devuelve una tendencia plana
Y no se fuerza una pendiente inexistente
```

### Escenario 5: Cálculo sin base de datos
```gherkin
Dado la función de proyección
Cuando se prueba con una lista de valores conocidos
Entonces devuelve el resultado esperado
Y no necesita base de datos ni aplicación levantada
```

## Notas
* **Es el requisito más vago del papel del cliente:** "componer proyecciones de evolución", sin más detalle. También es el que más puede crecer sin límite.
* **Recomendación:** empezar por una **regresión lineal simple** sobre el histórico y validar su utilidad con el equipo de pedagogía antes de invertir en nada más sofisticado. Conviene acordar por escrito qué se considera suficiente.
* **Decisiones:** el mínimo de tres pruebas es arbitrario pero necesario. Con dos puntos, una recta pasa exactamente por ambos y la proyección resultante es una ilusión de precisión.
* **Escenario 3 no es cosmético:** presentar una estimación con el mismo aspecto que un dato medido induce a tomarla por cierta. La distinción viaja desde el backend, no se deja al criterio de la interfaz.
* **Testing:** escenario 2 es prueba obligatoria.

## Estimación
8 Puntos de Historia (El alcance abierto pesa más que el cálculo)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE33-01 | **Regresión lineal simple** En `analytics/projection.py`, sin dependencias del proyecto. | - | Pendiente |
| T-BE33-02 | **Umbral mínimo de pruebas** Configurable, con respuesta explicativa por debajo. | - | Pendiente |
| T-BE33-03 | **Marcado de valores estimados** Distinguibles de los medidos en la respuesta. | - | Pendiente |
| T-BE33-04 | **Endpoint de proyección** Con permiso sobre el alumno. | - | Pendiente |
| T-BE33-05 | **Tests de proyección** Escenarios 1, 2 y 4 con series conocidas. | - | Pendiente |
| T-BE33-06 | **Validación con pedagogía** Presentar el resultado y acordar si es suficiente. | - | Pendiente |
