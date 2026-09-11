# Historia de Usuario

## ID
[BE-35]

## Título
Exportación de datos a Excel

## Descripción
**Como** coordinador pedagógico
**Quiero** descargar los datos filtrados en una hoja de cálculo

**Para** poder trabajarlos y compartirlos fuera de la aplicación.

## Criterios de Aceptación

### Escenario 1: Exportación del conjunto filtrado
```gherkin
Dado un conjunto de resultados con filtros aplicados
Cuando se solicita la exportación con esos mismos filtros
Entonces el fichero contiene exactamente ese conjunto
Y no el conjunto completo sin filtrar
```

### Escenario 2: Formato del fichero
```gherkin
Dado una exportación solicitada
Cuando se descarga el fichero
Entonces es un .xlsx válido
Y sus cabeceras están en castellano y son legibles
```

### Escenario 3: Métricas incluidas
```gherkin
Dado una exportación de resultados
Cuando se abre el fichero
Entonces cada fila incluye el PPM y el porcentaje de aciertos
Y no solo el tiempo, los aciertos y los errores
```

### Escenario 4: Tipos de dato correctos
```gherkin
Dado una exportación con fechas y valores decimales
Cuando se abre el fichero en una hoja de cálculo
Entonces las fechas se reconocen como fechas
Y los decimales como números
Y ninguno de los dos aparece como texto
```

### Escenario 5: Conjunto vacío
```gherkin
Dado unos filtros que no devuelven ningún resultado
Cuando se solicita la exportación
Entonces se genera un fichero con solo las cabeceras
Y no se produce un error
```

### Escenario 6: Registro de la exportación
```gherkin
Dado una exportación completada
Cuando termina la descarga
Entonces queda registrada en auditoría con el usuario y el ámbito exportado
```

## Notas
* **La especificación de API entregada por el cliente no contempla ningún endpoint de exportación**, pese a ser un requisito explícito del papel. Hay que añadirlo.
* **Escenario 4 es el que más se descuida.** Una fecha exportada como texto no se puede ordenar ni filtrar en Excel, y un decimal como texto no se puede promediar. El destinatario notará el problema justo cuando intente usar el fichero.
* **Seguridad:** una exportación saca datos de menores del sistema. Queda en auditoría (BE-44) y se limita al ámbito del usuario.
* **Testing:** escenarios 1, 4 y 5.

## Estimación
5 Puntos de Historia (Generación de fichero con formatos correctos)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE35-01 | **Generador de xlsx** En `exports/excel.py`, con cabeceras en castellano. | Yeremi | Completado |
| T-BE35-02 | **Aplicación de los filtros recibidos** Reutilizando los de BE-27. | Yeremi | Completado |
| T-BE35-03 | **Formato de fechas y decimales** Tipos reales, no texto. | Yeremi | Completado |
| T-BE35-04 | **Endpoint de exportación** Con restricción de ámbito por rol. | Yeremi | Completado |
| T-BE35-05 | **Registro en auditoría** Usuario y ámbito exportado. | Yeremi | Completado |
| T-BE35-06 | **Tests de exportación** Escenarios 1, 4 y 5, abriendo el fichero generado. | Yeremi | Completado |
