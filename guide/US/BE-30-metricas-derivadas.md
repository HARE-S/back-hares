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

Este backend implementa las **tres métricas de la Batería de Lectura Eficaz (Bruño)**:
- **VE (Velocidad Espontánea)**: palabras por minuto leídas (sin comprensión)
- **CL (Comprensión Lectora)**: % de comprensión con penalización de errores
- **Vef (Velocidad Eficaz)**: palabras leídas Y comprendidas por minuto

### Escenario 1: Cálculo del PPM (VE)
```gherkin
Dado una prueba de 835 palabras
Y un resultado con 300 segundos de tiempo
Cuando se calcula el PPM (velocidad espontánea)
Entonces el valor devuelto es 167 palabras por minuto
```

### Escenario 2: Comprensión lectora con penalización (CL)
```gherkin
Dado un resultado con 15 aciertos, 3 fallos y 2 en blanco (20 preguntas fijas)
Cuando se calcula CL usando la fórmula P = aciertos − (fallos/2), luego (P/20)×100
Entonces P = 15 − 1.5 = 13.5
Y CL = (13.5/20)×100 = 67.5 por ciento

Nota: La penalización castiga respuestas incorrectas; respuestas en blanco no penalizan pero no puntúan.
Esto es muy distinto de "aciertos/(aciertos+errores)×100", que daría 83.3% (falso).
```

### Escenario 3: Tiempo cero (manejo de casos límite)
```gherkin
Dado un resultado cuyo tiempo es cero
Cuando se calcula el PPM
Entonces la función no lanza ninguna excepción
Y devuelve 0.0
```

### Escenario 4: Sin aciertos ni errores (manejo de casos límite)
```gherkin
Dado un resultado con cero aciertos y cero errores
Cuando se calcula CL
Entonces la función no lanza ninguna excepción
Y devuelve 0.0
```

### Escenario 5: Velocidad eficaz (Vef)
```gherkin
Dado PPM=174.4 y CL=67.5%
Cuando se calcula Vef = (PPM × CL) / 100
Entonces el valor devuelto es 117.7 palabras leídas y comprendidas por minuto

Nota: Vef es la métrica pedagógica que importa. Un lector rápido pero que no entiende
tiene baja Vef. Un lector lento pero que entiende bien también tiene baja Vef.
```

### Escenario 6: Cálculo sin base de datos
```gherkin
Dado las funciones de cálculo en analytics/
Cuando se ejecutan en una prueba unitaria
Entonces reciben números y devuelven números
Y no necesitan sesión de base de datos ni aplicación levantada
```

### Escenario 7: Presencia en todas las respuestas
```gherkin
Dado cualquier listado o detalle que devuelva resultados
Cuando se consulta
Entonces cada resultado incluye su PPM, CL y Vef
```

## Notas
* **Es el punto más peligroso del proyecto.** Un error aquí no rompe nada visible: produce un número plausible pero falso, y alguien toma decisiones pedagógicas sobre un alumno con ese número. Por eso `analytics/` es la capa con el objetivo de cobertura más alto (95%).
* **Cambio crítico en BE-30:** se descubrió que la implementación previa calculaba un porcentaje de aciertos simple (aciertos/(aciertos+errores)×100), que NO es la métrica de la Batería Bruño. La Batería penaliza los errores y usa 20 ítems fijos. El cambio afecta a todos los datos anteriores de BE-30 — necesitarán recálculo.
* **Decisiones:** el PPM se calcula, no se almacena. Almacenarlo obligaría a recalcularlo si se corrige el número de palabras de una prueba, y quedarían valores inconsistentes. Igual para CL y Vef.
* **Escenario 6 es de diseño, no de prueba:** `analytics/` no importa nada del resto del proyecto precisamente para que se pueda probar con listas de números inventados.
* **Testing:** escenarios 3, 4 y 5 son pruebas obligatorias. Escenario 2 es el que diferencia a la Batería Bruño de una métrica simple.

## Estimación
3 Puntos de Historia (Funciones simples con casos límite bien cubiertos)

## Prioridad
Crítica

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE30-01 | **Función de cálculo de PPM (VE)** En `analytics/metrics.py`, sin dependencias del proyecto. | Santiago | Completado |
| T-BE30-02 | **Función de comprensión lectora (CL) con penalización** Implementa Batería Bruño: P = aciertos − (fallos/2), CL = (P/20)×100. **REESCRITO para corregir definición anterior.** | Santiago | Completado |
| T-BE30-02b | **Función de velocidad eficaz (Vef)** Vef = (PPM × CL) / 100. Métrica pedagógica que combina velocidad y comprensión. | Santiago | Completado |
| T-BE30-03 | **Integración en los esquemas de respuesta** Campos calculados en todo resultado devuelto. | - | Pendiente |
| T-BE30-04 | **Tests unitarios de métricas** Escenarios 1 a 7, con valores conocidos, incluyendo Batería Bruño. | Santiago | Completado |

