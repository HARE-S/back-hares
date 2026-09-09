# Historia de Usuario

## ID
[BE-50]

## Título
Alta y modificación manual de alumnado, centros y secciones

## Descripción
**Como** administrador
**Quiero** dar de alta y corregir alumnos, centros y secciones desde la aplicación

**Para** poder incorporar un alumno que no aparece en el volcado o corregir un dato erróneo sin esperar a la siguiente exportación de Alexia.

## Criterios de Aceptación

### Escenario 1: Alta manual de un alumno
```gherkin
Dado un administrador con sesión activa
Cuando crea un alumno indicando nombre, centro y sección
Entonces el sistema lo registra
Y le asigna un external_id propio marcado como de origen manual
Y devuelve 201 Created
```

### Escenario 2: Modificación de datos
```gherkin
Dado un alumno existente
Cuando el administrador corrige su nombre o sus datos de perfil
Entonces los cambios se guardan
Y quedan registrados en auditoría con el valor anterior
```

### Escenario 3: Un alta manual no se pierde al reimportar
```gherkin
Dado un alumno creado manualmente
Cuando se ejecuta una importación desde Alexia que no lo incluye
Entonces ese alumno sigue existiendo
Y conserva sus resultados y lecturas
```

### Escenario 4: Alexia manda sobre los datos que trae
```gherkin
Dado un alumno cuyo origen es la importación
Y que un administrador ha modificado su nombre a mano
Cuando se reimporta el volcado con el nombre original
Entonces prevalece el valor de Alexia
Y el cambio manual queda registrado en auditoría como sobrescrito
```

### Escenario 5: Baja lógica de un alumno
```gherkin
Dado un alumno que deja el programa
Cuando el administrador lo da de baja
Entonces se rellena su disabled_at
Y desaparece de los listados por defecto
Y su histórico de resultados sigue siendo consultable
```

### Escenario 6: Solo el administrador
```gherkin
Dado un usuario con rol tutor o coordinador
Cuando intenta crear o modificar un alumno, centro o sección
Entonces el sistema devuelve 403 Forbidden
```

### Escenario 7: Sección sin centro
```gherkin
Dado un intento de crear una sección sin indicar centro
Cuando se procesa
Entonces el sistema devuelve 400 Bad Request
```

## Notas

* **Esta historia resuelve una contradicción entre dos documentos del cliente.** El papel de presentación pide expresamente *"pantallas que permitan la carga manual (y también las modificaciones pertinentes de dichos datos)"*. Pero la especificación de API entregada declara `students`, `centers` y `sections` **solo con `GET`**. Ambos son del cliente y dicen cosas distintas.

* **Decisión propuesta:** se permite el CRUD manual, pero **Alexia sigue siendo la fuente de verdad** para los registros que ella trae. El escenario 4 fija esa regla: si un dato viene de Alexia, una reimportación lo restaura. Sin esa regla, cada importación destruiría trabajo manual o lo perpetuaría en conflicto, y nadie sabría qué valor es el bueno.

* **Origen del registro:** cada alumno, centro y sección guarda si procede de importación o de alta manual. Es lo que permite aplicar el escenario 3 sin borrar altas manuales en cada sincronización.

* **A confirmar con el cliente antes de implementar:** ¿un alumno creado a mano debe aparecer en el siguiente volcado de Alexia, o el centro asume que vivirá solo en esta aplicación? La respuesta cambia la política de conflictos.

* **Seguridad:** solo administrador. Toda alta y modificación en auditoría (BE-44). Un alta manual introduce datos personales de un menor sin pasar por Alexia, así que la traza es imprescindible.

* **Testing:** escenarios 3, 4 y 6.

* **Dependencias:** requiere BE-03, BE-07 y BE-42.

## Estimación
8 Puntos de Historia (CRUD de tres entidades más la política de conflictos con la importación, que es lo que realmente cuesta)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE50-01 | **Confirmar la política con el cliente** Qué prevalece ante conflicto y si los altas manuales vuelven a Alexia. | - | Bloqueado |
| T-BE50-02 | **Campo de origen del registro** Importado o manual, en centros, secciones y alumnos. | - | Pendiente |
| T-BE50-03 | **Esquemas de alta y modificación** Para las tres entidades, con validación de referencias. | - | Pendiente |
| T-BE50-04 | **Endpoints CRUD** `POST`, `PATCH` y `DELETE` lógico, restringidos a administrador. | - | Pendiente |
| T-BE50-05 | **Política de conflictos en la importación** Alexia prevalece sobre lo modificado a mano; los altas manuales se conservan. | - | Pendiente |
| T-BE50-06 | **Auditoría de altas y cambios** Con el valor anterior. | - | Pendiente |
| T-BE50-07 | **Tests de CRUD y conflictos** Escenarios 1 a 7. | - | Pendiente |
