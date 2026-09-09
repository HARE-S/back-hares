# Historia de Usuario

## ID
[BE-32]

## Título
Comparativa de evolución por grupos

## Descripción
**Como** responsable pedagógico
**Quiero** comparar la evolución media entre secciones, centros o perfiles

**Para** detectar dónde funciona mejor el programa y dónde hay que intervenir.

## Criterios de Aceptación

### Escenario 1: Comparación de dos secciones
```gherkin
Dado dos secciones con resultados registrados
Cuando se solicita su comparativa
Entonces se devuelve la media de PPM de cada una
Y la media de porcentaje de aciertos de cada una
```

### Escenario 2: Tamaño de cada grupo
```gherkin
Dado una comparativa entre grupos
Cuando se consulta el resultado
Entonces cada grupo indica cuántos alumnos lo componen
Y cuántas pruebas se han considerado
```

### Escenario 3: Grupo poco representativo
```gherkin
Dado un grupo con menos alumnos que el mínimo configurado
Cuando se incluye en una comparativa
Entonces se marca como poco representativo
Y su media se devuelve acompañada de esa advertencia
```

### Escenario 4: Comparación por centro
```gherkin
Dado alumnos de varios centros
Cuando se solicita la comparativa agrupando por centro
Entonces se devuelve una media por centro
```

### Escenario 5: Grupo sin datos
```gherkin
Dado un grupo sin resultados registrados
Cuando se incluye en una comparativa
Entonces se devuelve con tamaño cero y sin media
Y no se representa como un cero
```

### Escenario 6: Alcance por rol
```gherkin
Dado un tutor
Cuando solicita una comparativa entre centros
Entonces el sistema deniega la operación
Y devuelve 403 Forbidden
```

## Notas
* **Escenarios 2, 3 y 5 son lo importante.** Una media sin el tamaño de la muestra invita a conclusiones falsas: dos alumnos de una sección pueden dar una media espectacular que no significa nada. Y un grupo sin datos representado como cero parecería el peor del centro cuando simplemente no ha hecho pruebas.
* **Decisiones:** el mínimo de representatividad es configurable, no una constante. Lo que es razonable en un centro grande no lo es en un grupo de mejora lectora de seis alumnos.
* **Seguridad:** comparativas entre centros solo para coordinador y responsable pedagógico.
* **Testing:** escenarios 3 y 5.

## Estimación
8 Puntos de Historia (Agrupaciones flexibles y tratamiento cuidadoso de muestras pequeñas)

## Prioridad
Media

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE32-01 | **Agrupación configurable** Por sección, centro o perfil. | - | Pendiente |
| T-BE32-02 | **Cálculo de medias con tamaño** Media siempre acompañada de n y del número de pruebas. | - | Pendiente |
| T-BE32-03 | **Umbral de representatividad** Configurable, con marca en la respuesta. | - | Pendiente |
| T-BE32-04 | **Grupos vacíos sin media** Distinguir ausencia de datos de un valor cero. | - | Pendiente |
| T-BE32-05 | **Restricción por rol** Comparativas entre centros limitadas. | - | Pendiente |
| T-BE32-06 | **Tests de comparativa** Escenarios 2, 3, 5 y 6. | - | Pendiente |
