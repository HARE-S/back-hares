# Historia de Usuario

## ID
[BE-42]

## Título
Perfiles de permisos por rol

## Descripción
**Como** administrador
**Quiero** que cada rol vea y modifique solo lo que le corresponde

**Para** que un tutor no pueda alterar el catálogo ni ver datos de otro centro.

## Criterios de Aceptación

### Escenario 1: Roles diferenciados
```gherkin
Dado los roles pendiente, tutor, coordinador, responsable y administrador
Cuando cada uno accede a la aplicación
Entonces sus permisos son distintos y están definidos explícitamente
```

### Escenario 2: Tutor limitado a sus secciones
```gherkin
Dado un tutor con dos secciones asignadas
Cuando consulta o modifica datos de un alumno de otra sección
Entonces el sistema devuelve 403 Forbidden
```

### Escenario 3: Tutor sin acceso al catálogo
```gherkin
Dado un tutor con sesión activa
Cuando intenta crear, modificar o eliminar una prueba o un libro
Entonces el sistema devuelve 403 Forbidden
Y sí puede consultarlos
```

### Escenario 4: Comprobación en el servidor
```gherkin
Dado una operación no permitida para el rol del usuario
Cuando se envía directamente al endpoint sin pasar por la interfaz
Entonces el sistema la rechaza igualmente con 403 Forbidden
```

### Escenario 5: Cobertura completa
```gherkin
Dado el conjunto de endpoints bajo /api
Cuando se revisan uno a uno
Entonces todos declaran explícitamente qué roles pueden usarlos
Y ninguno queda sin comprobación
```

### Escenario 6: Distinción entre 401 y 403
```gherkin
Dado una petición sin sesión, el sistema devuelve 401
Y dado una petición con sesión pero sin permiso, el sistema devuelve 403
Entonces ambos casos son distinguibles por la interfaz
```

## Notas
* **Ocultar un botón no es seguridad.** La interfaz oculta las acciones no permitidas para no confundir; el backend las rechaza para proteger. Ambas cosas, siempre. El escenario 4 verifica precisamente que la protección no depende de la interfaz.
* **Escenario 6 es contrato con la interfaz:** `401` significa "no sé quién eres" y lleva al login; `403` significa "sé quién eres y no puedes" y muestra un mensaje. Confundirlos mete al usuario en un bucle de login.
* **Escenario 5 es una revisión, no código.** Merece un repaso explícito antes de cerrar la historia: un endpoint sin comprobación no falla, simplemente está abierto.
* **Testing:** escenarios 2, 3 y 4 son pruebas obligatorias.

## Estimación
8 Puntos de Historia (Atraviesa todos los endpoints y exige revisión sistemática)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE42-01 | **Definición de roles y permisos** Matriz explícita de rol contra operación. | - | Pendiente |
| T-BE42-02 | **Decorador require_role** Aplicable a cada método de los blueprints. | - | Pendiente |
| T-BE42-03 | **Comprobación de ámbito por sección** Para el rol tutor. | - | Pendiente |
| T-BE42-04 | **Aplicación a todos los endpoints** Revisión endpoint por endpoint. | - | Pendiente |
| T-BE42-05 | **Distinción 401 / 403** En el manejador global de errores. | - | Pendiente |
| T-BE42-06 | **Tests de permisos** Escenarios 2, 3, 4 y 6, con fixture por rol. | - | Pendiente |
