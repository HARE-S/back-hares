# Backlog — Backend

**Programa de Gestión de Mejora de Comprensión Lectora** (Peñascal)
Equipo: Marlen Álvarez, Santiago Patiño, Yeremi Peralta · Coordinación: Andrés Ocina
Versión: v2 — 09/09/2026

> Historias de servidor: API, base de datos, lógica de negocio, importación y autenticación.
> **Stack: Flask + flask-smorest + SQLAlchemy 2.0 + Alembic + PostgreSQL + Gunicorn.**
> Las de interfaz están en `frontend/BACKLOG.md`.
> **Los números `US-XX` son compartidos.** Una historia que aparece en los dos backlogs está partida por responsabilidad, no duplicada: el punto de encuentro es siempre el contrato de la API.

---

## Cómo leer este documento

| Marca | Significado |
|---|---|
| **[solo backend]** | No tiene contraparte en la interfaz |
| **[mitad backend]** | La otra mitad está en `frontend/BACKLOG.md` con el mismo número |
| 🔒 | Bloqueada por una decisión del cliente |

---

## EP-B1 — Infraestructura

### US-01 — Stack contenedorizado **[mitad backend]**
**Como** desarrollador **quiero** levantar el entorno de servidor con un comando **para** que los tres trabajemos sobre la misma base.

- `docker compose up` levanta `database` y `backend`; `import` y `pgadmin` quedan bajo perfil.
- Imágenes DHI indicadas en `guides/deployment.md`.
- Redes internas: `database` solo alcanzable desde `backend` e `import`.
- `database` con `healthcheck`; el backend no arranca hasta que responda.
- Volumen `data_dir` persistente.

**Puntos:** 5 · **Crítica**

---

### US-03 — Configuración por variables de entorno **[solo backend]**
**Como** administrador **quiero** configurar credenciales sin reconstruir imágenes **para** desplegar en varios entornos.

- Todo por variables de entorno; `.env.example` documentado y `.env` en `.gitignore`.
- La aplicación **falla al arrancar** si falta una variable obligatoria.
- Falla también si `APP_ENV=production` y `DEV_AUTH_BYPASS=true` coinciden.
- `SESSION_SECRET` de al menos 32 bytes.

**Notas:** el fallo ruidoso al arrancar es la diferencia entre un despliegue fallido y una brecha silenciosa.
**Puntos:** 3 · **Alta**

---

## EP-B2 — Modelo de datos **[solo backend]**

### US-04 — Esquema inicial versionado
**Como** desarrollador **quiero** el esquema en migraciones versionadas **para** evolucionarlo sin perder datos.

- Todas las tablas por migración, nunca por script manual.
- Claves foráneas con política `ON DELETE` explícita.
- Índices sobre `results(student_id, test_date)` y `read_books(student_id)`.
- Migración reversible.

**Correcciones obligatorias sobre el esquema del cliente:**

| Tabla | Cambio | Motivo |
|---|---|---|
| `centers`, `sections`, `students` | + `external_id varchar unique` | Sin él la reimportación duplica |
| `students` | + `birth_date`, `gender`, `academic_status`, `sector` (nullable) | Criterios de filtrado de US-28 |
| `tests` | + `level`, `type`; `code` unique | El código `0IF` esconde nivel y tipo |
| `results` | **PK → `id uuid`** + `UNIQUE(student_id, test_id, test_date)` | La PK original impide pruebas sucesivas |
| `books` | **quitar `student_id`**; `level` a varchar | Es catálogo, no relación |
| `read_books` | renombrada; **PK → `id uuid`** + `UNIQUE(student_id, book_id, start_date)` | Permitir relectura |
| `users`, `user_sections` | nuevas | Autenticación y permisos |

**Puntos:** 8 · **Crítica**

---

### US-05 — Borrado lógico
**Como** coordinador **quiero** que dar de baja una prueba no borre el histórico **para** conservar los resultados de años anteriores.

- `DELETE` sobre pruebas y libros rellena `disabled_at`; devuelve `204`.
- Los listados los excluyen por defecto; `?include_disabled=true` los muestra.
- Los resultados de una prueba deshabilitada **siguen siendo accesibles**.

**Puntos:** 3 · **Alta**

---

### US-06 — Datos de prueba anónimos
**Como** desarrollador **quiero** poblar la base con datos realistas anónimos **para** probar sin manejar datos de menores.

