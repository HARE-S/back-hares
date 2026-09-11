# Historia de Usuario

## ID
[BE-08]

## Título
Informe de errores de importación

## Descripción
**Como** administrador
**Quiero** ver qué filas han fallado y por qué

**Para** poder corregir el fichero de origen sin adivinar.

## Criterios de Aceptación

### Escenario 1: Una fila inválida no detiene el proceso
```gherkin
Dado un fichero de 28 filas donde la número 12 es inválida
Cuando se ejecuta la importación
Entonces se procesan las 27 filas válidas
Y la fila 12 se registra como error
Y el resumen indica 27 procesadas y 1 con error
```

### Escenario 2: Detalle del error
```gherkin
Dado una fila rechazada
Cuando se consulta el informe de errores
Entonces cada error indica el número de línea
Y la columna afectada
Y el motivo del rechazo en lenguaje comprensible
```

### Escenario 3: Detección de casos concretos
```gherkin
Dado filas con external_id vacío, centro vacío, secciones malformadas
    o un número de columnas distinto al esperado
Cuando se procesan
Entonces cada una se rechaza con su motivo específico
Y ninguna genera un error genérico sin explicación
```

### Escenario 4: Descarga del informe
```gherkin
Dado una importación terminada con errores
Cuando el administrador solicita el informe
Entonces se descarga un fichero con la lista de errores
```

## Notas
* **Decisiones:** abortar el fichero entero por una fila mala obliga a repetir todo el proceso por un fallo trivial. Procesar lo válido y reportar lo demás es lo que hace usable la herramienta con ficheros reales.
* **Seguridad:** el informe puede contener fragmentos del fichero de origen, así que solo lo descarga el administrador y su descarga queda en auditoría.
* **Testing:** escenarios 1 y 3.

## Estimación
3 Puntos de Historia (Acumulación de errores y serialización)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE08-01 | **Acumulador de errores** Estructura con línea, columna y motivo por cada fila rechazada. | marlen713 | Completado |
| T-BE08-02 | **Validaciones con motivo específico** Los cuatro casos del escenario 3. | marlen713 | Completado |
| T-BE08-03 | **Endpoint de descarga del informe** Restringido a administrador. | marlen713 | Completado |
| T-BE08-04 | **Tests del informe** Escenarios 1 a 4. | marlen713 | Completado |
