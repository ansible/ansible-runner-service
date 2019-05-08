#!/usr/bin/env sh

CERT_IDENTITY="/C=ES/ST=Madrid/L=Madrid/O=ClientOrg/OU=Automation/CN=AnsibleRunnerService"
CERT_PASSWORD="ansible"
BASE_PATH="/etc/ansible-runner-service/certs"

# create folders
mkdir -p $BASE_PATH/client

# Client -----------------------------------------------------------------------

echo "Create the Client Key and CSR"
openssl genrsa -des3 -out $BASE_PATH/client/client.key.org -passout pass:$CERT_PASSWORD 1024
# Remove password (avoid https client claiming for it in each request)
openssl rsa -in $BASE_PATH/client/client.key.org -out $BASE_PATH/client/client.key -passin pass:$CERT_PASSWORD
# Generate client certificate
openssl req -new -key $BASE_PATH/client/client.key -out $BASE_PATH/client/client.csr -passin pass:$CERT_PASSWORD -subj "$CERT_IDENTITY"

echo "Sign the client certificate with our CA cert"
openssl x509 -req -days 365 -in $BASE_PATH/client/client.csr -CA $BASE_PATH/server/ca.crt -CAkey $BASE_PATH/server/ca.key -CAcreateserial -out $BASE_PATH/client/client.crt -passin pass:$CERT_PASSWORD