- Carga los 28 alumnos de `import_data.csv` y las 34 pruebas de `tests.csv`.
- Genera resultados sintéticos: mínimo 3 pruebas por alumno en fechas distintas.
- Idempotente.

**Puntos:** 3 · **Alta**

---

## EP-B3 — Importación de datos maestros

### US-07 — Importar alumnado desde fichero **[solo backend]**
**Como** administrador **quiero** cargar el volcado de Alexia **para** no dar de alta a cientos de alumnos a mano.

- CSV con separador `;`, UTF-8.
- Columnas: `student_id`, `student_name`, `sections`, `center`.
- **`sections` es multivalor separado por comas**: una fila en `student_sections` por cada una.
- Crea centro y sección si no existen.
- Resumen final: creados, actualizados, omitidos, errores.

**Puntos:** 8 · **Crítica**

---

### US-08 — Importación idempotente **[solo backend]**
**Como** administrador **quiero** reimportar sin duplicar **para** resincronizar cuando Alexia cambie.

- Identidad por `external_id`, **nunca por nombre**.
- Alumno existente se actualiza, no se recrea.
- Matrícula ya registrada no se duplica; una sección nueva se añade conservando las anteriores.
- **Reimportar el mismo fichero deja el recuento de filas idéntico.**

**Puntos:** 5 · **Crítica**

---

### US-09 — Informe de errores de importación **[mitad backend]**
**Como** administrador **quiero** saber qué filas fallaron y por qué **para** corregir el origen.

- Una fila inválida no aborta el proceso.
- Cada error indica línea, columna y motivo.
- Informe descargable.
- Detecta: `external_id` vacío, centro vacío, secciones malformadas, número de columnas incorrecto.

**Puntos:** 3 · **Media**

---

### US-10 — Endpoint de subida de fichero **[mitad backend]**
**Como** administrador **quiero** subir el fichero desde el navegador **para** no depender de acceso al servidor.

- Endpoint de subida con validación de extensión y tamaño.
- Devuelve previsualización de las primeras filas antes de confirmar.
- **Reutiliza el mismo módulo de validación que `importer/`**, sin duplicar lógica.

**Notas:** dos caminos de escritura con dos validaciones acabarán divergiendo. Ver `guides/structure.md`, apartado 3.
**Puntos:** 5 · **Alta**

---

### US-11 — Consulta de centros y secciones **[mitad backend]**
**Como** tutor **quiero** navegar por centros y secciones **para** llegar a mi grupo.

- `GET /api/centers`, `/api/centers/{id}`, `/api/centers/{id}/sections`, `/api/sections/{id}/students`.
- Solo lectura: su origen es Alexia.
- `200` / `404` según la especificación.

**Puntos:** 3 · **Alta**

---

## EP-B4 — Catálogo de pruebas

### US-12 — Alta de prueba **[mitad backend]**
- `POST /api/tests` con `code`, `name`, `words`; opcionales `level` y `type`.
- `code` duplicado → `409`. `words` no entero positivo → `400`.
- Devuelve `201` con el recurso completo.

**Puntos:** 3 · **Alta**

---

### US-13 — Importar el catálogo de pruebas **[solo backend]**
- Lee `tests.csv` con separador `;`.
- **Tolera la columna vacía final** que deja el `;` al cierre de cada línea.
- Maneja comillas dobles y acentos.
- Deriva `level` y `type` del patrón del código (`0IF` → nivel 0, tipo F).

**Notas:** confirmar el significado de F/L con pedagogía. Hipótesis: F informativo, L literario; en todos los pares la L tiene más palabras.
**Puntos:** 5 · **Alta**

---

### US-14 — Edición y baja de pruebas **[mitad backend]**
- `PUT` reemplaza; `PATCH` parcial con `422` si es inválido; `DELETE` lógico con `204`.
- **No se permite modificar `code` si ya tiene resultados asociados.**

**Puntos:** 3 · **Media**

---

### US-15 — Listado paginado y filtrado **[mitad backend]**
- `?page`, `?limit`, `?filter` sobre `code` y `name`; filtros por `level` y `type`.
- La respuesta incluye total de elementos y número de páginas.

**Puntos:** 3 · **Media**

---

## EP-B5 — Catálogo de libros

