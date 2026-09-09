# Historia de Usuario

## ID
[BE-44]

## Título
Revocación de acceso y registro de auditoría

## Descripción
**Como** responsable pedagógico
**Quiero** poder retirar el acceso de inmediato y saber quién ha consultado qué

**Para** poder responder ante una incidencia con datos de menores.

## Criterios de Aceptación

### Escenario 1: Revocación inmediata
```gherkin
Dado un usuario con sesiones activas
Cuando un administrador lo deshabilita
Entonces todas sus sesiones quedan invalidadas al momento
Y su siguiente petición devuelve 401 Unauthorized
```

### Escenario 2: Registro de accesos
```gherkin
Dado un usuario que consulta datos de alumnado
Cuando se completa la petición
Entonces queda registrado quién accedió, cuándo y a qué recurso
```

### Escenario 3: Registro de modificaciones
```gherkin
Dado una modificación o eliminación de un resultado
Cuando se completa la operación
Entonces queda registrada con el usuario y el valor anterior
```

### Escenario 4: Registro de exportaciones
```gherkin
Dado una exportación de datos completada
Cuando termina la descarga
Entonces queda registrada con el usuario y el ámbito exportado
```

### Escenario 5: Consulta del registro
```gherkin
Dado un administrador con sesión activa
Cuando consulta la auditoría filtrando por usuario y por rango de fechas
Entonces recibe las entradas correspondientes
```

### Escenario 6: Registro no editable
```gherkin
Dado el registro de auditoría
Cuando se intenta modificar o eliminar una entrada desde la aplicación
Entonces la operación no está disponible
Y no existe ningún endpoint que lo permita
```

## Notas
* **Desfase inherente que conviene conocer:** si el centro desactiva la cuenta de Google de alguien, esta aplicación no se entera hasta que esa persona intenta reautenticarse. Por eso la caducidad de sesión de BE-40 no debe ser larga, y por eso hace falta la revocación manual de esta historia.
* **Decisiones:** la auditoría registra accesos a datos de alumnado, modificaciones y exportaciones. No registra consultas al catálogo de pruebas o libros, que no contienen datos personales — registrarlo todo generaría tanto ruido que nadie lo consultaría.
* **Escenario 6 es la razón de ser del registro.** Un log que se puede editar desde la aplicación no sirve como evidencia ante una incidencia.
* **Relación con pgAdmin:** las correcciones de datos se hacen por la aplicación, nunca con un `UPDATE` directo, precisamente porque un cambio desde pgAdmin no deja rastro aquí.
* **Testing:** escenarios 1 y 6.

## Estimación
5 Puntos de Historia (Registro transversal más revocación)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE44-01 | **Módulo de auditoría** En `core/audit.py`, con la estructura de entrada definida. | - | Pendiente |
| T-BE44-02 | **Registro de accesos a datos de alumnado** Aplicado en los servicios correspondientes. | - | Pendiente |
| T-BE44-03 | **Registro de modificaciones con valor anterior** En resultados, lecturas y roles. | - | Pendiente |
| T-BE44-04 | **Registro de exportaciones** Usuario y ámbito. | - | Pendiente |
| T-BE44-05 | **Revocación de sesiones al deshabilitar** Borrado de sesiones activas del usuario. | - | Pendiente |
| T-BE44-06 | **Endpoint de consulta de auditoría** Solo lectura, filtrable, solo administrador. | - | Pendiente |
| T-BE44-07 | **Tests de auditoría y revocación** Escenarios 1 a 5. | - | Pendiente |
