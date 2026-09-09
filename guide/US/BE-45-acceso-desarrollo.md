# Historia de Usuario

## ID
[BE-45]

## Título
Acceso en entorno de desarrollo

## Descripción
**Como** desarrollador
**Quiero** trabajar sin depender de Google

**Para** poder programar y ejecutar pruebas sin conexión ni credenciales reales.

## Criterios de Aceptación

### Escenario 1: Entrada simulada en desarrollo
```gherkin
Dado un entorno con DEV_AUTH_BYPASS activo
Cuando se solicita una sesión de desarrollo
Entonces se crea una sesión con un usuario simulado
Y su rol se puede configurar
```

### Escenario 2: Desactivado por defecto
```gherkin
Dado un entorno sin la variable DEV_AUTH_BYPASS definida
Cuando arranca la aplicación
Entonces el bypass está desactivado
Y el endpoint de sesión simulada no existe
```

### Escenario 3: Incompatible con producción
```gherkin
Dado un entorno con APP_ENV=production y DEV_AUTH_BYPASS=true
Cuando arranca la aplicación
Entonces la aplicación se niega a arrancar
Y el mensaje explica el motivo con claridad
```

### Escenario 4: Uso en las pruebas
```gherkin
Dado la suite de pruebas automatizadas
Cuando necesita un usuario autenticado
Entonces usa este mecanismo
Y no cuentas reales de Google ni conexión a internet
```

### Escenario 5: Ausente en la especificación pública
```gherkin
Dado la especificación OpenAPI generada en producción
Cuando se consulta
Entonces el endpoint de sesión simulada no aparece
```

## Notas
* **Una puerta trasera de desarrollo que llega a producción es una brecha completa.** Los escenarios 2 y 3 no son opcionales: el arranque debe **fallar ruidosamente**, no registrar un aviso que nadie lea.
* **Decisiones:** el mecanismo es un endpoint que solo se registra si el bypass está activo, no un endpoint permanente que comprueba una condición. Si no está registrado, no puede llamarse aunque alguien se equivoque en la comprobación.
* **Escenario 4 es el motivo real de la historia.** Sin él, las pruebas de integración dependerían de la red y de credenciales reales, serían lentas y frágiles, y no se ejecutarían.
* **Testing:** escenario 3 es prueba obligatoria.

## Estimación
3 Puntos de Historia (Sencillo, pero las salvaguardas son lo importante)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE45-01 | **Registro condicional del endpoint** Solo si el bypass está activo. | - | Pendiente |
| T-BE45-02 | **Usuario simulado con rol configurable** Para poder probar cada perfil. | - | Pendiente |
| T-BE45-03 | **Comprobación al arrancar** Fallo si coincide con configuración de producción. | - | Pendiente |
| T-BE45-04 | **Fixture de autenticación para pruebas** Basada en este mecanismo. | - | Pendiente |
| T-BE45-05 | **Tests de salvaguarda** Escenarios 2, 3 y 5. | - | Pendiente |