### US-16 — Modelo de niveles de libro **[solo backend]**
- Acepta `0`, `0-I`, `I`, `II`, `I/II`.
- Los niveles tienen orden definido para poder ordenar y comparar.
- Nivel no reconocido → error con mensaje claro.

**Notas:** el esquema del cliente declara `level int not null` y el Excel real trae valores no numéricos. Incompatible tal cual.
**Puntos:** 3 · **Alta**

---

### US-17 — Alta y mantenimiento de libros **[mitad backend]**
- `POST` con `title` y `level` obligatorios; título duplicado → `409`.
- `GET`, `PUT`, `PATCH`, `DELETE` según especificación; `DELETE` lógico.

**Puntos:** 3 · **Alta**

---

### US-18 — Carga inicial del catálogo 🔒 **[solo backend]**
- Importa título y nivel de las filas válidas del Excel.
- Ignora cabeceras repetidas y rótulos de sección.
- `Nº ejemplares` y `Nº sesiones` como texto libre.
- Filas no interpretables listadas aparte.

**Notas — riesgo de planificación:** el Excel no es importable tal cual. `Nº ejemplares` trae `11 Fotocopias`, `PDF`, `COMPRAR`; `Nº sesiones` trae `PREPARAR`, `4 o 5`, `5+` y un `43075` que es una fecha corrupta. **Pedir limpieza manual previa.**
**Puntos:** 8 · **Media**

---

## EP-B6 — Registro de resultados (núcleo)

### US-19 — Registrar una prueba realizada **[mitad backend]**
**Como** tutor **quiero** consignar el resultado de una prueba **para** dejar registrada la progresión.

- Registra alumno, sección, prueba, fecha, tiempo, aciertos y errores.
- **La sección se guarda como foto del momento**, no por referencia a la matrícula actual.
- `201` al crear; `400` si hay valores negativos o referencias inexistentes.
- `403` si el tutor no tiene esa sección asignada.

**Notas:** `results.section_id` es redundante con `student_sections` **a propósito**: si el alumno cambia de grupo, el histórico debe seguir diciendo dónde estaba al hacer cada prueba.
**Puntos:** 5 · **Crítica**

---

### US-20 — Pruebas sucesivas del mismo texto **[solo backend]**
**Como** coordinador **quiero** que un alumno repita la misma prueba en fechas distintas **para** medir su mejora.

- N resultados de la misma prueba con fechas diferentes.
- Solo se rechaza con `409` el duplicado exacto de alumno + prueba + fecha.
- El histórico muestra todos los intentos ordenados.

**Notas:** arregla la PK `(student_id, section_id)`. **Sin esta historia el objetivo del proyecto es inalcanzable.** Validar antes que cualquier funcionalidad de análisis.
**Puntos:** 3 · **Crítica**

---

### US-21 — Consultar resultados de un alumno **[mitad backend]**
- `GET /api/students/{id}/results` ordenado por fecha.
- Cada resultado incluye nombre y palabras de la prueba **sin otra llamada**.
- Incluye el PPM ya calculado.
- Alumno inexistente → `404`.

**Puntos:** 3 · **Crítica**

---

### US-22 — Corregir y anular un resultado **[mitad backend]**
- `PATCH` parcial con `422` si es inválido; `DELETE` con `204`; inexistente → `404`.
- Toda modificación queda en auditoría.

**Puntos:** 3 · **Alta**

---

### US-23 — Endpoint de registro en lote **[mitad backend]**
- Recibe una prueba, una fecha y una lista de resultados por alumno.
- Se guarda en **una sola transacción**.
- Si una fila falla, devuelve qué fila y por qué sin perder el resto.
- Alumnos ausentes se omiten, no se registran con ceros.

**Puntos:** 5 · **Alta**

---

## EP-B7 — Registro de libros leídos

### US-24 — Asignar un libro **[mitad backend]**
- `POST /api/students/{id}/books` con `book_id` y `start_date`; `end_date` opcional.
- `201`; alumno o libro inexistente → `400`.

**Puntos:** 3 · **Alta**

---

### US-25 — Cerrar una lectura **[mitad backend]**
- `PATCH` para fijar `end_date`; anterior a `start_date` → `422`.

**Puntos:** 2 · **Alta**

---

