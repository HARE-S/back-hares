# Manual de administración

Guía de operaciones de servidor del programa de **Mejora de Comprensión Lectora**.

Está pensado para la persona que administra el programa: importa el alumnado, da de alta usuarios y revisa la auditoría. **No hace falta tener conocimientos técnicos** para seguirlo: cada apartado explica qué hacer, en qué orden y qué se debe ver como resultado.

**Alcance:** cubre las operaciones de administración que se gestionan desde el servidor — importación de alumnado, usuarios y auditoría. El uso diario de tutores y coordinadores (resultados, lecturas, informes) se documenta desde la interfaz, no aquí.

---

## 1. Quién puede administrar

Antes de cualquier operación de este manual hay que entrar en la aplicación como **admin**.

Solo las personas con rol **admin** (y en algunos casos **director**) pueden gestionar usuarios y consultar la auditoría. La importación de alumnado es exclusiva de **admin**.

| Rol | Qué puede hacer |
| :--- | :--- |
| **admin** | Todo: importar alumnado, gestionar usuarios, consultar la auditoría. |
| **director** | Gestionar usuarios y consultar la auditoría. No importa alumnado. |
| **coordinador** | Acceso completo al alumnado y a sus informes. Puede consultar la auditoría. |
| **tutor** | Solo el alumnado de sus secciones asignadas. |
| **pendiente** | Acaba de registrarse: aún no puede ver datos. Sin permisos hasta que se le asigne un rol. |

---

## 2. Importar alumnado desde Alexia

Cuando el centro recibe un nuevo volcado de alumnado desde Alexia, se importa en tres pasos: preparar el fichero, subirlo y revisarlo, y confirmar la importación.

### 2.1. Preparar el fichero

El fichero debe cumplir estas reglas; si no, el sistema lo rechaza al subirlo:

- Es un fichero **CSV** guardado en formato **UTF-8** (en Excel/Calc: *Guardar como → CSV UTF-8*).
- Las columnas se separan con punto y coma.
- La primera línea es la cabecera, exactamente así:

  | student_id | student_name | sections | center |
  | :--- | :--- | :--- | :--- |

- Cada línea siguiente es un alumno:
  - **student_id**: el identificador que Alexia asigna (no cambia nunca).
  - **student_name**: nombre y apellidos.
  - **sections**: la sección del alumnado. Si un alumno está en varias secciones, se escriben separadas por comas.
  - **center**: el centro al que pertenece.
- El fichero no puede superar los **2 MB**.

Un ejemplo de tres líneas válidas:

```
student_id;student_name;sections;center
STU01;student 1;1A;centro 1
STU03;student 3;1A,1B;centro 1
STU08;student 8;2A;centro 2
```

Fíjate en `STU03`: un alumno en dos secciones, `1A` y `1B`, separadas con coma. La primera línea (cabecera) tiene que coincidir exactamente con la tabla de arriba.

### 2.2. Subir y revisar

1. En el panel de administración, entra en *Importación de alumnado*.
2. Sube el fichero.
3. El sistema muestra una **previsualización** (las primeras líneas), el **número total de líneas** leídas y el **número de errores detectados**.

4. Si hay errores, se puede **descargar un informe** que indica la **línea**, la **columna** y el **motivo** de cada error. Corrige el fichero y vuelve a subirlo. Se repite hasta que el fichero no presente errores.
5. Cuando la previsualización y el número de líneas sean correctos, la subida queda lista para confirmar.

### 2.3. Confirmar la importación

1. Pulsa *Confirmar importación*.
2. El sistema procesa **todo el fichero de una vez** y muestra un resumen:
   - **Creados**: alumnos nuevos que no estaban en el sistema.
   - **Actualizados**: alumnos que ya existían (se reconoce por su identificador) y cuyos datos se han puesto al día.
   - **Omitidos**: líneas repetidas o sin cambios.
3. Importar **más de una vez el mismo fichero es seguro**: nadie se duplica. Los alumnos ya existentes se actualizan; los que no cambian se omiten.

Para volver a importar tras una importación hecha, hay que subir el fichero de nuevo siguiendo los pasos 2.2 y 2.3.

### 2.4. Qué no hacer

- **No cambies el formato** del fichero (columnas, cabecera o separador). El sistema lo rechaza.
- **No uses más columnas** de las cuatro indicadas.
- **No dejes el identificador vacío**: es lo que permite reconocer al mismo alumno en importaciones sucesivas.
- **No corrijas datos con un acceso directo a la base de datos** (p. ej. desde una herramienta de administración de PostgreSQL): esos cambios no quedan registrados en la auditoría. Las correcciones se hacen por la aplicación.

