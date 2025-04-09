#!/bin/bash

set -e

mkdir -p certificates
cd certificates

# === Step 1: Create the CA ===
openssl genrsa -out server_CA.key 4096
openssl req -x509 -new -nodes -key server_CA.key -sha256 -days 3650 \
  -out server_CA.crt -subj "/CN=serverCA"

# === Helper Function to Create SAN Certificates ===
generate_cert_with_san() {
  NAME=$1
  CN=$2
  SAN=$3

  # Generate private key and CSR with SAN
  openssl req -newkey rsa:4096 -nodes \
    -keyout ${NAME}_server.key \
    -out ${NAME}_server.csr \
    -subj "/CN=${CN}" \
    -addext "subjectAltName=DNS:${SAN}"

  # Sign the CSR with SAN
  openssl x509 -req -in ${NAME}_server.csr \
    -CA server_CA.crt -CAkey server_CA.key -CAcreateserial \
    -out ${NAME}_server.crt -days 825 -sha256 \
    -extfile <(printf "subjectAltName=DNS:${SAN}")
}

# === Step 2: Create certs for bank1, bank2, gateway with SAN ===
generate_cert_with_san bank1 bank1 localhost
generate_cert_with_san bank2 bank2 localhost
generate_cert_with_san gateway localhost localhost

echo "✅ All SAN-based certs created in ./certificates/"