### US-26 — Relectura **[solo backend]**
- Varias lecturas del mismo libro por alumno con fechas de inicio distintas.
- Solo se rechaza el duplicado exacto.

**Notas:** arregla la PK `(student_id, book_id)`.
**Puntos:** 2 · **Media**

---

### US-27 — Lecturas por alumno y por libro **[mitad backend]**
- `GET /api/students/{id}/books` con título y nivel.
- `GET /api/books/{id}/students`.
- Filtro por estado: en curso / finalizada.

**Puntos:** 3 · **Media**

---

## EP-B8 — Consulta y filtrado

### US-28 — Filtrado multicriterio 🔒 **[mitad backend]**
**Como** coordinador **quiero** segmentar por edad, género, situación académica y sector **para** comparar perfiles.

- Filtros combinables entre sí, más centro y sección.
- La edad se **deriva de `birth_date`**, no se almacena.
- Los alumnos sin dato se agrupan como "sin datos".

**Notas — BLOQUEANTE:** ninguno de los cuatro campos existe en el volcado actual. **No se puede completar** hasta que el cliente amplíe la exportación de Alexia. Entregar mientras tanto la infraestructura de filtrado sobre centro y sección.
**Puntos:** 5 · **Alta (bloqueada)**

---

### US-29 — Endpoint agregado de ficha del alumno **[mitad backend]**
- Una sola llamada devuelve datos, secciones actuales e históricas, resultados con métricas y lecturas.
- Evita que la interfaz encadene cinco peticiones.

**Puntos:** 3 · **Alta**

---

### US-30 — Búsqueda de alumnos **[mitad backend]**
- Insensible a mayúsculas y acentos.
- Responde con menos de 3 caracteres.
- Devuelve centro y sección para desambiguar homónimos.

**Puntos:** 3 · **Media**

---

## EP-B9 — Análisis y evolución **[solo backend]**

### US-31 — Métricas derivadas
- PPM = palabras / minutos empleados.
- Porcentaje de aciertos = aciertos / (aciertos + errores).
- Presentes en todo listado de resultados.
- **Tiempo cero no lanza excepción.**

**Puntos:** 3 · **Crítica**

---

### US-32 — Evolución individual **[mitad backend]**
- Serie temporal de PPM y porcentaje de aciertos, acotable por fechas.
- Indica la variación entre la primera y la última prueba.
- Con menos de 2 pruebas devuelve serie vacía con indicador, no error.

**Puntos:** 5 · **Alta**

---

### US-33 — Comparativa por grupos **[mitad backend]**
- Medias por sección, centro o perfil.
- **Devuelve siempre el tamaño de cada grupo (n).**
- Marca como poco representativos los grupos por debajo de un mínimo configurable.

**Puntos:** 8 · **Media**

---

### US-34 — Proyección de evolución
- Tendencia calculada a partir del histórico.
- Devuelve el número de pruebas en que se basa.
- **Con menos de 3 pruebas no proyecta** y explica por qué.
- Se marca explícitamente como estimación.

**Notas:** el requisito más vago del papel. Empezar por regresión lineal simple y validar utilidad con el cliente antes de invertir más.
**Puntos:** 8 · **Media**

---

### US-35 — Detección de alumnos sin progreso **[mitad backend]**
- Lista alumnos con tendencia plana o negativa en las últimas N pruebas.
- Umbral y N configurables.
- Distingue "sin datos suficientes" de "sin progreso".

**Puntos:** 5 · **Baja**

---

## EP-B10 — Exportación e informes

### US-36 — Exportación a Excel **[mitad backend]**
- Exporta exactamente el conjunto filtrado recibido.
- `.xlsx` con cabeceras en castellano.
- Incluye métricas calculadas, no solo datos crudos.
- **Fechas y decimales con formato real, no como texto.**

**Notas:** la especificación de API entregada no contempla ningún endpoint de exportación. Hay que añadirlo.
**Puntos:** 5 · **Alta**

---

### US-37 — Datos del informe de alumno **[mitad backend]**
- Endpoint con todo lo necesario para el informe individual en una llamada.
- Incluye fecha de generación.

**Puntos:** 3 · **Media**

---

### US-38 — Informe de grupo **[mitad backend]**
- Medias, número de pruebas y de participantes.
- **Distribución de resultados, no solo la media.**
- Exportable a Excel.

**Puntos:** 5 · **Media**

