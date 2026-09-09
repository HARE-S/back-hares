# Historia de Usuario

## ID
[BE-37]

## Título
Informe agregado de grupo

## Descripción
**Como** responsable pedagógico
**Quiero** un informe agregado de una sección o un centro

**Para** valorar el programa en las reuniones de seguimiento.

## Criterios de Aceptación

### Escenario 1: Datos agregados del grupo
```gherkin
Dado una sección con alumnado y resultados
Cuando se solicita su informe
Entonces se devuelve la media de PPM y de porcentaje de aciertos
Y el número de participantes y de pruebas realizadas
```

### Escenario 2: Distribución, no solo media
```gherkin
Dado un informe de grupo
Cuando se consulta el resultado
Entonces incluye la distribución de resultados
Y no únicamente el valor medio
```

### Escenario 3: Informe de centro
```gherkin
Dado un centro con varias secciones
Cuando se solicita su informe agregado
Entonces se devuelven los datos del conjunto
Y el desglose por sección
```

### Escenario 4: Grupo sin datos
```gherkin
Dado una sección sin resultados registrados
Cuando se solicita su informe
Entonces se indica la ausencia de datos
Y no se devuelven medias calculadas sobre cero
```

### Escenario 5: Exportable
```gherkin
Dado un informe de grupo
Cuando se solicita su exportación
Entonces se genera un fichero Excel con los mismos datos
```

### Escenario 6: Alcance por rol
```gherkin
Dado un tutor
Cuando solicita el informe de un centro completo
Entonces el sistema devuelve 403 Forbidden
```

## Notas
* **Escenario 2 es la razón de ser de esta historia.** Dos grupos con la misma media pueden ser muy distintos: uno homogéneo y otro con la mitad del alumnado estancado y la otra mitad muy por encima. La media sola oculta exactamente el problema que el programa quiere detectar.
* **Seguridad:** informes de centro solo para coordinador y responsable pedagógico. Los agregados no incluyen nombres de alumnado salvo en el desglose, que sí está restringido.
* **Testing:** escenarios 2, 4 y 6.

## Estimación
5 Puntos de Historia (Agregación con distribución y desglose)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE37-01 | **Cálculo de agregados** Medias, participantes y número de pruebas. | - | Pendiente |
| T-BE37-02 | **Distribución de resultados** Por tramos, no solo la media. | - | Pendiente |
| T-BE37-03 | **Desglose por sección** En el informe de centro. | - | Pendiente |
| T-BE37-04 | **Exportación del informe** Reutilizando BE-35. | - | Pendiente |
| T-BE37-05 | **Restricción por rol** Informes de centro limitados. | - | Pendiente |
| T-BE37-06 | **Tests del informe de grupo** Escenarios 2, 4 y 6. | - | Pendiente |
