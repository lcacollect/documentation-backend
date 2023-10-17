#! /usr/bin/bash
set -e

export SERVER_NAME="LCA Test"
export SERVER_HOST="http://test"
export PROJECT_NAME="LCA Test"
export POSTGRES_HOST=localhost
export POSTGRES_USER=postgresuser
export POSTGRES_PASSWORD=mypassword
export POSTGRES_DB=documentation
export POSTGRES_PORT=5435
export AAD_OPENAPI_CLIENT_ID=PLACEHOLDER
export AAD_APP_CLIENT_ID=PLACEHOLDER
export AAD_TENANT_ID=PLACEHOLDER
export AAD_GRAPH_SECRET=PLACEHOLDER
export STORAGE_ACCOUNT_URL=PLACEHOLDER
export STORAGE_CONTAINER_NAME=PALCEHOLDER
export STORAGE_ACCESS_KEY=PLACEHOLDER
export STORAGE_BASE_PATH=PLACEHOLDER
export ROUTER_URL=PLACEHOLDER
export SPECKLE_TOKEN=placeholder
export EMAIL_NOTIFICATION_FROM=no-reply@arkitema.com
export INTERNAL_EMAIL_DOMAINS_LIST=arkitema,cowi,cowicloud
export DEFAULT_AD_FQDN=cowi.onmicrosoft.com
export SENDGRID_SECRET=PLACEHOLDER

alembic revision --autogenerate
