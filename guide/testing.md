# Estrategia de pruebas

> Estrategia de pruebas del **backend** — Programa de Gestión de Mejora de Comprensión Lectora (Peñascal).
> Define qué se prueba, cómo y contra qué. Todo código que llega a `main` ha pasado por lo aquí descrito.
> Las pruebas de la interfaz están en `frontend/guides/testing.md`.

---

## 1. Qué se prueba y qué no

No todo merece una prueba. Lo que sí, en orden de importancia:

1. **Cálculos.** PPM, porcentaje de aciertos, tendencias y proyecciones. Un error aquí no rompe nada: produce un número plausible pero falso, y alguien toma decisiones pedagógicas sobre un alumno con ese número. Es el fallo más peligroso del proyecto precisamente porque es silencioso.
2. **Reglas de negocio.** Que un resultado no se duplique en la misma fecha, que una prueba con resultados no cambie de código, que la importación sea idempotente.
3. **Seguridad.** Que un endpoint sin sesión devuelva `401`, que un rol sin permiso reciba `403`, que un token con dominio ajeno sea rechazado.
4. **Contratos de la API.** Que los códigos de estado y las formas de respuesta sean los que dice la especificación.

Lo que **no** se prueba: que SQLAlchemy sepa hacer un `INSERT`, que Flask enrute, que Marshmallow valide un entero. Eso ya está probado por sus autores. Escribir tests de librerías ajenas infla la cobertura y no protege de nada.

---

## 2. Herramientas

| Herramienta | Uso |
|---|---|
| `pytest` | Motor de pruebas |
| `pytest-cov` | Cobertura |
| Cliente de pruebas de Flask | Peticiones a la API en tests de integración |
| `factory-boy` o *fixtures* propias | Generación de datos de prueba |
| `freezegun` | Congelar el tiempo en tests con fechas |
| `ruff` | Linter y formateo |

Todo en `requirements-dev.txt`, separado de `requirements.txt`. Las dependencias de prueba no viajan a la imagen de producción.

---

## 3. Organización

Refleja la estructura de `src/`, para que encontrar el test de un módulo sea inmediato:

```
backend/tests/
├── conftest.py                  # fixtures compartidas
├── unit/
│   ├── analytics/
│   │   ├── test_metrics.py
│   │   ├── test_evolution.py
│   │   └── test_projection.py
│   ├── services/
│   │   ├── test_result_service.py
│   │   ├── test_reading_service.py
│   │   └── test_catalog_service.py
│   ├── importer/
│   │   ├── test_parser.py
│   │   └── test_loader.py
│   └── auth/
│       ├── test_google.py
│       └── test_permissions.py
├── integration/
│   ├── test_auth_endpoints.py
│   ├── test_students_endpoints.py
│   ├── test_results_endpoints.py
│   ├── test_books_endpoints.py
│   └── test_import_flow.py
└── fixtures/
    ├── import_data_valid.csv
    ├── import_data_errors.csv
    └── tests_catalog.csv
```

> **Fábrica de aplicación obligatoria.** Los tests crean la app con `create_app(TestConfig)`. Una aplicación creada a nivel de módulo no se puede configurar por test y obliga a variables de entorno globales, que es como los tests acaban apuntando sin querer a la base de datos equivocada.

**Unitarias:** sin base de datos, sin red, sin HTTP. Rápidas — el conjunto entero debe correr en segundos.
**Integración:** con base de datos real y peticiones HTTP completas. Más lentas, menos numerosas.

La mayoría de las pruebas deben ser unitarias. Si para probar una regla de negocio hace falta levantar la base de datos, normalmente indica que la regla está en el sitio equivocado — probablemente dentro de un endpoint o de un repositorio en lugar de en un servicio.

---

## 4. Base de datos de pruebas

**Las pruebas corren contra PostgreSQL, nunca contra SQLite.**

Esta es la decisión más importante del documento. Usar SQLite en tests porque "es más rápido y no necesita contenedor" es un atajo que se paga entero:

- SQLite no tiene tipo `uuid` nativo ni `uuidv7()`, que es el generador por defecto de todas las tablas del esquema.
- No aplica igual las restricciones `UNIQUE` compuestas — justo el mecanismo que impide duplicar un resultado en US-20.
- No tiene tipos `date` reales.
- Trata las claves foráneas como opcionales salvo que se activen explícitamente.

El resultado es el peor escenario posible: pruebas verdes que no detectan errores reales, y fallos que solo aparecen en producción. Si no se prueba contra el mismo motor que se despliega, no se está probando el sistema.

### Servicio dedicado

En `docker-compose.override.yml`:

```yaml
database-test:
  image: dhi.io/postgresql:18.6-alpine3.24-fips
  profiles: ["test"]
  environment:
    POSTGRES_DB: comprension_lectora_test
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_password
  tmpfs:
    - /var/lib/postgresql/data      # en memoria: rápido y sin persistencia
  networks: [db-network]
```

`tmpfs` mantiene los datos en memoria. Recupera buena parte de la velocidad que se buscaba con SQLite, sin renunciar al motor real. Y al no persistir, es imposible que un test contamine nada.

