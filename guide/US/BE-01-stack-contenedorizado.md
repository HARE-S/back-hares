# Historia de Usuario

## ID
[BE-01]

## Título
Stack contenedorizado del backend

## Descripción
**Como** desarrollador
**Quiero** levantar el entorno de servidor con un solo comando

**Para** que los tres trabajemos sobre la misma base y el despliegue no dependa de la máquina.

## Criterios de Aceptación

### Escenario 1: Arranque del entorno
```gherkin
Dado un equipo con Docker y Docker Compose instalados
Cuando se ejecuta "docker compose up -d"
Entonces se levantan los servicios database y backend
Y los servicios import y pgadmin NO se levantan por estar bajo perfil
Y el backend responde en /api/health con 200 OK
```

### Escenario 2: La base de datos debe estar sana antes que el backend
```gherkin
Dado un arranque desde cero
Cuando el contenedor de PostgreSQL aún no acepta conexiones
Entonces el backend no arranca hasta que el healthcheck da "healthy"
Y no se producen fallos intermitentes de conexión
```

### Escenario 3: Aislamiento de red
```gherkin
Dado el entorno levantado
Cuando se intenta alcanzar el puerto 5432 desde fuera del servidor
Entonces la conexión falla
Y ningún servicio salvo el proxy publica puertos al exterior
```

### Escenario 4: Persistencia de datos
```gherkin
Dado datos guardados en la base de datos
Cuando se ejecuta "docker compose down" y luego "docker compose up -d"
Entonces los datos siguen presentes
Y el volumen data_dir conserva el estado
```

## Notas
* **Imágenes:** las DHI indicadas por el cliente. Son de suscripción; si no hay acceso, se pactan las oficiales equivalentes. Ver `guides/deployment.md`.
* **Alpine y PostgreSQL:** Alpine usa musl; el conector puede necesitar compilación. Instalar y desinstalar las dependencias de compilación en la misma capa del Dockerfile.
* **Decisiones:** sin `healthcheck`, `depends_on` solo garantiza que el contenedor arrancó, no que PostgreSQL responda. Es la causa más común de fallo en el primer despliegue.
* **Testing:** escenario 3 verificable con `docker compose exec`.

## Estimación
5 Puntos de Historia (Dockerfile multicapa, healthchecks y segmentación de redes)

## Prioridad
Crítica

## Tareas

| Código | Nombre | Responsable | Estado |
| :--- | :--- | :--- | :--- |
| T-BE01-01 | **Dockerfile del backend** Base Python DHI, dependencias de compilación en una sola capa, `PYTHONPATH=/app/src`, arranque con Gunicorn. | - | Pendiente |
| T-BE01-02 | **Servicio database** Imagen PostgreSQL, volumen `data_dir`, `healthcheck` con `pg_isready`. | - | Pendiente |
| T-BE01-03 | **Redes internas** `db-network` y `backend-network`; ningún `ports:` en backend ni database. | - | Pendiente |
| T-BE01-04 | **Endpoint /api/health** Comprobación de vida sin autenticación. | - | Pendiente |
| T-BE01-05 | **Perfiles para import y pgadmin** `profiles: ["tools"]` para que no arranquen por defecto. | - | Pendiente |
