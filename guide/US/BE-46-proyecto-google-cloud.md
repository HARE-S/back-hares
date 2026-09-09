# Historia de Usuario

## ID
[BE-46]

## Título
Configuración del proyecto en Google Cloud

## Descripción
**Como** administrador
**Quiero** que las credenciales OAuth estén correctamente registradas

**Para** que el inicio de sesión funcione en desarrollo y en producción sin cambios de código.

## Criterios de Aceptación

### Escenario 1: Proyecto creado
```gherkin
Dado el dominio corporativo de Google Workspace
Cuando se crea el proyecto en Google Cloud
Entonces existe un identificador de cliente OAuth para la aplicación
Y un secreto asociado
```

### Escenario 2: Consentimiento interno
```gherkin
Dado la pantalla de consentimiento del proyecto
Cuando se configura
Entonces queda como interna al dominio
Y las cuentas ajenas al dominio no pueden completar el flujo desde el propio Google
```

### Escenario 3: URIs de redirección
```gherkin
Dado los entornos de desarrollo y producción
Cuando se registran las URIs de redirección
Entonces ambas están autorizadas
Y coinciden exactamente con las configuradas en la aplicación, protocolo incluido
```

### Escenario 4: Credenciales fuera del código
```gherkin
Dado el repositorio del proyecto
Cuando se busca el client_id o el client_secret
Entonces no aparecen en ningún fichero versionado
Y se inyectan por variable de entorno
```

### Escenario 5: Procedimiento documentado
```gherkin
Dado la necesidad de rehacer la configuración
Cuando se consulta la documentación del proyecto
Entonces el procedimiento está descrito paso a paso
```

## Notas
* **BLOQUEANTE del proyecto.** Sin acceso a la consola de Google Cloud de la organización no hay `client_id` ni `client_secret`, y sin ellos BE-38 y BE-39 no se pueden ni desarrollar. **Hay que identificar al administrador de Workspace del centro y solicitar acceso en el primer sprint.**
* **Escenario 2 es defensa en profundidad.** Configurar el consentimiento como interno añade una barrera a nivel de Google, independiente de la validación del claim `hd` de BE-39. Si una falla, la otra sigue en pie.
* **Escenario 3 causa un fallo muy frecuente:** la URI de redirección debe coincidir **exactamente**, incluido `https://` frente a `http://`. De ahí que el proxy deba enviar `X-Forwarded-Proto`, o la aplicación construirá la URL con el protocolo equivocado y Google la rechazará.
* **Confirmado:** `grupopenascal.com` es un dominio de Google Workspace, así que el consentimiento interno es aplicable.

## Estimación
3 Puntos de Historia (Configuración, no desarrollo; el coste real es coordinarse con quien administra Workspace)

## Prioridad
Crítica — bloquea toda la épica de seguridad

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE46-01 | **Identificar al administrador de Workspace** Y solicitar acceso a la consola. | - | Bloqueado |
| T-BE46-02 | **Crear el proyecto y las credenciales OAuth** Identificador y secreto de cliente. | - | Bloqueado |
| T-BE46-03 | **Pantalla de consentimiento interna** Restringida al dominio. | - | Bloqueado |
| T-BE46-04 | **Registrar URIs de redirección** Desarrollo y producción, con el protocolo exacto. | - | Bloqueado |
| T-BE46-05 | **Documentar el procedimiento** En `guides/deployment.md`. | - | Pendiente |
