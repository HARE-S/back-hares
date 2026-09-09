# Historia de Usuario

## ID
[BE-41]

## Título
Alta de usuario en el primer acceso

## Descripción
**Como** administrador
**Quiero** que quien entra por primera vez quede registrado sin acceso a datos

**Para** no tener que dar de alta manualmente a cada persona antes de que use la aplicación.

## Criterios de Aceptación

### Escenario 1: Primer acceso
```gherkin
Dado un usuario del dominio que nunca ha entrado
Cuando completa el flujo de autenticación
Entonces se crea su usuario con rol "pendiente"
Y se guardan su google_sub, email y nombre
```

### Escenario 2: Un usuario pendiente no ve datos
```gherkin
Dado un usuario con rol "pendiente" y sesión activa
Cuando consulta cualquier endpoint de alumnado, resultados o informes
Entonces el sistema devuelve 403 Forbidden
Y no devuelve ningún dato de alumnado
```

### Escenario 3: Accesos posteriores
```gherkin
Dado un usuario ya registrado
Cuando vuelve a autenticarse
Entonces se actualizan su nombre y su foto desde Google
Y se registra la fecha de su último acceso
Y NO se crea un usuario nuevo
```

### Escenario 4: Cambio de correo en Google
```gherkin
Dado un usuario registrado cuyo google_sub es conocido
Cuando Google devuelve ese mismo google_sub con otra dirección de correo
Entonces se actualiza el correo del usuario existente
Y conserva su rol y sus secciones asignadas
```

### Escenario 5: Aviso a los administradores
```gherkin
Dado uno o más usuarios con rol "pendiente"
Cuando un administrador consulta el listado de usuarios
Entonces se le indica que hay usuarios esperando asignación de permisos
```

## Notas
* **Escenario 4 es el motivo de usar `google_sub` como identidad.** Google puede cambiar la dirección de una persona —cambio de apellido, corrección de alias— manteniendo el mismo `sub`. Si la identidad se ancla al correo, ese usuario aparece como una persona nueva y pierde su rol, sus secciones y su rastro de auditoría.
* **Decisiones:** el rol `pendiente` evita los dos extremos malos. Pre-provisionar a mano es un cuello de botella; dar acceso completo por tener correo del dominio significa que el personal de administración o mantenimiento vería expedientes de menores.
* **Seguridad:** escenario 2 es obligatorio y debe comprobarse en el servidor, no solo ocultando pantallas.
* **Testing:** escenarios 2 y 4.

## Estimación
5 Puntos de Historia (Alta automática con estado intermedio y actualización por `sub`)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE41-01 | **Alta en el primer acceso** Crear usuario con rol `pendiente` a partir del ID token. | - | Pendiente |
| T-BE41-02 | **Resolución por google_sub** Actualizar el existente en vez de crear uno nuevo. | - | Pendiente |
| T-BE41-03 | **Bloqueo del rol pendiente** `403` en todo endpoint de datos. | - | Pendiente |
| T-BE41-04 | **Registro de último acceso** Actualizado en cada autenticación. | - | Pendiente |
| T-BE41-05 | **Indicador de pendientes** Para el listado de administración. | - | Pendiente |
| T-BE41-06 | **Tests de alta y actualización** Escenarios 1 a 4. | - | Pendiente |
