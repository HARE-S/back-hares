# Historia de Usuario

## ID
[BE-18]

## Título
Registrar el resultado de una prueba realizada

## Descripción
**Como** tutor
**Quiero** consignar el resultado de una prueba de comprensión lectora de un alumno

**Para** dejar registrada su progresión y poder valorarla más adelante.

## Criterios de Aceptación

### Escenario 1: Registro correcto (POST /api/students/{student_id}/results)
```gherkin
Dado un tutor con sesión activa y la sección del alumno asignada
Cuando envía test_id, section_id, test_date, time, successes y mistakes
Entonces el sistema crea el resultado asociado al alumno
Y guarda la sección como foto del momento
Y devuelve 201 Created con el recurso completo
Y el recurso incluye el PPM calculado
```

### Escenario 2: Valores numéricos inválidos
```gherkin
Dado un tutor con sesión activa
Cuando envía un tiempo, aciertos o errores negativos
Entonces el sistema rechaza la petición
Y devuelve 400 Bad Request indicando el campo inválido
Y no se crea ningún registro
```

### Escenario 3: Referencia inexistente
```gherkin
Dado un tutor con sesión activa
Cuando envía un test_id o un section_id que no existe
Entonces el sistema devuelve 400 Bad Request
```

### Escenario 4: Duplicado exacto
```gherkin
Dado un alumno con un resultado de la prueba 1AF con fecha 10/03/2026
Cuando se envía otro resultado de la prueba 1AF con esa misma fecha
Entonces el sistema devuelve 409 Conflict
```

### Escenario 5: Petición sin sesión
```gherkin
Dado una petición sin cookie de sesión válida
Cuando se llama al endpoint
Entonces el sistema devuelve 401 Unauthorized
Y no devuelve ninguna redirección
```

### Escenario 6: Tutor sin permiso sobre la sección
```gherkin
Dado un tutor con sesión activa
Y que la sección indicada no está entre las que tiene asignadas
Cuando envía el resultado
Entonces el sistema devuelve 403 Forbidden
Y no se crea ningún registro
```

### Escenario 7: Usuario con rol pendiente
```gherkin
Dado un usuario recién autenticado con rol "pendiente"
Cuando intenta registrar un resultado
Entonces el sistema devuelve 403 Forbidden
```

### Escenario 8: Registro en auditoría
```gherkin
Dado un registro de resultado completado con éxito
Cuando termina la operación
Entonces queda una entrada de auditoría con usuario, fecha y recurso afectado
```

## Notas
* **Decisiones:** `results.section_id` se guarda aunque el alumno ya tenga sus matrículas en `student_sections`. **No es redundancia por descuido:** si el alumno cambia de grupo el curso siguiente, el histórico debe seguir diciendo en qué grupo estaba al hacer cada prueba. Sin eso, toda comparativa por sección queda falseada retroactivamente.
* **PPM:** se calcula, no se almacena. `palabras / (tiempo en segundos / 60)`. Vive en `analytics/metrics.py` y se devuelve en la respuesta para que el tutor vea el resultado al momento.
* **Seguridad:** tutor (solo sus secciones) y coordinador. Escenarios 5, 6 y 7 obligatorios.
* **Testing:** escenarios 2, 4, 5 y 6 están en la lista de pruebas obligatorias.
* **Dependencias:** requiere BE-03 y BE-40. Desbloquea la pantalla de registro y la de lote en la interfaz.

## Estimación
5 Puntos de Historia (Atraviesa las cuatro capas y concentra la comprobación de permisos por sección)

## Prioridad
Crítica — núcleo funcional del proyecto

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE18-01 | **Esquemas de resultado** `ResultCreateSchema` con validación de no negativos y `ResultSchema` con PPM. | - | Pendiente |
| T-BE18-02 | **ResultRepository** Alta y comprobación de duplicado por alumno, prueba y fecha. | - | Pendiente |
| T-BE18-03 | **ResultService** Validar referencias, comprobar permiso sobre la sección y lanzar excepciones de dominio. | - | Pendiente |
| T-BE18-04 | **Blueprint POST de resultados** `MethodView` con `@blp.arguments`, `@blp.response(201)` y `@require_role`. | - | Pendiente |
| T-BE18-05 | **Mapeo de excepciones** Dominio → 400, 403, 409 con forma de error estable. | - | Pendiente |
| T-BE18-06 | **Registro en auditoría** Usuario, fecha y recurso afectado. | - | Pendiente |
| T-BE18-07 | **Tests de integración** Los ocho escenarios, con fixtures de tutor con y sin permiso. | - | Pendiente |
