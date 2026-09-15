#!/bin/bash
# Script para generar certificados SSL autofirmados para desarrollo/testing
# Uso: bash nginx/generate-ssl.sh

set -e

SSL_DIR="$(dirname "$0")/ssl"
CERT_FILE="$SSL_DIR/cert.pem"
KEY_FILE="$SSL_DIR/key.pem"
DAYS=365

# Crear directorio si no existe
mkdir -p "$SSL_DIR"

# Generar certificado autofirmado si no existe
if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo "🔐 Generando certificado SSL autofirmado..."
    openssl req -x509 \
        -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -days "$DAYS" \
        -nodes \
        -subj "/C=ES/ST=Spain/L=Madrid/O=HARES/CN=localhost"

    chmod 600 "$KEY_FILE"
    chmod 644 "$CERT_FILE"

    echo "✅ Certificado generado en:"
    echo "   - Clave privada: $KEY_FILE"
    echo "   - Certificado: $CERT_FILE"
    echo ""
    echo "⚠️  Este certificado es autofirmado. En navegadores web:"
    echo "   - Firefox: No te pedirá confirmación"
    echo "   - Chrome/Safari: Mostrarán advertencia de seguridad (normal)"
    echo ""
    echo "📝 Para activar HTTPS en producción:"
    echo "   1. Descomenta el bloque HTTPS en nginx/nginx.conf"
    echo "   2. Descomenta los puertos 443 en docker-compose.yml"
    echo "   3. Actualiza los certificados con certificados válidos"
else
    echo "✅ Certificados SSL ya existen:"
    echo "   - $CERT_FILE"
    echo "   - $KEY_FILE"
    echo ""
    echo "📊 Info del certificado:"
    openssl x509 -in "$CERT_FILE" -text -noout | grep -A2 "Validity\|Subject\|Public-Key"
fi
