# Historia de Usuario

## ID
[BE-13]

## Título
Edición y baja de pruebas

## Descripción
**Como** coordinador pedagógico
**Quiero** corregir o retirar una prueba

**Para** mantener el catálogo al día.

## Criterios de Aceptación

### Escenario 1: Reemplazo completo (PUT)
```gherkin
Dado una prueba existente
Cuando se envía PUT con todos los campos
Entonces el recurso se reemplaza por completo
Y devuelve 200 OK
```

### Escenario 2: Modificación parcial (PATCH)
```gherkin
Dado una prueba existente
Cuando se envía PATCH con solo el campo name
Entonces se modifica únicamente ese campo
Y devuelve 200 OK
```

### Escenario 3: Datos inválidos en PATCH
```gherkin
Dado una prueba existente
Cuando se envía PATCH con un valor de words no válido
Entonces el sistema rechaza la petición
Y devuelve 422 Unprocessable Entity
```

### Escenario 4: Intento de cambiar el código de una prueba con resultados
```gherkin
Dado una prueba que ya tiene resultados de alumnos asociados
Cuando se intenta modificar su campo code
Entonces el sistema deniega la modificación
Y devuelve 409 Conflict explicando el motivo
```

### Escenario 5: Baja lógica
```gherkin
Dado una prueba activa
Cuando se envía DELETE
Entonces se rellena disabled_at
Y devuelve 204 No Content
Y los resultados asociados siguen siendo accesibles
```

## Notas
* **Decisiones:** el código de una prueba es su identificador funcional para el profesorado. Cambiarlo cuando ya tiene resultados asociados haría que el histórico dejara de tener sentido — los resultados quedarían atribuidos a un texto que ya no se llama así.
* **Seguridad:** coordinador y administrador. Toda modificación queda en auditoría.
* **Testing:** escenarios 3, 4 y 5.

## Estimación
3 Puntos de Historia (Verbos estándar más una regla de negocio)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE13-01 | **Esquema de actualización** `TestUpdateSchema` con todos los campos opcionales. | Yeremi | Hecho |
| T-BE13-02 | **Regla de código bloqueado** Comprobar existencia de resultados antes de permitir el cambio. | Yeremi | Hecho |
| T-BE13-03 | **Verbos PUT, PATCH y DELETE** En el `MethodView` del recurso individual. | Yeremi | Hecho |
| T-BE13-04 | **Tests de edición** Escenarios 1 a 5. | Yeremi | Hecho |

