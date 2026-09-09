# Historia de Usuario

## ID
[BE-05]

## Título
Datos de prueba anónimos

## Descripción
**Como** desarrollador
**Quiero** poblar la base de datos con datos anónimos realistas

**Para** poder probar el sistema sin manejar datos personales de menores.

## Criterios de Aceptación

### Escenario 1: Carga inicial
```gherkin
Dado una base de datos migrada y vacía
Cuando se ejecuta el comando de carga de datos de prueba
Entonces se crean los 28 alumnos de import_data.csv
Y se crean las 34 pruebas de tests.csv
Y se crea un catálogo mínimo de libros
```

### Escenario 2: Resultados sintéticos con evolución
```gherkin
Dado los alumnos cargados
Cuando termina la carga
Entonces cada alumno tiene al menos tres resultados
Y esos resultados están en fechas distintas
Y permiten calcular una evolución
```

### Escenario 3: Idempotencia del comando
```gherkin
Dado que el comando ya se ha ejecutado una vez
Cuando se ejecuta de nuevo
Entonces no se duplica ningún registro
Y el recuento de filas permanece igual
```

### Escenario 4: Ausencia de datos reales
```gherkin
Dado el conjunto de datos cargado
Cuando se inspeccionan los nombres de alumnado
Entonces son identificadores anónimos del tipo "student N"
Y no contienen ningún dato personal real
```

## Notas
* **Requisito explícito del cliente:** "inicialmente partimos de una carga de datos anónimos para probar el sistema".
* **Seguridad:** los datos de prueba se **generan**, nunca se copian de producción. Son datos de menores.
* **Utilidad:** este conjunto es el que usan las pruebas automatizadas y las demostraciones de sprint. Sin evolución sintética, BE-31 a BE-34 no se pueden demostrar.
* **Testing:** el escenario 3 se comprueba ejecutando el comando dos veces y comparando recuentos.

## Estimación
3 Puntos de Historia (Lectura de los CSV ya disponibles más generación de resultados)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE05-01 | **Comando de carga** Punto de entrada ejecutable dentro del contenedor. | - | Pendiente |
| T-BE05-02 | **Carga de maestros y catálogos** Reutilizar el importador de BE-07 y el de pruebas de BE-12. | - | Pendiente |
| T-BE05-03 | **Generación de resultados sintéticos** Mínimo tres por alumno, en fechas separadas y con tendencia variada. | - | Pendiente |
| T-BE05-04 | **Idempotencia** Comprobar existencia antes de crear. | - | Pendiente |
| T-BE05-05 | **Test del comando** Escenarios 1 a 3. | - | Pendiente |
