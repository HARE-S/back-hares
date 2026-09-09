# Historia de Usuario

## ID
[BE-XX]

> El número coincide con la historia del backlog compartido. `BE-19` y `FE-19` son las dos mitades de `US-19`.
> Historias sin contraparte en la interfaz llevan igualmente su número original.

## Título
[Frase corta en infinitivo o sustantivo]

## Descripción
**Como** [rol: administrador / tutor / coordinador pedagógico / responsable pedagógico / desarrollador]
**Quiero** [capacidad concreta]

**Para** [beneficio observable]

## Criterios de Aceptación

### Escenario 1: [Caso principal — el camino feliz]
```gherkin
Dado que [contexto y precondición]
Cuando [acción que dispara el comportamiento]
Entonces [resultado esperado]
Y [efecto adicional verificable]
```

### Escenario 2: [Caso de error o límite]
```gherkin
Dado que [contexto]
Cuando [acción]
Entonces [rechazo con código concreto]
Y [qué NO debe ocurrir]
```

> **Regla:** toda historia con endpoint necesita al menos un escenario de acceso denegado (`401` sin sesión, `403` con rol insuficiente). Con datos de menores, ese escenario no es opcional.

## Notas
* **Seguridad:** [qué rol accede, qué queda en auditoría]
* **Decisiones:** [qué se ha resuelto de forma no obvia y por qué]
* **Testing:** [pruebas obligatorias de `guides/testing.md` que aplican]

## Estimación
[N] Puntos de Historia ([motivo de la cifra])

## Prioridad
[Crítica / Alta / Media / Baja]

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BEXX-01 | **[Título]** [Detalle de qué hay que hacer] | - | Pendiente |
| T-BEXX-02 | **[Título]** [Detalle] | - | Pendiente |

---

**Estados posibles:** Pendiente · En curso · En revisión · Completado · Bloqueado