---

## EP-B11 — Seguridad y acceso

### US-43 — Login con Google (OIDC) **[mitad backend]**
- OAuth 2.0 / OIDC con **Authorization Code + PKCE**.
- Valida el ID token contra JWKS: firma, emisor, audiencia y caducidad.
- `state` y `nonce` verificados al volver del callback.
- **El intercambio de código por token ocurre en el backend**, nunca en el navegador.
- `client_secret` solo en variable de entorno.

**Puntos:** 8 · **Crítica**

---

### US-44 — Restricción al dominio corporativo **[solo backend]**
- Petición con `hd=grupopenascal.com`.
- **El backend valida el claim `hd` del ID token de forma independiente.**
- Comprueba `email_verified`.
- Dominio configurable por variable de entorno.
- Prueba automatizada que verifica el rechazo de un `hd` ajeno.

**Notas — el fallo clásico:** el parámetro `hd` de la petición es **solo una sugerencia de interfaz**. La restricción real es el claim en el token. Una cuenta personal de Gmail **no lleva claim `hd` en absoluto**, así que comprobarlo las rechaza todas sin lista negra.
**Confirmado:** `grupopenascal.com` es Google Workspace (MX en `aspmx.l.google.com`).
**Puntos:** 5 · **Crítica**

---

### US-45 — Sesión de servidor **[mitad backend]**
- **Estado de sesión almacenado en PostgreSQL**, no en la cookie.
- Cookie `HttpOnly`, `Secure`, `SameSite=Lax`, con solo un identificador.
- Caducidad por inactividad configurable.
- El cierre de sesión la invalida **en servidor**, no solo borra la cookie.
- Todo `/api/*` sin sesión → **`401`, nunca una redirección**.

**Notas:** sesión de servidor y **no JWT**: revocar debe ser borrar una fila. Y **tampoco la sesión por defecto de Flask**, que guarda el estado firmado dentro de la cookie: con ella no se puede invalidar nada en servidor y se incumplen este criterio y US-49. Usar Flask-Session con backend SQLAlchemy.
**Puntos:** 5 · **Crítica**

---

### US-46 — Alta en el primer acceso **[mitad backend]**
- Primer login del dominio crea el usuario con rol `pendiente`.
- Un `pendiente` **no recibe datos de alumnado** en ningún endpoint.
- Accesos posteriores actualizan nombre y foto y registran `last_login_at`.
- **Identidad por `google_sub`**, no por email: si cambia la dirección, se actualiza la ficha sin crear un usuario nuevo.

**Puntos:** 5 · **Alta**

---

### US-47 — Perfiles de permisos **[mitad backend]**
- Cinco roles diferenciados, `pendiente` incluido.
- El tutor solo accede a sus secciones asignadas.
- **El backend rechaza con `403` toda operación no permitida**, aunque la interfaz ya la oculte.
- Comprobación en servidor en toda operación, sin excepción.

**Puntos:** 8 · **Alta**

---

### US-48 — Gestión de usuarios y roles **[mitad backend]**
- Endpoints para listar usuarios, cambiar rol y asignar secciones.
- **Un administrador no puede quitarse el rol si es el último que queda.**
- Todo cambio de rol queda en auditoría.

**Puntos:** 5 · **Alta**

---

### US-49 — Revocación y auditoría **[solo backend]**
- Deshabilitar un usuario invalida sus sesiones activas al momento.
- Registra accesos, modificaciones de resultados y exportaciones.
- Consultable y filtrable por usuario y fecha; no editable desde la aplicación.

**Notas:** si el centro desactiva una cuenta en Google, esta aplicación no se entera hasta el siguiente intento de autenticación. Por eso la caducidad de sesión no debe ser larga.
**Puntos:** 5 · **Media**

---

### US-50 — Acceso en entorno de desarrollo **[solo backend]**
- Modo de desarrollo con usuario simulado y rol configurable.
- Activado por variable de entorno y **deshabilitado por defecto**.
- **La aplicación se niega a arrancar** si coincide con configuración de producción.
- Las pruebas usan este mecanismo, no cuentas reales.

**Puntos:** 3 · **Alta**

---

### US-51 — Proyecto en Google Cloud 🔒 **[solo backend]**
- Proyecto creado con pantalla de consentimiento **interna** al dominio.
- URIs de redirección para local y producción.
- `client_id` y `client_secret` por variable de entorno.
- Procedimiento documentado.

