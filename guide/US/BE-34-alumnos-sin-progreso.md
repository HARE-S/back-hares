# Historia de Usuario

## ID
[BE-34]

## Título
Detección de alumnos sin progreso

## Descripción
**Como** coordinador pedagógico
**Quiero** que el sistema me señale a quién no está mejorando

**Para** priorizar la atención sin revisar todas las fichas.

## Criterios de Aceptación

### Escenario 1: Detección de tendencia negativa
```gherkin
Dado alumnos cuyos resultados empeoran en las últimas pruebas
Cuando se consulta el listado de alumnos sin progreso
Entonces esos alumnos aparecen en la lista
```

### Escenario 2: Tendencia plana
```gherkin
Dado un alumno cuyos resultados no mejoran ni empeoran
Cuando se aplica el umbral configurado
Entonces se incluye en la lista si su variación está por debajo del umbral
```

### Escenario 3: Distinción de datos insuficientes
```gherkin
Dado un alumno con una sola prueba
Cuando se consulta el listado
Entonces aparece clasificado como "sin datos suficientes"
Y NO como "sin progreso"
```

### Escenario 4: Parámetros configurables
```gherkin
Dado el listado de alumnos sin progreso
Cuando se consulta indicando otro umbral y otro número de pruebas
Entonces el cálculo usa esos parámetros
Y no valores fijos escritos en el código
```

### Escenario 5: Alcance por rol
```gherkin
Dado un tutor con dos secciones asignadas
Cuando consulta el listado
Entonces solo aparecen alumnos de sus secciones
```

## Notas
* **Escenario 3 es el importante.** Confundir "no tengo datos de este alumno" con "este alumno no progresa" llevaría a intervenir sobre quien simplemente no ha hecho pruebas todavía, y a no intervenir sobre quien sí lo necesita. Son dos listas distintas.
* **Decisiones:** umbral y número de pruebas configurables porque lo que cuenta como falta de progreso depende del nivel de partida y del criterio pedagógico, no de una constante técnica.
* **Uso previsto:** listado de trabajo del coordinador, no una etiqueta permanente sobre el alumno. No se almacena ninguna clasificación en su ficha.
* **Testing:** escenario 3.

## Estimación
5 Puntos de Historia (Reutiliza la tendencia de BE-33 con clasificación y umbrales)

## Prioridad
Baja

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE34-01 | **Clasificación de alumnos** Reutilizando la tendencia de `analytics/projection.py`. | - | Pendiente |
| T-BE34-02 | **Separación de "sin datos suficientes"** Categoría propia, nunca mezclada. | - | Pendiente |
| T-BE34-03 | **Parámetros configurables** Umbral y número de pruebas por parámetro. | - | Pendiente |
| T-BE34-04 | **Endpoint del listado** Con filtrado por ámbito del usuario. | - | Pendiente |
| T-BE34-05 | **Tests de clasificación** Escenarios 1, 2, 3 y 5. | - | Pendiente |
