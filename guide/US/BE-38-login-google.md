# Historia de Usuario

## ID
[BE-38]

## Título
Inicio de sesión con cuenta corporativa de Google

## Descripción
**Como** tutor
**Quiero** entrar en la aplicación con mi cuenta corporativa de Google

**Para** acceder de forma segura sin gestionar otra contraseña más.

## Criterios de Aceptación

### Escenario 1: Inicio del flujo (GET /api/auth/login)
```gherkin
Dado un usuario sin sesión activa
Cuando solicita iniciar sesión
Entonces el sistema genera un state y un nonce y los guarda asociados a la petición
Y construye la URL de autorización de Google con Authorization Code y PKCE
Y añade el parámetro hd=grupopenascal.com
Y redirige al usuario a Google
```

### Escenario 2: Retorno correcto (GET /api/auth/callback)
```gherkin
Dado un usuario que ha autorizado la aplicación en Google
Cuando Google devuelve el código de autorización junto con el state
Entonces el sistema verifica que el state coincide con el emitido
Y intercambia el código por tokens desde el backend
Y valida la firma del ID token contra las claves públicas de Google
Y comprueba emisor, audiencia, caducidad y nonce
Y crea la sesión de servidor
```

### Escenario 3: State no coincidente
```gherkin
Dado una petición de callback cuyo state no coincide con ninguno emitido
Cuando el sistema lo verifica
Entonces devuelve 401 Unauthorized
Y no crea ninguna sesión
```

### Escenario 4: Firma inválida
```gherkin
Dado un ID token cuya firma no valida contra las claves públicas de Google
Cuando el sistema lo verifica
Entonces devuelve 401 Unauthorized con un mensaje genérico
Y no revela el motivo interno del fallo
```

### Escenario 5: Token caducado
```gherkin
Dado un ID token cuya fecha de caducidad ya ha pasado
Cuando el sistema lo verifica
Entonces devuelve 401 Unauthorized
```

### Escenario 6: Audiencia incorrecta
```gherkin
Dado un ID token emitido para otro client_id
Cuando el sistema lo verifica
Entonces devuelve 401 Unauthorized
```

### Escenario 7: El secreto nunca sale del servidor
```gherkin
Dado el flujo de autenticación completo
Cuando se inspecciona cualquier respuesta enviada al navegador
Entonces no aparece el client_secret en ninguna de ellas
Y el intercambio de código por tokens se ha realizado desde el backend
```

## Notas
* **Este proyecto no tiene registro ni contraseñas.** No hay `POST /register`, ni hash de contraseñas, ni recuperación. La identidad la da Google y el centro ya gestiona altas y bajas en su directorio: cuando alguien deja la organización y se le desactiva la cuenta, pierde el acceso aquí sin que nadie tenga que acordarse.
* **Tampoco hay JWT.** Tras validar el ID token se crea una **sesión de servidor** (BE-40). El ID token se usa una vez para autenticar; no se reutiliza como credencial.
* **PKCE aunque haya `client_secret`:** protege frente a la interceptación del código en el retorno. Se suma al secreto, no lo sustituye.
* **Mensajes genéricos:** un `401` no debe explicar si falló la firma, la audiencia o la caducidad.
* **Dependencias:** requiere BE-46 (**bloqueante**). Va junto con BE-39.

## Estimación
8 Puntos de Historia (El coste está en validar bien el token, no en redirigir)

## Prioridad
Crítica

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE38-01 | **Configuración del cliente OIDC** Authlib con credenciales del entorno y descubrimiento de Google. | - | Pendiente |
| T-BE38-02 | **Endpoint de inicio** Generar `state`, `nonce` y verificador PKCE; construir la URL con `hd`. | - | Pendiente |
| T-BE38-03 | **Endpoint de callback** Verificar `state` e intercambiar el código desde el servidor. | - | Pendiente |
| T-BE38-04 | **Validación del ID token** Firma contra JWKS con caché, emisor, audiencia, caducidad y `nonce`. | - | Pendiente |
| T-BE38-05 | **Errores genéricos** Todo fallo devuelve el mismo `401`; el detalle solo al log interno. | - | Pendiente |
| T-BE38-06 | **Tests de validación** Escenarios 3 a 6 firmando tokens en local contra un JWKS falso, **sin simular la validación en sí**. | - | Pendiente |
