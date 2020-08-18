#!/usr/bin/env bash

# Certificates data, password and placement are customizable in this file
source ./certificates_data.custom

# Get user preferences for CN parameter in server/client certificates
usage="$(basename "$0") [-h] [-c string] -- Generate self signed certificates for client

where:
    -h  show this help text
    -c  <string> use <string> as CN parameter for the client certificate"

CLIENT_CN="*"

while getopts hc: option
do
 case "${option}"
 in
 h) echo "$usage"
    exit
    ;;
 c) CLIENT_CN=${OPTARG};;
 \?) echo "illegal option"
     echo "$usage"
     exit
     ;;
 esac
done

CERT_IDENTITY_CLIENT=$CERT_IDENTITY_CLIENT$CLIENT_CN

# create folders
mkdir -p $BASE_PATH/client

# Client -----------------------------------------------------------------------

echo "Create the Client Key and CSR"
openssl genrsa -des3 -out $BASE_PATH/client/client.key.org -passout pass:$CERT_PASSWORD 4096
# Remove password (avoid https client claiming for it in each request)
openssl rsa -in $BASE_PATH/client/client.key.org -out $BASE_PATH/client/client.key -passin pass:$CERT_PASSWORD
# Generate client certificate
openssl req -new -sha256 -key $BASE_PATH/client/client.key -out $BASE_PATH/client/client.csr -passin pass:$CERT_PASSWORD -subj "$CERT_IDENTITY_CLIENT"

echo "Sign the client certificate with our CA cert"
openssl x509 -req -sha256 -days 365 -in $BASE_PATH/client/client.csr -CA $BASE_PATH/server/ca.crt -CAkey $BASE_PATH/server/ca.key -CAcreateserial -out $BASE_PATH/client/client.crt -passin pass:$CERT_PASSWORD
