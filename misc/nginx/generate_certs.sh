#!/usr/bin/env sh

CERT_IDENTITY="/C=US/ST=North Carolina/L=Raleigh/O=Red Hat/OU=Automation/CN=AnsibleRunnerService"
CERT_IDENTITY_CLIENT="/C=US/ST=North Carolina/L=Raleigh/O=TestOrg/OU=testOU/CN=testCN"
CERT_PASSWORD="ansible"
BASE_PATH="/etc/ansible-runner-service/certs"

# create folders
mkdir -p $BASE_PATH/server
mkdir -p $BASE_PATH/client


# CA----------------------------------------------------------------------------

echo "Create the CA Key and Certificate for signing Client Certs"
openssl genrsa -des3 -out $BASE_PATH/server/ca.key -passout pass:$CERT_PASSWORD 4096
openssl req -new -x509 -days 365 -key $BASE_PATH/server/ca.key -out $BASE_PATH/server/ca.crt -passin pass:$CERT_PASSWORD -subj "$CERT_IDENTITY"


# Server -----------------------------------------------------------------------

echo "Create the Server Key, CSR, and Certificate"
openssl genrsa -des3 -out $BASE_PATH/server/server.key.org -passout pass:$CERT_PASSWORD 1024
# Remove password (avoid server claiming for it each time it starts)
openssl rsa -in $BASE_PATH/server/server.key.org -out $BASE_PATH/server/server.key -passin pass:$CERT_PASSWORD
# Generate server certificate
openssl req -new -key $BASE_PATH/server/server.key -out $BASE_PATH/server/server.csr -passin pass:$CERT_PASSWORD -subj "$CERT_IDENTITY"

echo "Self-sign the certificate with our CA cert"
openssl x509 -req -days 365 -in $BASE_PATH/server/server.csr -CA $BASE_PATH/server/ca.crt -CAkey $BASE_PATH/server/ca.key -set_serial 01 -out $BASE_PATH/server/server.crt -passin pass:$CERT_PASSWORD


# Client -----------------------------------------------------------------------

echo "Create the Client Key and CSR"
openssl genrsa -des3 -out $BASE_PATH/client/client.key.org -passout pass:$CERT_PASSWORD 1024
# Remove password (avoid https client claiming for it in each request)
openssl rsa -in $BASE_PATH/client/client.key.org -out $BASE_PATH/client/client.key -passin pass:$CERT_PASSWORD
# Generate client certificate
openssl req -new -key $BASE_PATH/client/client.key -out $BASE_PATH/client/client.csr -passin pass:$CERT_PASSWORD -subj "$CERT_IDENTITY_CLIENT"

echo "Sign the client certificate with our CA cert"
openssl x509 -req -days 365 -in $BASE_PATH/client/client.csr -CA $BASE_PATH/server/ca.crt -CAkey $BASE_PATH/server/ca.key -CAcreateserial -out $BASE_PATH/client/client.crt -passin pass:$CERT_PASSWORD
