# Historia de Usuario

## ID
[BE-09]

## Título
Endpoint de subida del fichero de importación

## Descripción
**Como** administrador
**Quiero** subir el fichero de Alexia desde el navegador

**Para** no depender de acceso al servidor ni de contenedores.

## Criterios de Aceptación

### Escenario 1: Subida y previsualización
```gherkin
Dado un administrador con sesión activa
Cuando sube un CSV válido
Entonces el sistema devuelve una previsualización de las primeras filas
Y no ha escrito todavía nada en la base de datos
```

### Escenario 2: Confirmación de la importación
```gherkin
Dado un fichero ya subido y previsualizado
Cuando el administrador confirma la importación
Entonces se ejecuta el proceso de BE-06 y BE-07
Y se devuelve el resumen de la ejecución
```

### Escenario 3: Extensión no permitida
```gherkin
Dado un fichero con una extensión distinta a las permitidas
Cuando se intenta subir
Entonces el sistema lo rechaza
Y devuelve 400 Bad Request indicando las extensiones válidas
```

### Escenario 4: Fichero demasiado grande
```gherkin
Dado un fichero que supera el tamaño máximo configurado
Cuando se intenta subir
Entonces el sistema lo rechaza con un mensaje claro
```

### Escenario 5: Usuario sin permiso
```gherkin
Dado un usuario con rol tutor y sesión activa
Cuando intenta subir un fichero de importación
Entonces el sistema deniega la operación
Y devuelve 403 Forbidden
```

## Notas
* **Decisiones:** este endpoint **reutiliza el mismo módulo de validación que el importador por línea de comandos**. Dos caminos de escritura con dos validaciones acabarán divergiendo — alguien corregirá un caso raro en uno y no en el otro. Ver `guides/structure.md`, apartado 3.
* **Pendiente con el cliente:** definir si el contenedor `import` es un job puntual de arranque o el mecanismo permanente. Mientras no se decida, ambos caminos comparten código.
* **Infraestructura:** el proxy debe permitir el tamaño de subida; por defecto nginx corta en 1 MB y devolvería `413`.
* **Testing:** escenarios 3, 4 y 5.

## Estimación
5 Puntos de Historia (Subida, previsualización, confirmación y reutilización del validador)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE09-01 | **Endpoint de subida** Recepción del fichero con validación de extensión y tamaño. | - | Pendiente |
| T-BE09-02 | **Previsualización** Devolver las primeras filas parseadas sin escribir en base de datos. | - | Pendiente |
| T-BE09-03 | **Endpoint de confirmación** Ejecutar la importación sobre el fichero previamente subido. | - | Pendiente |
| T-BE09-04 | **Reutilización del validador** Mismo módulo que `importer/`, sin duplicar lógica. | - | Pendiente |
| T-BE09-05 | **Restricción por rol** Solo administrador; `403` para el resto. | - | Pendiente |
| T-BE09-06 | **Tests del endpoint** Escenarios 1 a 5. | - | Pendiente |
