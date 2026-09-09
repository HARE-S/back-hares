# Historia de Usuario

## ID
[BE-17]

## Título
Carga inicial del catálogo de libros

## Descripción
**Como** administrador
**Quiero** partir del listado histórico de libros del centro

**Para** no reconstruir a mano un catálogo de más de cien títulos.

## Criterios de Aceptación

### Escenario 1: Importación de filas válidas
```gherkin
Dado el Excel de listado de libros del centro
Cuando se ejecuta la importación
Entonces se crean los libros con su título y su nivel
Y se informa del número de libros creados
```

### Escenario 2: Filas de cabecera repetidas
```gherkin
Dado un fichero con cabeceras repetidas a mitad de la hoja
Cuando se procesa
Entonces esas filas se ignoran
Y no se crean libros con títulos como "Título" o "Nivel"
```

### Escenario 3: Rótulos de sección
```gherkin
Dado filas que contienen rótulos como "ELIGE TU PROPIA AVENTURA"
    o "TALLER DE LITERATURA"
Cuando se procesan
Entonces se reconocen como separadores y no como libros
```

### Escenario 4: Campos de inventario no numéricos
```gherkin
Dado filas con "11 Fotocopias", "PDF" o "12 + 6 fotocopias" en ejemplares
Y con "PREPARAR", "4 o 5" o "5+" en sesiones
Cuando se procesan
Entonces esos valores se guardan como texto libre
Y no provocan el rechazo de la fila
```

### Escenario 5: Filas no interpretables
```gherkin
Dado una fila que no permite extraer título ni nivel
Cuando se procesa
Entonces se añade a un listado aparte para revisión manual
Y el resto del fichero continúa
```

## Notas
* **Riesgo de planificación.** El Excel entregado **no es importable automáticamente sin pérdidas**. Contiene cinco hojas, cabeceras repetidas, tres columnas "Centro y nº libros", texto suelto al final, y un valor `43075` en la columna de sesiones que es **una fecha convertida por Excel a número de serie**. Es una hoja mantenida a mano durante años.
* **Recomendación:** acordar con el cliente una **limpieza manual previa** del fichero. Intentar parsearlo tal cual consumirá días sin resultado fiable.
* **Dependencias:** requiere BE-15 (niveles) y BE-16 (modelo de libro).
* **Testing:** escenarios 2, 3 y 4 con el fichero real.

## Estimación
8 Puntos de Historia (El coste está en la limpieza de datos, no en la lógica)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE17-01 | **Lectura del Excel** Localizar la hoja y el rango de datos útil. | - | Pendiente |
| T-BE17-02 | **Detección de filas no válidas** Cabeceras repetidas, rótulos de sección y texto suelto. | - | Pendiente |
| T-BE17-03 | **Normalización de niveles** Del texto "Nivel 0-I" al valor de la enumeración de BE-15. | - | Pendiente |
| T-BE17-04 | **Campos de inventario como texto** `copies_note` y `sessions_note` sin conversión numérica. | - | Pendiente |
| T-BE17-05 | **Listado de revisión manual** Filas no interpretables, exportables. | - | Pendiente |
| T-BE17-06 | **Tests con el fichero real** Escenarios 2, 3 y 4. | - | Pendiente |
