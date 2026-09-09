# Historia de Usuario

## ID
[BE-43]

## Título
Gestión de usuarios y asignación de roles

## Descripción
**Como** administrador
**Quiero** asignar roles y secciones a cada usuario

**Para** dar acceso al personal nuevo sin tocar la base de datos.

## Criterios de Aceptación

### Escenario 1: Listado de usuarios
```gherkin
Dado un administrador con sesión activa
Cuando consulta el listado de usuarios
Entonces recibe cada usuario con su rol y su último acceso
Y devuelve 200 OK
```

### Escenario 2: Cambio de rol
```gherkin
Dado un usuario con rol "pendiente"
Cuando el administrador le asigna el rol "tutor"
Entonces el usuario pasa a tener ese rol
Y sus permisos cambian en la siguiente petición
```

### Escenario 3: Asignación de secciones
```gherkin
Dado un usuario con rol "tutor"
Cuando el administrador le asigna dos secciones
Entonces el tutor accede a los alumnos de esas secciones
Y sigue recibiendo 403 para el resto
```

### Escenario 4: Último administrador protegido
```gherkin
Dado un sistema con un único administrador
Cuando ese administrador intenta quitarse su propio rol
Entonces el sistema deniega la operación
Y devuelve 409 Conflict explicando el motivo
```

### Escenario 5: Solo el administrador gestiona usuarios
```gherkin
Dado un usuario con rol coordinador
Cuando intenta cambiar el rol de otro usuario
Entonces el sistema devuelve 403 Forbidden
```

### Escenario 6: Traza de los cambios
```gherkin
Dado un cambio de rol completado
Cuando termina la operación
Entonces queda registrado en auditoría con quién lo hizo y el rol anterior
```

## Notas
* **Escenario 4 evita un bloqueo irrecuperable.** Sin esa comprobación, el último administrador puede dejarse sin permisos por error y nadie podría volver a asignarlos: haría falta entrar a la base de datos a mano.
* **Seguridad:** cambiar roles es la operación más sensible del sistema — concede acceso a datos de menores. Solo administrador, y siempre en auditoría.
* **Decisiones:** el cambio de rol surte efecto en la siguiente petición, no obliga a reautenticarse. La comprobación de permisos lee el rol de la base de datos, no de la sesión.
* **Testing:** escenarios 4 y 5.

## Estimación
5 Puntos de Historia (CRUD de usuarios con una regla de protección)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE43-01 | **Listado de usuarios** Con rol y último acceso, solo para administrador. | - | Pendiente |
| T-BE43-02 | **Cambio de rol** Con validación del rol destino. | - | Pendiente |
| T-BE43-03 | **Asignación de secciones** Alta y baja en `user_sections`. | - | Pendiente |
| T-BE43-04 | **Protección del último administrador** Comprobación antes de degradar. | - | Pendiente |
| T-BE43-05 | **Auditoría de cambios de rol** Con el valor anterior. | - | Pendiente |
| T-BE43-06 | **Tests de gestión** Escenarios 2 a 6. | - | Pendiente |
