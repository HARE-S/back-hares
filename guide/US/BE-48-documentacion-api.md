# Historia de Usuario

## ID
[BE-48]

## Título
Documentación de la API

## Descripción
**Como** desarrollador
**Quiero** una especificación navegable de la API

**Para** que interfaz y servidor avancen en paralelo sin bloquearse.

## Criterios de Aceptación

### Escenario 1: Especificación generada desde el código
```gherkin
Dado la aplicación en funcionamiento
Cuando se consulta la especificación
Entonces se genera automáticamente a partir de los blueprints y esquemas
Y no se mantiene a mano en un documento aparte
```

### Escenario 2: Interfaz navegable en desarrollo
```gherkin
Dado el entorno de desarrollo levantado
Cuando se accede a la ruta de documentación
Entonces se muestra la especificación navegable
Y permite probar los endpoints
```

### Escenario 3: Códigos de respuesta documentados
```gherkin
Dado cualquier endpoint de la API
Cuando se consulta su documentación
Entonces enumera todos sus códigos de respuesta posibles
Incluidos 401 y 403
```

### Escenario 4: Un endpoint sin decoradores no entra
```gherkin
Dado un endpoint escrito sin @blp.arguments ni @blp.response
Cuando se genera la especificación
Entonces ese endpoint aparece sin esquemas documentados
Y se considera un defecto a corregir antes de fusionar
```

### Escenario 5: Sincronización con el código
```gherkin
Dado un cambio en el esquema de un recurso
Cuando se regenera la especificación
Entonces refleja el cambio sin intervención manual
```

## Notas
* **Es la fuente de verdad para el equipo de interfaz.** De aquí salen los tipos del frontend. Si la especificación no refleja la realidad, la interfaz se construye contra algo que no existe y el desajuste aparece al integrar, no antes.
* **Decisiones:** generación automática con flask-smorest en vez de documentación manual. Un documento mantenido a mano se desincroniza a la tercera semana, y entonces es peor que no tener ninguno, porque induce a error.
* **Escenario 4 es una consecuencia del stack:** los decoradores no son decorativos. Validan, serializan y documentan. Un endpoint sin ellos funciona pero queda invisible para quien consume la API.
* **Proceso:** si un cambio altera la especificación, se avisa al equipo de interfaz **antes** de fusionar.

## Estimación
3 Puntos de Historia (Configuración de la generación más la revisión de cobertura documental)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE48-01 | **Configuración de flask-smorest** Metadatos de la API y ruta de la especificación. | - | Pendiente |
| T-BE48-02 | **Interfaz navegable en desarrollo** Desactivada o restringida en producción. | - | Pendiente |
| T-BE48-03 | **Documentación de códigos de error** Incluyendo `401` y `403` en cada endpoint. | - | Pendiente |
| T-BE48-04 | **Revisión de cobertura documental** Ningún endpoint sin esquemas declarados. | - | Pendiente |
