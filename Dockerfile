FROM python:3.14-alpine
# Para cambiar a dhi.io: sustituir la línea anterior por
#   FROM dhi.io/python:3.14.7-alpine3.24-fips

WORKDIR /app

COPY requirements.txt .
# Alpine usa musl: psycopg2 no tiene rueda precompilada, requiere compilación.
# Build deps instaladas y desinstaladas en la misma capa para que no queden en la imagen final.
RUN apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev \
 && pip install --no-cache-dir -r requirements.txt \
 && apk del .build-deps

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:create_app()"]