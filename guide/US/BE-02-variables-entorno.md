# Historia de Usuario

## ID
[BE-02]

## Título
Configuración por variables de entorno

## Descripción
**Como** administrador
**Quiero** configurar credenciales y parámetros sin reconstruir imágenes

**Para** poder desplegar en distintos entornos sin tocar el código.

## Criterios de Aceptación

### Escenario 1: Arranque con configuración completa
```gherkin
Dado un fichero .env con todas las variables obligatorias
Cuando arranca la aplicación
Entonces lee la configuración del entorno
Y no existe ningún valor de credencial escrito en el código
```

### Escenario 2: Falta una variable obligatoria
```gherkin
Dado un entorno sin SECRET_KEY definida
Cuando arranca la aplicación
Entonces la aplicación se niega a arrancar
Y muestra un mensaje indicando qué variable falta
```

### Escenario 3: Combinación peligrosa detectada
```gherkin
Dado un entorno con APP_ENV=production y DEV_AUTH_BYPASS=true
Cuando arranca la aplicación
Entonces la aplicación se niega a arrancar
Y el mensaje indica que el bypass de desarrollo no puede estar activo en producción
```

### Escenario 4: Secreto de sesión insuficiente
```gherkin
Dado un SECRET_KEY de menos de 32 bytes
Cuando arranca la aplicación
Entonces se niega a arrancar
```

### Escenario 5: Almacenamiento de sesión mal configurado
```gherkin
Dado un entorno donde SESSION_TYPE no apunta a almacenamiento en servidor
Cuando arranca la aplicación
Entonces se niega a arrancar
Y el mensaje explica que la sesión debe persistirse en servidor
```

## Notas
* **Decisiones:** un fallo ruidoso al arrancar es preferible a un sistema que levanta con el bypass de autenticación activo. La diferencia es entre un despliegue fallido y una brecha silenciosa.
* **Seguridad:** `.env` en `.gitignore` desde el primer commit. En el repositorio vive solo `.env.example` con las claves y sin valores. Si un secreto llega a subirse, **hay que rotarlo**: borrarlo en el commit siguiente no lo quita del historial.
* **Configuración por clases:** `DevConfig`, `TestConfig`, `ProdConfig`, seleccionadas por `APP_ENV`.
* **Testing:** escenarios 2 a 5 como pruebas unitarias de la carga de configuración.

## Estimación
3 Puntos de Historia (Lectura sencilla, pero las validaciones de arranque son el valor real)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE02-01 | **Clases de configuración** `Config` base y variantes por entorno seleccionadas con `APP_ENV`. | - | Pendiente |
| T-BE02-02 | **Validación al arrancar** Comprobar presencia y validez; abortar con mensaje claro. | - | Pendiente |
| T-BE02-03 | **Comprobación de combinaciones peligrosas** Producción con bypass activo, secreto corto, sesión no persistida. | - | Pendiente |
| T-BE02-04 | **.env.example documentado** Todas las claves con comentario y sin valores reales. | - | Pendiente |
| T-BE02-05 | **Tests de configuración** Escenarios 2 a 5. | - | Pendiente |
