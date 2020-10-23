#!/usr/bin/env bash

# Certificates data, password and placement are customizable in this file
source ./certificates_data.custom

usage="$(basename "$0") [-h] [-s string] [-c string] -- Generate self signed certificates for server and client

where:
    -h  show this help text
    -s  <string> use <string> as CN parameter for the server certificate
    -c  <string> use <string> as CN parameter for the client certificate"

# Get user preferences for CN parameter in server/client certificates
SERVER_CN="*"
CLIENT_CN="*"

while getopts hc:s: option
do
 case "${option}"
 in
 h) echo "$usage"
    exit
    ;;
 s) SERVER_CN=${OPTARG};;
 c) CLIENT_CN=${OPTARG};;
 \?) echo "illegal option"
     echo "$usage"
     exit
     ;;
 esac
done

CERT_IDENTITY=$CERT_IDENTITY$SERVER_CN
CERT_IDENTITY_CLIENT=$CERT_IDENTITY_CLIENT$CLIENT_CN


# create folders
mkdir -p $BASE_PATH/server
mkdir -p $BASE_PATH/client


# CA----------------------------------------------------------------------------

echo "Create the CA Key and Certificate for signing Client Certs"
openssl genrsa -des3 -out $BASE_PATH/server/ca.key -passout pass:$CERT_PASSWORD 4096
openssl req -new -x509 -sha256 -days 365 -key $BASE_PATH/server/ca.key -out $BASE_PATH/server/ca.crt -passin pass:$CERT_PASSWORD -subj "$CERT_IDENTITY"


# Server -----------------------------------------------------------------------

echo "Create the Server Key, CSR, and Certificate"
openssl genrsa -des3 -out $BASE_PATH/server/server.key.org -passout pass:$CERT_PASSWORD 4096
# Remove password (avoid server claiming for it each time it starts)
openssl rsa -in $BASE_PATH/server/server.key.org -out $BASE_PATH/server/server.key -passin pass:$CERT_PASSWORD
# Generate server certificate
openssl req -new -sha256 -key $BASE_PATH/server/server.key -out $BASE_PATH/server/server.csr -passin pass:$CERT_PASSWORD -subj "$CERT_IDENTITY"

echo "Self-sign the certificate with our CA cert"
openssl x509 -req -sha256 -days 365 -in $BASE_PATH/server/server.csr -CA $BASE_PATH/server/ca.crt -CAkey $BASE_PATH/server/ca.key -set_serial 01 -out $BASE_PATH/server/server.crt -passin pass:$CERT_PASSWORD


# Client -----------------------------------------------------------------------

echo "Create the Client Key and CSR"
openssl genrsa -des3 -out $BASE_PATH/client/client.key.org -passout pass:$CERT_PASSWORD 4096
# Remove password (avoid https client claiming for it in each request)
openssl rsa -in $BASE_PATH/client/client.key.org -out $BASE_PATH/client/client.key -passin pass:$CERT_PASSWORD
# Generate client certificate
openssl req -new -sha256 -key $BASE_PATH/client/client.key -out $BASE_PATH/client/client.csr -passin pass:$CERT_PASSWORD -subj "$CERT_IDENTITY_CLIENT"

echo "Sign the client certificate with our CA cert"
openssl x509 -req -sha256 -days 365 -in $BASE_PATH/client/client.csr -CA $BASE_PATH/server/ca.crt -CAkey $BASE_PATH/server/ca.key -CAcreateserial -out $BASE_PATH/client/client.crt -passin pass:$CERT_PASSWORD
