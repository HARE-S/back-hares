# Historia de Usuario

## ID
[BE-40]

## Título
Sesión de servidor

## Descripción
**Como** usuario
**Quiero** mantener la sesión mientras trabajo y poder cerrarla

**Para** no reautenticarme cada cinco minutos ni dejar la sesión abierta en un aula.

## Criterios de Aceptación

### Escenario 1: Creación de la sesión
```gherkin
Dado un usuario autenticado correctamente en Google
Cuando se crea su sesión
Entonces el estado de la sesión se guarda en la base de datos
Y la cookie enviada al navegador contiene solo un identificador
Y la cookie lleva los atributos HttpOnly, Secure y SameSite=Lax
```

### Escenario 2: Cierre de sesión
```gherkin
Dado un usuario con sesión activa
Cuando solicita cerrar sesión
Entonces el registro de sesión se elimina del servidor
Y una petición posterior con esa misma cookie devuelve 401
```

### Escenario 3: Caducidad por inactividad
```gherkin
Dado una sesión sin actividad durante el plazo configurado
Cuando se hace una petición
Entonces el sistema devuelve 401 Unauthorized
Y la sesión deja de ser válida
```

### Escenario 4: Petición sin sesión
```gherkin
Dado una petición a cualquier endpoint bajo /api sin cookie válida
Cuando se procesa
Entonces el sistema devuelve 401 Unauthorized
Y NO devuelve una redirección al login
```

### Escenario 5: Endpoints exentos
```gherkin
Dado los endpoints de salud y del flujo de autenticación
Cuando se llaman sin sesión
Entonces responden con normalidad
Y son los únicos exentos de la comprobación
```

### Escenario 6: Revocación inmediata
```gherkin
Dado un usuario con dos sesiones activas
Cuando un administrador lo deshabilita
Entonces ambas sesiones dejan de ser válidas al momento
Y no hace falta esperar a que caduquen
```

## Notas
* **Dos decisiones que parecen la misma y no lo son.**

  **No se usa JWT.** Revocar un token antes de su caducidad obliga a mantener una lista de revocación, que es exactamente el estado que el JWT pretendía evitar. Con sesión de servidor, revocar es borrar una fila.

  **Y tampoco la sesión por defecto de Flask.** Flask guarda el estado **dentro de la propia cookie, firmado**. No hay nada en el servidor. Con ella, el escenario 2 no invalida nada y el escenario 6 es imposible: la cookie sigue siendo válida hasta caducar, la tenga quien la tenga. Por eso se usa Flask-Session con almacenamiento en PostgreSQL.

  Si alguien configura la sesión por defecto "porque es más simple", se incumplen dos criterios de aceptación de esta historia y uno de BE-44.

* **Escenario 4 es contrato con la interfaz:** una redirección desde el backend rompe cualquier petición hecha con `fetch`. Es la interfaz quien decide qué hacer con el `401`.
* **TLS obligatorio:** la cookie es `Secure`; sin HTTPS el navegador no la envía y el login no funcionará.
* **Testing:** escenarios 2, 4 y 6 son pruebas obligatorias.

## Estimación
5 Puntos de Historia (Configuración del almacén de sesión y comprobación global)

## Prioridad
Crítica

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE40-01 | **Almacén de sesión en base de datos** Flask-Session con backend SQLAlchemy. | - | Pendiente |
| T-BE40-02 | **Atributos de la cookie** `HttpOnly`, `Secure`, `SameSite=Lax` y caducidad configurable. | - | Pendiente |
| T-BE40-03 | **Comprobación global de sesión** Todo `/api` protegido salvo salud y autenticación. | - | Pendiente |
| T-BE40-04 | **Endpoint de cierre de sesión** Eliminando el registro en servidor. | - | Pendiente |
| T-BE40-05 | **Endpoint /api/auth/me** Devuelve el usuario actual o `401`. | - | Pendiente |
| T-BE40-06 | **Tests de sesión** Escenarios 2, 3, 4 y 6. | - | Pendiente |
