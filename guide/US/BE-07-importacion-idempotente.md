# Historia de Usuario

## ID
[BE-07]

## Título
Importación idempotente

## Descripción
**Como** administrador
**Quiero** poder reimportar el mismo fichero sin generar duplicados

**Para** resincronizar cuando Alexia cambie sin ensuciar la base de datos.

## Criterios de Aceptación

### Escenario 1: Reimportación del mismo fichero
```gherkin
Dado que el fichero ya se ha importado una vez
Cuando se vuelve a ejecutar la importación con el mismo fichero
Entonces el recuento de filas de students es idéntico al anterior
Y el recuento de filas de student_sections es idéntico al anterior
Y el recuento de centers y sections es idéntico al anterior
```

### Escenario 2: Un alumno cambia de nombre en Alexia
```gherkin
Dado un alumno con external_id "STU01" ya registrado
Cuando se importa un fichero donde ese external_id tiene otro nombre
Entonces se actualiza el nombre del alumno existente
Y NO se crea un alumno nuevo
Y sus resultados y lecturas anteriores siguen asociados a él
```

### Escenario 3: Matrícula adicional
```gherkin
Dado un alumno matriculado en la sección "1CARMED2"
Cuando se importa un fichero donde figura en "1CARMED2, ITININSMAD"
Entonces se añade la matrícula en "ITININSMAD"
Y se conserva la matrícula en "1CARMED2"
```

### Escenario 4: Dos alumnos distintos con el mismo nombre
```gherkin
Dado dos filas con nombre "student 3" y external_id "STU03" y "STU17"
Cuando se importan
Entonces se crean dos alumnos independientes
Y la identidad se resuelve por external_id, nunca por nombre
```

### Escenario 5: Fila sin identificador de origen
```gherkin
Dado una fila cuyo external_id está vacío
Cuando se procesa
Entonces la fila se rechaza y se registra en el informe de errores
Y el resto del fichero se sigue procesando
```

## Notas
* **Decisiones:** la identidad se resuelve **siempre por `external_id`**, nunca por nombre. Comparar por nombre es frágil y se rompe con homónimos — y en los datos de prueba ya hay nombres repetidos. Sin `external_id` en el esquema (BE-03) esta historia es irrealizable.
* **Testing:** el escenario 1 es **prueba obligatoria** de `guides/testing.md`. Es la que hace usable la importación en producción y no solo en la demostración.
* **Dependencias:** requiere BE-03 y BE-06.

## Estimación
5 Puntos de Historia (La lógica es sencilla; el coste está en cubrir bien los casos de reimportación)

## Prioridad
Crítica

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE07-01 | **Resolución por external_id** Buscar antes de crear, en centros, secciones y alumnos. | Marlen | Completado |
| T-BE07-02 | **Actualización de existentes** Alumno encontrado se actualiza, no se recrea. | Marlen | Completado |
| T-BE07-03 | **Sincronización de matrículas** Crear las que falten conservando las existentes. | Marlen | Completado |
| T-BE07-04 | **Manejo transaccional por fila** Una fila inválida no aborta ni deja datos a medias. | Marlen | Completado |
| T-BE07-05 | **Test de idempotencia** Importar dos veces y comparar recuentos de las cuatro tablas. | Marlen | Completado |
| T-BE07-06 | **Tests de casos límite** Escenarios 2, 3, 4 y 5. | Marlen | Completado |
