# Historia de Usuario

## ID
[BE-15]

## Título
Modelo de niveles de libro

## Descripción
**Como** coordinador pedagógico
**Quiero** que los niveles de libro admitan los valores que usamos realmente

**Para** no tener que inventar una equivalencia numérica que no existe.

## Criterios de Aceptación

### Escenario 1: Niveles válidos aceptados
```gherkin
Dado los niveles usados por el centro
Cuando se registra un libro con nivel "0", "0-I", "I", "II" o "I/II"
Entonces el sistema acepta el valor
Y lo conserva tal cual
```

### Escenario 2: Nivel no reconocido
```gherkin
Dado un libro con nivel "III"
Cuando se intenta registrar
Entonces el sistema rechaza la petición
Y devuelve 400 Bad Request enumerando los niveles válidos
```

### Escenario 3: Ordenación por nivel
```gherkin
Dado libros de niveles "II", "0", "I/II" y "0-I"
Cuando se consulta el catálogo ordenado por nivel
Entonces se devuelven en el orden pedagógico 0, 0-I, I, I/II, II
Y no en orden alfabético
```

### Escenario 4: Filtro por nivel
```gherkin
Dado un catálogo con libros de varios niveles
Cuando se filtra por nivel "I"
Entonces se devuelven solo los libros de ese nivel
Y no los de "0-I" ni "I/II"
```

## Notas
* **Esta historia corrige un conflicto del esquema del cliente.** El diagrama declara `level int not null`, pero los niveles reales del centro son `Nivel 0`, `Nivel 0-I`, `Nivel I`, `Nivel II` y `Nivel I / II`. **No caben en un entero.** Forzar una numeración inventada rompería la correspondencia con el material que el profesorado ya usa.
* **Decisiones:** se guarda como texto con un orden definido aparte, para poder ordenar y comparar sin perder la notación original.
* **Testing:** escenarios 2 y 3.

## Estimación
3 Puntos de Historia (Enumeración con orden propio y validación)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE15-01 | **Enumeración de niveles** Con su orden pedagógico definido. | - | Pendiente |
| T-BE15-02 | **Validación en el esquema** Rechazo con mensaje enumerando los válidos. | - | Pendiente |
| T-BE15-03 | **Ordenación en el repositorio** Por orden pedagógico, no alfabético. | - | Pendiente |
| T-BE15-04 | **Tests de niveles** Escenarios 1 a 4. | - | Pendiente |