### Aislamiento entre pruebas

Cada test corre dentro de una transacción que se revierte al terminar:

```python
@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()      # nada de lo que hizo el test sobrevive
    connection.close()
```

Así el orden de ejecución deja de importar y un test que falla no arrastra a los siguientes.

### Regla absoluta

**Las pruebas nunca apuntan a la base de datos de producción ni de preproducción.** La configuración de test debe fallar al arrancar si `DATABASE_URL` no contiene `_test`. No es paranoia: un `--clean` mal dirigido borra expedientes de alumnado, y la copia de seguridad no siempre está tan reciente como uno cree.

Y en la otra dirección: **nunca copiar datos reales a un entorno de pruebas.** Los datos de prueba se generan (US-06). Son datos de menores; no salen de producción.

---

## 5. Convenciones

### Nombres

El nombre del test describe el comportamiento esperado, no la función que llama:

```python
# Bien: se entiende el fallo sin abrir el fichero
def test_ppm_returns_zero_when_time_is_zero():
def test_same_test_can_be_repeated_on_different_dates():
def test_login_rejects_token_from_other_domain():

# Mal: no dice nada al fallar
def test_ppm():
def test_login_2():
```

Cuando un test falla en el registro de la integración continua, su nombre suele ser toda la información disponible. Que diga qué se ha roto ahorra el viaje al código.

### Estructura

Tres bloques: preparar, ejecutar, comprobar.

```python
def test_ppm_is_calculated_from_words_and_time():
    # Arrange
    test = Test(code="1AF", name="Warner BROS Park", words=835)
    result = Result(time=300, successes=8, mistakes=2)

    # Act
    ppm = calculate_ppm(test.words, result.time)

    # Assert
    assert ppm == pytest.approx(167.0, rel=0.01)
```

### Una comprobación por concepto

Un test verifica una cosa. Si comprueba cinco, al fallar la primera no sabrás si las otras cuatro estaban bien.

### Marcadores

```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.slow
```

Permiten ejecutar solo lo rápido durante el desarrollo.

---

## 6. Pruebas obligatorias

Estas no son sugerencias. Cada una corresponde a un fallo concreto ya identificado en el análisis del proyecto.

| Prueba | Historia | Qué protege |
|---|---|---|
| Un alumno puede repetir la misma prueba en fechas distintas | US-20 | El bug de la clave primaria original. Sin esto no hay evolución que medir |
| Duplicar alumno + prueba + fecha devuelve `409` | US-20 | Que la restricción única sea la correcta, ni más ni menos estricta |
| Reimportar el mismo CSV no cambia el recuento de filas | US-08 | Idempotencia. Se ejecuta el import dos veces y se comparan totales |
| Un alumno en tres secciones genera tres matrículas | US-07 | El campo multivalor separado por comas |
| El CSV con `;` final no rompe el parser | US-13 | La columna vacía de `tests.csv` |
| Un ID token sin claim `hd` es rechazado | US-44 | Cuentas personales de Gmail |
| Un ID token con `hd` distinto es rechazado | US-44 | El fallo de confiar en el parámetro en vez del claim |
| `GET /api/students` sin sesión devuelve `401` | US-45 | Que ningún endpoint quede abierto |
| Un tutor no accede a secciones ajenas | US-47 | Aislamiento entre centros |
| La aplicación no arranca con `DEV_AUTH_BYPASS=true` y `APP_ENV=production` | US-50 | Que la puerta trasera de desarrollo no llegue a producción |
| PPM con tiempo cero no lanza excepción | US-31 | División por cero |
| No se proyecta con menos de tres pruebas | US-34 | Estimaciones sin fundamento |
| Un libro se puede releer en fechas distintas | US-26 | La otra clave primaria mal puesta |
| Una prueba deshabilitada no aparece en el listado por defecto | US-05 | Borrado lógico |
| Los resultados de una prueba deshabilitada siguen siendo accesibles | US-05 | Que el borrado lógico no rompa el histórico |

---

## 7. Pruebas de autenticación sin llamar a Google

Los tests no pueden depender de una conexión a Google: serían lentos, frágiles y no funcionarían sin red.

Pero **no basta con simular la verificación entera**. Si se sustituye la función que valida el token por una que siempre devuelve un usuario válido, se está eliminando de las pruebas justo la lógica que protege el sistema. Los tests pasarían con la validación del `hd` borrada del código.

Enfoque correcto: firmar tokens de prueba localmente con una clave propia y apuntar la verificación a un JWKS falso. Así se ejercita la validación real —firma, emisor, audiencia, caducidad y `hd`— sin salir a internet.

```python
def test_login_rejects_token_from_other_domain(client, fake_id_token):
    token = fake_id_token(email="alguien@gmail.com", hd=None)
    response = client.post("/api/auth/callback", json={"id_token": token})
    assert response.status_code == 401


def test_login_accepts_corporate_domain(client, fake_id_token):
    token = fake_id_token(
        email="tutor@grupopenascal.com",
        hd="grupopenascal.com",
        email_verified=True,
    )
    response = client.post("/api/auth/callback", json={"id_token": token})
    assert response.status_code == 200
```

