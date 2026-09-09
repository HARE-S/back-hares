# Historia de Usuario

## ID
[BE-47]

## Título
Batería de pruebas automatizadas

## Descripción
**Como** desarrollador
**Quiero** una batería de pruebas de la lógica crítica

**Para** poder refactorizar sin miedo a romper el histórico.

## Criterios de Aceptación

### Escenario 1: Ejecución contra PostgreSQL
```gherkin
Dado la suite de pruebas
Cuando se ejecuta
Entonces corre contra un contenedor de PostgreSQL
Y NO contra SQLite
```

### Escenario 2: Aislamiento entre pruebas
```gherkin
Dado dos pruebas que escriben en la misma tabla
Cuando se ejecutan en cualquier orden
Entonces ninguna afecta al resultado de la otra
Y cada una revierte sus cambios al terminar
```

### Escenario 3: Cobertura por capa
```gherkin
Dado la ejecución con informe de cobertura
Cuando termina
Entonces analytics supera el 95 por ciento
Y auth supera el 90
Y services e importer superan el 85
Y el conjunto supera el 70
```

### Escenario 4: Pruebas obligatorias presentes
```gherkin
Dado la suite completa
Cuando se revisa su contenido
Entonces incluye la idempotencia del importador
Y el rechazo de un ID token con dominio ajeno
Y el fallo de arranque con el bypass activo en producción
Y la repetición de una prueba en fechas distintas
```

### Escenario 5: Protección del entorno
```gherkin
Dado una configuración de pruebas cuya URL de base de datos no contiene "_test"
Cuando se intenta ejecutar la suite
Entonces la ejecución se detiene
Y no se conecta a esa base de datos
```

### Escenario 6: Sin pruebas desactivadas
```gherkin
Dado la suite antes de fusionar a develop
Cuando se revisa
Entonces ninguna prueba está marcada para omitirse
```

## Notas
* **Escenario 1 es la decisión más importante de la historia.** Probar contra SQLite porque es más rápido invalida buena parte de la suite: SQLite no tiene `uuidv7()`, no aplica igual las restricciones `UNIQUE` compuestas y no tiene tipos `date` reales. Las pruebas de BE-19 y BE-25 pasarían **sin comprobar nada**. Con `tmpfs` se recupera casi toda la velocidad sin renunciar al motor real.
* **Escenario 5 no es paranoia.** Un `--clean` mal dirigido borra expedientes de alumnado, y la copia de seguridad no siempre está tan reciente como uno cree.
* **Los datos de prueba se generan (BE-05), nunca se copian de producción.** Son datos de menores.
* **Escenario 6:** una prueba desactivada es un fallo conocido que se ha decidido ignorar, y nadie lo vuelve a mirar. O se arregla el código o se borra la prueba con justificación en el commit.

## Estimación
8 Puntos de Historia (Infraestructura de pruebas más la cobertura de lo crítico)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE47-01 | **Servicio database-test** PostgreSQL con `tmpfs`, bajo perfil de pruebas. | - | Pendiente |
| T-BE47-02 | **Fixtures de conftest** Aplicación con `create_app(TestConfig)`, sesión con reversión por prueba y usuarios por rol. | - | Pendiente |
| T-BE47-03 | **Protección del entorno** Rechazo si la URL no contiene `_test`. | - | Pendiente |
| T-BE47-04 | **Pruebas unitarias de analytics** Métricas, evolución y proyección con valores conocidos. | - | Pendiente |
| T-BE47-05 | **Pruebas de integración de los endpoints principales** Con sus escenarios de acceso denegado. | - | Pendiente |
| T-BE47-06 | **Informe de cobertura con umbrales** Por capa, no solo global. | - | Pendiente |
