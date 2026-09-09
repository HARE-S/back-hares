# Historia de Usuario

## ID
[BE-30]

## Título
Métricas derivadas de comprensión lectora

## Descripción
**Como** coordinador pedagógico
**Quiero** que el sistema calcule las métricas de comprensión lectora

**Para** no tener que hacer las cuentas a mano en una hoja de cálculo.

## Criterios de Aceptación

### Escenario 1: Cálculo del PPM
```gherkin
Dado una prueba de 835 palabras
Y un resultado con 300 segundos de tiempo
Cuando se calcula el PPM
Entonces el valor devuelto es 167 palabras por minuto
```

### Escenario 2: Porcentaje de aciertos
```gherkin
Dado un resultado con 8 aciertos y 2 errores
Cuando se calcula el porcentaje de aciertos
Entonces el valor devuelto es 80 por ciento
```

### Escenario 3: Tiempo cero
```gherkin
Dado un resultado cuyo tiempo es cero
Cuando se calcula el PPM
Entonces la función no lanza ninguna excepción
Y devuelve un valor definido documentado
```

### Escenario 4: Sin aciertos ni errores
```gherkin
Dado un resultado con cero aciertos y cero errores
Cuando se calcula el porcentaje de aciertos
Entonces la función no lanza ninguna excepción
Y devuelve un valor definido documentado
```

### Escenario 5: Presencia en todas las respuestas
```gherkin
Dado cualquier listado o detalle que devuelva resultados
Cuando se consulta
Entonces cada resultado incluye su PPM y su porcentaje de aciertos
```

### Escenario 6: Cálculo sin base de datos
```gherkin
Dado las funciones de cálculo
Cuando se ejecutan en una prueba unitaria
Entonces reciben números y devuelven números
Y no necesitan sesión de base de datos ni aplicación levantada
```

## Notas
* **Es el punto más peligroso del proyecto.** Un error aquí no rompe nada visible: produce un número plausible pero falso, y alguien toma decisiones pedagógicas sobre un alumno con ese número. Por eso `analytics/` es la capa con el objetivo de cobertura más alto (95%).
* **Decisiones:** el PPM se calcula, no se almacena. Almacenarlo obligaría a recalcularlo si se corrige el número de palabras de una prueba, y quedarían valores inconsistentes.
* **Escenario 6 es de diseño, no de prueba:** `analytics/` no importa nada del resto del proyecto precisamente para que se pueda probar con listas de números inventados.
* **Testing:** escenarios 3 y 4 son pruebas obligatorias.

## Estimación
3 Puntos de Historia (Funciones simples con casos límite bien cubiertos)

## Prioridad
Crítica

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE30-01 | **Función de cálculo de PPM** En `analytics/metrics.py`, sin dependencias del proyecto. | - | Pendiente |
| T-BE30-02 | **Función de porcentaje de aciertos** Con su caso de denominador cero definido. | - | Pendiente |
| T-BE30-03 | **Integración en los esquemas de respuesta** Campos calculados en todo resultado devuelto. | - | Pendiente |
| T-BE30-04 | **Tests unitarios de métricas** Escenarios 1 a 4, con valores conocidos. | - | Pendiente |
