# Historia de Usuario

## ID
[BE-36]

## Título
Datos del informe individual de alumno

## Descripción
**Como** tutor
**Quiero** obtener todo lo necesario para el informe de un alumno en una llamada

**Para** poder generar un documento imprimible para la familia o el expediente.

## Criterios de Aceptación

### Escenario 1: Contenido del informe
```gherkin
Dado un alumno con histórico registrado
Cuando se solicitan los datos de su informe
Entonces la respuesta incluye sus datos identificativos
Y su histórico de pruebas con métricas
Y sus lecturas
Y su serie de evolución
```

### Escenario 2: Fecha de generación
```gherkin
Dado una solicitud de informe
Cuando se devuelven los datos
Entonces incluyen la fecha y hora de generación
```

### Escenario 3: Alumno sin datos suficientes
```gherkin
Dado un alumno con una sola prueba
Cuando se solicitan los datos de su informe
Entonces se devuelven sus datos con el indicador de evolución insuficiente
Y no se incluye ninguna proyección
```

### Escenario 4: Permiso sobre el alumno
```gherkin
Dado un tutor sin la sección de ese alumno
Cuando solicita su informe
Entonces el sistema devuelve 403 Forbidden
```

### Escenario 5: Registro de la generación
```gherkin
Dado un informe generado
Cuando termina la operación
Entonces queda registrada en auditoría
```

## Notas
* **Decisiones:** el backend entrega los datos; **la maquetación imprimible es responsabilidad de la interfaz**. Generar un PDF en el servidor añadiría una dependencia pesada para un resultado que el navegador ya sabe producir.
* **Seguridad:** un informe individual es el documento más sensible del sistema — reúne todo lo de un menor en una página. Permiso estricto y auditoría obligatoria.
* **Testing:** escenarios 3 y 4.

## Estimación
3 Puntos de Historia (Composición de datos ya disponibles)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE36-01 | **Esquema del informe** Datos, histórico, lecturas y evolución en una estructura. | - | Pendiente |
| T-BE36-02 | **Composición en el servicio** Reutilizando BE-28 y BE-31. | - | Pendiente |
| T-BE36-03 | **Fecha de generación** Incluida en la respuesta. | - | Pendiente |
| T-BE36-04 | **Auditoría y permisos** Registro y comprobación estricta. | - | Pendiente |
| T-BE36-05 | **Tests del informe** Escenarios 1 a 5. | - | Pendiente |
