# Historia de Usuario

## ID
[BE-12]

## Título
Importar el catálogo de pruebas

## Descripción
**Como** administrador
**Quiero** cargar las 34 pruebas de golpe desde el CSV

**Para** no teclearlas una a una.

## Criterios de Aceptación

### Escenario 1: Importación del catálogo
```gherkin
Dado el fichero tests.csv con separador punto y coma
Cuando se ejecuta la importación del catálogo
Entonces se crean las 34 pruebas
Y cada una conserva su código, nombre y número de palabras
```

### Escenario 2: Punto y coma al final de línea
```gherkin
Dado que cada línea del fichero termina en punto y coma
Y esto produce una cuarta columna vacía
Cuando se procesa el fichero
Entonces el parser ignora la columna sobrante
Y no rechaza ninguna fila por número de columnas
```

### Escenario 3: Nombres con comillas y acentos
```gherkin
Dado una fila cuyo nombre contiene comillas dobles y caracteres acentuados
Cuando se procesa
Entonces el nombre se guarda íntegro y correctamente codificado
```

### Escenario 4: Derivación de nivel y tipo
```gherkin
Dado una prueba con código "0IF"
Cuando se importa
Entonces se guarda con level "0"
Y con type "F"
```

### Escenario 5: Reimportación
```gherkin
Dado un catálogo ya importado
Cuando se vuelve a ejecutar la importación
Entonces no se duplica ninguna prueba
Y las existentes se actualizan por su código
```

## Notas
* **Formato real:** separador `;`, y **cada línea acaba en `;`**, lo que genera una columna vacía final. Un parser estricto rechazaría las 34 filas.
* **Pendiente con pedagogía:** confirmar el significado de la letra final F/L. Hipótesis: F texto informativo, L literario. En todos los pares del catálogo, la versión L tiene más palabras que su F correspondiente.
* **Decisiones:** `level` y `type` se guardan como columnas propias en vez de dejarlos enterrados en el código. Filtrar por nivel troceando cadenas de texto en cada consulta es frágil y lento.
* **Testing:** escenario 2 es prueba obligatoria.

## Estimación
5 Puntos de Historia (Parseo con rarezas de formato y derivación de campos)

## Prioridad
Alta

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE12-01 | **Parser de tests.csv** Separador `;`, UTF-8, tolerante a la columna vacía final. | Yeremi | Hecho |
| T-BE12-02 | **Derivación de level y type** A partir del patrón del código. | Yeremi | Hecho |
| T-BE12-03 | **Alta o actualización por código** Reimportación sin duplicar. | Yeremi | Hecho |
| T-BE12-04 | **Tests del parser** Escenarios 2, 3 y 4 con el fichero real. | Yeremi | Hecho |