---

## 3. Gestión de usuarios

### 3.1. Dar acceso a una persona nueva

1. El personal nuevo **se registra** en la aplicación con su correo del centro (dominio `grupopenascal.com`) y una contraseña.
2. Al registrarse queda en rol **pendiente**: todavía no ve nada.
3. El admin (en el panel de *Usuarios*) le asigna el **rol** correspondiente y, si es tutor o coordinador, sus **secciones**.

### 3.2. Qué significa cada rol

| Rol | Qué puede hacer | Ejemplo de uso |
| :--- | :--- | :--- |
| **pendiente** | Nada todavía. | Primer acceso, hasta que se asigne rol. |
| **tutor** | El alumnado de sus secciones. | Un tutor o tutor de ciclo. |
| **coordinador** | Todo el alumnado y sus informes. | Responsable de lectura del centro. |
| **director** | Gestión de usuarios y auditoría. | Dirección del centro. |
| **admin** | Todo, incluida la importación. | Administrador del programa. |

### 3.3. Asignar secciones

Solo tienen secciones quienes gestionan alumnado (tutor/coordinador):

1. Abre al usuario en *Usuarios*.
2. Añade cada sección asignada (una a una).
3. Para retirar una sección, se elimina del mismo lugar.

Sin secciones asignadas, un tutor no puede acceder a ningún alumno.

### 3.4. Cambiar el rol

Cuando una persona cambia de responsabilidad (por ejemplo, pasa de tutor a coordinador, o deja de ser tutor), el admin cambia su rol desde *Usuarios*. **El cambio se aplica a partir de su siguiente inicio de sesión.**

---

## 4. Revocar un acceso

Ante la salida de una persona del programa, lo que hay que hacer hoy es:

1. Entra en *Usuarios*.
2. Cambia su rol a **pendiente**. Así pierde todo acceso a datos del alumnado (solo podría iniciar sesión, pero no ver nada) a partir de su siguiente inicio de sesión.
3. Si además hay que retirar la vista de un grupo concreto, quita también sus **secciones**.
4. Confirma con la persona o con dirección que ya no necesita el acceso.

> **En curso:** la desactivación total (bloquear el acceso de forma definitiva y cortar al instante las sesiones abiertas de esa persona) está pendiente de terminarse en una historia posterior (BE-44). Cuando esté disponible, este apartado se ampliará con el procedimiento completo. Para cualquier salida del personal, conviene además coordinar con el administrador de Google Workspace del centro la desactivación de la cuenta corporativa.

---

## 5. Registro de auditoría

### 5.1. Para qué sirve

La auditoría guarda **quién hizo qué y cuándo**. Sirve para responder ante una incidencia con datos de menores: poder demostrar quién consultó, modificó o exportó qué, y cuándo.

Quedan registradas, entre otras: la subida y la confirmación de importaciones, los accesos a datos de alumnado, la modificación y anulación de resultados, los informes y comparativas generados, las exportaciones a Excel y los inicios de sesión.

### 5.2. Quién puede consultarla

El listado completo está disponible para **admin**, **director** y **coordinador**. Cualquier usuario puede consultar únicamente **sus propias** acciones.

### 5.3. Cómo consultarla

1. Entra en *Auditoría*.
2. Opcionalmente filtra por:
   - **persona** (su correo),
   - **tipo de acción**,
   - **cantidad de registros** a mostrar.
3. Revisa las entradas resultantes.

### 5.4. Cómo se lee una entrada

Cada registro indica:

| Campo | Qué significa |
| :--- | :--- |
| **Cuándo** | Fecha y hora de la acción. |
| **Quién** | Correo de la persona que la hizo. |
| **Qué hizo** | El tipo de acción (importar, consultar, modificar, exportar…). |
| **Sobre qué** | El recurso afectado (alumno, grupo, centro…). |
| **Desde dónde** | La dirección IP de la que partió la acción. |
| **Resultado** | Si terminó bien o falló. |

### 5.5. Por qué el registro no se puede borrar ni editar

El registro de auditoría **no se puede modificar ni borrar desde la aplicación**: no existe esa opción, a propósito. Un registro que se pudiera editar no serviría como evidencia ante una incidencia.

---

## 6. Mantenimiento de este manual

Este manual se actualiza **en el mismo cambio** en que cambia un procedimiento documentado aquí. Si un cambio de la aplicación afecta a la importación, a los usuarios o a la auditoría, la persona que lo hace añade o corrige la sección correspondiente de este manual en el mismo conjunto de cambios que envía, antes de dar el cambio por terminado.

**Responsable:** Marlen Álvarez (historia BE-49).