**Notas:** consentimiento interno = segunda barrera a nivel de Google, independiente de la validación de US-44. **Bloqueante: hace falta acceso a la consola de Google Cloud de la organización.**
**Puntos:** 3 · **Crítica**

---

## EP-B12 — Calidad

### US-52 — Pruebas automatizadas **[solo backend]**
- Unitarias de métricas y proyección; integración de los endpoints principales.
- **Contra PostgreSQL, nunca SQLite.**
- Prueba de idempotencia del importador (US-08).
- Prueba de rechazo de `hd` ajeno (US-44) y de bypass desactivado (US-50).

**Puntos:** 8 · **Alta**

---

### US-53 — Documentación de la API **[solo backend]**
- OpenAPI generada desde el código **por flask-smorest**, navegable en desarrollo.
- Todo endpoint declara `@blp.arguments` y `@blp.response`; sin ellos no entra en la especificación.
- Todos los endpoints documentan sus códigos de respuesta.
- **Es la fuente de verdad para el equipo de interfaz.**

**Puntos:** 3 · **Alta**

---

### US-54 — Manual de usuario **[mitad backend]**
- Procedimiento de importación paso a paso.
- En castellano y sin jerga técnica.

**Puntos:** 2 · **Media**

---

## Planificación

| Sprint | Historias | Objetivo demostrable |
|---|---|---|
| **1 — Cimientos** | US-01, US-03, US-04, US-05, US-06, US-51 | El stack levanta con datos anónimos |
| **2 — Identidad** | US-43, US-44, US-45, US-46, US-50, US-53 | La API rechaza a quien no sea del dominio |
| **3 — Datos maestros** | US-07, US-08, US-09, US-10, US-11 | Se importa el CSV de Alexia |
| **4 — Catálogos y permisos** | US-12 a US-18, US-47, US-48 | Pruebas y libros con roles operativos |
| **5 — Núcleo** | US-19 a US-27, US-31 | Resultados y lecturas con métricas |
| **6 — Análisis** | US-28, US-29, US-30, US-32, US-33 | Filtrado y evolución |
| **7 — Salidas** | US-34, US-36, US-37, US-38, US-52 | Exportación e informes |
| **8 — Cierre** | US-35, US-49, US-54 | Auditoría y documentación |

**La autenticación va en el Sprint 2 a propósito.** Cada endpoint escrito después nace ya protegido. Dejarla para el final obliga a repasar todos los endpoints uno a uno, y ahí es donde se cuela el que se quedó abierto.

---

## Historias que desbloquean la interfaz

El equipo de frontend puede avanzar con simulacros, pero estas son las que necesita **cerradas y con contrato estable**:

| Backend | Desbloquea en frontend |
|---|---|
| US-53 (OpenAPI) | Todo. Es la fuente de tipos |
| US-45 (sesión, `401`) | US-45 front: manejo de sesión caducada |
| US-11 (centros/secciones) | US-39: navegación |
| US-29 (ficha agregada) | US-29 front: pantalla de ficha |
| US-23 (lote) | US-23 front: registro en lote |
| US-32 (evolución) | US-32 front: gráfico |
| US-36 (Excel) | US-36 front: botón de exportación |

---

## Riesgos abiertos

| # | Riesgo | Impacto | Acción |
|---|---|---|---|
| 1 | Campos de filtrado ausentes en el volcado | US-28 incumplible | Solicitar ampliación de Alexia |
| 2 | Excel de libros sin limpiar | US-18 se alarga | Pedir limpieza manual previa |
| 3 | Acceso a Google Cloud | Bloquea EP-B11 | Identificar administrador de Workspace |
| 4 | "Proyecciones" sin definir | US-34 abierta | Acordar por escrito qué es suficiente |
| 5 | Suscripción a imágenes DHI | Despliegue | Confirmar acceso o pactar imágenes oficiales |
| 6 | `import` como job o mecanismo permanente | Doble validación | Definir con el cliente |
| 7 | Significado de F/L en los códigos | Bajo | Confirmar con pedagogía |

---

*Ver `guides/structure.md`, `guides/testing.md`, `guides/deployment.md` y `guides/workflow.md` · Interfaz en `frontend/BACKLOG.md`*
