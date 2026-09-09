# Historia de Usuario

## ID
[BE-49]

## Título
Manual de uso de las funciones de servidor

## Descripción
**Como** administrador
**Quiero** una guía de las operaciones de administración

**Para** poder usarlas sin depender del equipo de desarrollo.

## Criterios de Aceptación

### Escenario 1: Procedimiento de importación
```gherkin
Dado un administrador que recibe un nuevo volcado de Alexia
Cuando consulta el manual
Entonces encuentra el procedimiento de importación paso a paso
Y qué hacer si aparecen errores en el informe
```

### Escenario 2: Gestión de usuarios
```gherkin
Dado un administrador que debe dar acceso a personal nuevo
Cuando consulta el manual
Entonces encuentra cómo asignar rol y secciones
Y qué significa cada rol
```

### Escenario 3: Lenguaje comprensible
```gherkin
Dado el manual completo
Cuando lo lee alguien sin perfil técnico
Entonces lo entiende sin conocer la arquitectura del sistema
Y está escrito en castellano
```

### Escenario 4: Procedimientos de operación
```gherkin
Dado una incidencia habitual
Cuando se consulta el manual
Entonces encuentra cómo revocar un acceso
Y cómo consultar el registro de auditoría
```

### Escenario 5: Actualizado con el sistema
```gherkin
Dado un cambio en un procedimiento documentado
Cuando se fusiona ese cambio
Entonces el manual se actualiza en el mismo commit
```

## Notas
* **Alcance:** este manual cubre las operaciones de administración que tienen su origen en el servidor —importación, usuarios, auditoría—. El uso diario de tutores y coordinadores se documenta desde la interfaz.
* **Escenario 5 es lo que evita que el manual muera.** Un documento que se actualiza "cuando haya tiempo" queda obsoleto en un mes y deja de consultarse.
* **Decisiones:** en castellano y sin jerga. El destinatario no es un desarrollador; si necesita entender qué es un endpoint para importar un fichero, el manual ha fallado.

## Estimación
2 Puntos de Historia (Redacción sobre funcionalidad ya construida)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE49-01 | **Procedimiento de importación** Paso a paso, con el tratamiento de errores. | - | Pendiente |
| T-BE49-02 | **Guía de gestión de usuarios** Roles, asignación de secciones y revocación. | - | Pendiente |
| T-BE49-03 | **Consulta de auditoría** Cómo y para qué. | - | Pendiente |
| T-BE49-04 | **Revisión de comprensión** Que lo lea alguien ajeno al equipo de desarrollo. | - | Pendiente |