Regla general: se simula la **frontera externa** (la red, Google), nunca la lógica propia.

---

## 8. Pruebas con fechas

La evolución y las proyecciones dependen del tiempo, y los tests que dependen del reloj fallan solos algún día — típicamente el 1 de enero o al cambiar la hora.

```python
@freeze_time("2026-03-15")
def test_projection_uses_only_last_six_months():
    ...
```

Nunca usar `date.today()` en un test para construir los datos esperados. Fechas fijas y explícitas.

---

## 9. Cobertura

Objetivos por capa, porque no todo el código merece el mismo nivel:

| Capa | Cobertura mínima |
|---|---|
| `analytics/` | 95% |
| `services/` | 85% |
| `importer/` | 85% |
| `auth/` | 90% |
| `api/` | 70% |
| `models/`, `schemas/` | sin objetivo |

```bash
pytest --cov=src/app --cov-report=term-missing --cov-fail-under=80
```

**La cobertura es un indicador, no una meta.** Un 90% con tests que no comprueban nada útil es peor que un 70% bien elegido: da confianza falsa. Lo que interesa de `--cov-report=term-missing` no es el porcentaje, sino qué líneas concretas no ha pisado nadie. Si una de ellas es una regla de negocio, ahí hay un test que falta.

---

## 10. Ejecución

```bash
# Todo
docker compose --profile test run --rm backend pytest

# Solo unitarias, durante el desarrollo
docker compose --profile test run --rm backend pytest -m unit

# Un fichero concreto
docker compose --profile test run --rm backend pytest tests/unit/analytics/test_metrics.py -v

# Con cobertura
docker compose --profile test run --rm backend pytest --cov=src/app --cov-report=term-missing

# Parar en el primer fallo
docker compose --profile test run --rm backend pytest -x
```

Si aparece `ModuleNotFoundError: No module named 'app'`, revisar `pythonpath = ["src"]` en `pyproject.toml` — está explicado en `structure.md`, apartado 6.

---

## 11. Integración continua

Antes de fusionar a `develop` o `main`:

- [ ] `ruff check .` sin errores
- [ ] `ruff format --check .` sin cambios pendientes
- [ ] `pytest` completo en verde
- [ ] Cobertura por encima del umbral
- [ ] Todas las pruebas obligatorias del apartado 6 que apliquen a la historia

**Ningún test se marca como `skip` para poder fusionar.** Un test desactivado es un fallo conocido que se ha decidido ignorar, y nadie lo vuelve a mirar. Si un test estorba, o se arregla el código o se borra el test con una justificación en el commit.

---

## 12. Antipatrones

| Antipatrón | Por qué falla |
|---|---|
| Probar contra SQLite | Distinto motor, distintos resultados. Apartado 4 |
| Simular la validación del token | Elimina de las pruebas justo lo que protege el sistema |
| Tests que dependen del orden | Uno falla y arrastra a los demás. Usar rollback por test |
| `time.sleep()` para esperar | Lento y frágil. Esperar por condición, no por tiempo |
| Un test que comprueba diez cosas | Al fallar no se sabe cuál |
| Datos reales en pruebas | Datos de menores. Se generan, no se copian |
| Perseguir el porcentaje de cobertura | Produce tests sin comprobaciones útiles |
| `assert response.status_code == 200` como único assert | Confirma que responde, no que responda bien |

---

## 13. El contrato con el frontend también se prueba

La interfaz se construye contra lo que el backend promete devolver. Si ese contrato cambia sin aviso, la interfaz se rompe en producción y no en las pruebas de nadie.

Por eso los tests de integración comprueban **forma**, no solo código de estado:

```python
def test_student_detail_response_shape(client, authenticated_tutor):
    response = client.get(f"/api/students/{student.id}")

    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {"id", "name", "sections", "results"}
    assert body["results"][0]["ppm"] is not None
```

Y hay dos que no pueden faltar, porque la interfaz depende de ellas para decidir qué hacer:

- Sin sesión → **`401`**, nunca una redirección. Una redirección desde el backend rompe cualquier petición hecha con `fetch`.
- Con sesión pero sin permiso → **`403`**. Son casos distintos y la interfaz reacciona distinto a cada uno.

La especificación OpenAPI generada (US-53) es la fuente que consume el equipo de interfaz. Si un cambio la altera, se avisa antes de fusionar.

---

## 14. Antes de entregar

Comprobaciones manuales que ninguna prueba automática cubre:

- [ ] Restaurar una copia de seguridad en un entorno limpio y verificar que los datos están completos.
- [ ] Entrar con una cuenta `@grupopenascal.com` real.
- [ ] Intentar entrar con una cuenta personal y confirmar el rechazo.
- [ ] Comprobar desde fuera del servidor que pgAdmin no responde.
- [ ] Importar el CSV real del cliente y revisar el informe de errores.
- [ ] Abrir una exportación a Excel y comprobar que fechas y decimales tienen formato, no son texto.

---

*Última actualización: 08/09/2026 · Ver también `deployment.md`, `structure.md` y `workflow.md` de esta carpeta.*
