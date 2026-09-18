FROM python:3.14-alpine
# Para cambiar a dhi.io: sustituir la línea anterior por
#   FROM dhi.io/python:3.14.7-alpine3.24-fips

WORKDIR /app

COPY requirements.txt .
# Alpine usa musl: psycopg2 no tiene rueda precompilada, requiere compilación.
# Build deps instaladas y desinstaladas en la misma capa para que no queden en la imagen final.
RUN apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev \
 && pip install --no-cache-dir -r requirements.txt \
 && apk del .build-deps \
 && apk add --no-cache postgresql-client bash

COPY . .

RUN chmod +x docker-entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["./docker-entrypoint.sh"]