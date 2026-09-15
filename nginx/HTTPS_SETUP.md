# Configuración HTTPS en HARE-S

Esta guía explica cómo configurar HTTPS en tu stack de HARE-S.

## 🔧 Para Desarrollo/Testing (con certificados autofirmados)

### 1. Generar certificados autofirmados

```bash
bash nginx/generate-ssl.sh
```

Esto creará:
- `nginx/ssl/cert.pem` - Certificado público
- `nginx/ssl/key.pem` - Clave privada (600 permisos)

### 2. Activar HTTPS en nginx.conf

Descomenta el bloque HTTPS en `nginx/nginx.conf`:

```bash
# Busca la sección "# HTTPS configuration" y descomenta
```

### 3. Activar puerto 443 en docker-compose.yml

```bash
# Descomenta: - "443:443"
```

### 4. Reiniciar Docker

```bash
docker-compose down && docker-compose up -d
```

### 5. Acceder a tu aplicación

- HTTP: http://localhost
- HTTPS: https://localhost (aceptar advertencia de seguridad)

---

## 🚀 Para Producción (con certificados válidos)

### Opciones recomendadas:

#### Opción A: Let's Encrypt con Certbot (RECOMENDADO)

```bash
# Instalar certbot en el host
sudo apt-get install certbot python3-certbot-nginx

# Generar certificado
sudo certbot certonly --standalone -d tudominio.com

# Los certificados estarán en:
# /etc/letsencrypt/live/tudominio.com/fullchain.pem
# /etc/letsencrypt/live/tudominio.com/privkey.pem

# Montar en Docker:
volumes:
  - /etc/letsencrypt/live/tudominio.com/fullchain.pem:/etc/nginx/ssl/cert.pem:ro
  - /etc/letsencrypt/live/tudominio.com/privkey.pem:/etc/nginx/ssl/key.pem:ro
```

#### Opción B: Certificado de una CA

Reemplaza los archivos en `nginx/ssl/` con tus certificados válidos.

### Cambios necesarios:

1. **nginx/nginx.conf**: Uncomment bloque HTTPS
2. **docker-compose.yml**: Uncomment puerto 443
3. **Certificados**: Montar paths correctos
4. **Redirección HTTP→HTTPS**: Uncomment servidor HTTP que redirige a HTTPS

---

## 🔍 Verificación

### Verificar certificado generado

```bash
openssl x509 -in nginx/ssl/cert.pem -text -noout
```

### Probar conexión HTTPS

```bash
# Con curl (ignorar certificado autofirmado)
curl -k https://localhost

# Con openssl
openssl s_client -connect localhost:443
```

### Ver logs de Nginx

```bash
docker logs hares_proxy
```

---

## 📋 Configuración Actual

| Entorno | HTTP | HTTPS | Redirección |
|---------|------|-------|------------|
| **Desarrollo** | ✅ Activo | Opcional | No |
| **Producción** | ⚠️ Deshabilitado | ✅ Requerido | Sí (80→443) |

---

## ⚠️ Notas Importantes

- Los certificados autofirmados generan advertencias en navegadores (NORMAL)
- Nunca uses certificados autofirmados en producción
- Renueva certificados Let's Encrypt cada 3 meses automáticamente
- Agrupa los headers de seguridad que ya están en nginx.conf (HSTS, CSP, etc.)

---

## 🛠️ Troubleshooting

### "Port 443 already in use"
```bash
sudo lsof -i :443
sudo kill -9 <PID>
```

### "Permission denied" en certificados
```bash
chmod 600 nginx/ssl/key.pem
chmod 644 nginx/ssl/cert.pem
```

### Nginx no arranca después de activar HTTPS
```bash
# Verificar sintaxis
docker run --rm -v $PWD/nginx/nginx.conf:/etc/nginx/nginx.conf:ro nginx:alpine nginx -t

# Ver logs completos
docker logs hares_proxy
```

---

## 📚 Referencias

- [Nginx SSL/TLS Documentation](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)
- [Let's Encrypt](https://letsencrypt.org/)
- [OpenSSL Manual](https://www.openssl.org/docs/)
