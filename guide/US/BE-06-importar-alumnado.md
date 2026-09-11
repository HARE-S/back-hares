# Historia de Usuario

## ID
[BE-06]

## Título
Importar alumnado desde el volcado de Alexia

## Descripción
**Como** administrador
**Quiero** cargar el volcado de Alexia desde un fichero

**Para** no tener que dar de alta a cientos de alumnos a mano.

## Criterios de Aceptación

### Escenario 1: Importación de un fichero correcto
```gherkin
Dado un CSV con separador punto y coma y codificación UTF-8
Y con las columnas student_id, student_name, sections y center
Cuando se ejecuta la importación
Entonces se crean los centros, secciones, alumnos y matrículas
Y se muestra un resumen con creados, actualizados, omitidos y errores
```

### Escenario 2: Campo de secciones multivalor
```gherkin
Dado una fila cuya columna sections contiene "1CARMED2,JB25480021,ITININSMAD"
Cuando se procesa esa fila
Entonces se generan tres matrículas para ese alumno
Y cada una apunta a una sección distinta
```

### Escenario 3: Centro no existente
```gherkin
Dado una fila con el centro "Boluetaberri" que no está en la base de datos
Cuando se procesa esa fila
Entonces se crea el centro
Y el alumno queda asociado a él a través de sus secciones
```

### Escenario 4: Sección no existente
```gherkin
Dado una fila con una sección que no está registrada
Cuando se procesa esa fila
Entonces se crea la sección asociada al centro de la fila
```

### Escenario 5: Fichero con codificación o separador incorrectos
```gherkin
Dado un fichero que no usa punto y coma como separador
Cuando se intenta importar
Entonces el proceso se detiene con un mensaje claro
Y no se crea ningún registro parcial
```

## Notas
* **Formato real del fichero:** el campo `sections` es **multivalor separado por comas dentro de un fichero separado por punto y coma**. El centro llega por nombre, no por código.
* **Seguridad:** solo rol administrador. La importación queda en auditoría con el número de filas procesadas; **nunca se vuelcan datos de alumnado a los logs**.
* **Relación con otras historias:** la lógica de alta o actualización sin duplicar está en BE-07; el informe de errores en BE-08. Esta historia cubre la lectura y el alta inicial.
* **Testing:** escenario 2 es prueba obligatoria.

## Estimación
8 Puntos de Historia (Lectura, resolución de tres entidades relacionadas y manejo transaccional)

## Prioridad
Crítica

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE06-01 | **Lector de CSV** Separador `;`, UTF-8, validación de cabeceras esperadas. | Marlen | Completado |
| T-BE06-02 | **Parseo de la fila** Extraer alumno, centro y lista de secciones; dividir el multivalor. | Marlen | Completado |
| T-BE06-03 | **Alta de centros y secciones** Crear las que falten antes de matricular. | Marlen | Completado |
| T-BE06-04 | **Alta de alumnos y matrículas** Una fila en `student_sections` por sección. | Marlen | Completado |
| T-BE06-05 | **Resumen de ejecución** Contadores de creados, actualizados, omitidos y errores. | Marlen | Completado |
| T-BE06-06 | **Tests de importación** Escenarios 1 a 5 con el fichero real de ejemplo. | Marlen | Completado |
