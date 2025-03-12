# Generate bank2 private key
openssl genrsa -out bank2.key 4096

# Create a configuration file for the certificate (bank2.cnf)
echo "[req]
default_bits = 4096
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[dn]
CN = localhost

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1" > bank2.cnf

# Generate a CSR for bank2
openssl req -new -key bank2.key -out bank2.csr -config bank2.cnf

# Sign the CSR with the CA to create the bank2 certificate
openssl x509 -req -days 365 -in bank2.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out bank2.crt -extensions req_ext -extfile bank2.cnf