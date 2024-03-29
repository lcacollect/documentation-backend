# Introduction

This repo is a [git submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules). Thus changes made here will be reflected in external sources, which requires a certain workflow to ensure consistency for all developers who depend on this repo.
Besides that it functions as any other repo.

# Getting Started

To get started please make sure that the following pieces of software are installed on your machine.

# Software dependencies

## Windows

-   [WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10)
-   [Docker](https://docs.docker.com/desktop/windows/install/)
-   [Minikube](https://minikube.sigs.k8s.io/docs/start/)
-   [Skaffold](https://skaffold.dev/docs/install/#standalone-binary)
-   [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows?
-   Python 3.10
-   [pipenv](https://pipenv.pypa.io/en/latest/#install-pipenv-today)
-   [pre-commit](https://pre-commit.com/#installation)

## Linux

-   [Docker](https://docs.docker.com/engine/install/ubuntu/)
-   [Minikube](https://minikube.sigs.k8s.io/docs/start/)
-   [Skaffold](https://skaffold.dev/docs/install/#standalone-binary)
-   [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-linux?pivots=apt)
-   Python 3.10
-   [pipenv](https://pipenv.pypa.io/en/latest/#install-pipenv-today)
-   [pre-commit](https://pre-commit.com/#installation)

## Getting the backend up and running

**Setup local `.env`**
Copy the contents of `.env.example` to a local `.env` file.

**Install dependencies**
```shell
# Load environment variables
source .env .

# Install packages
pipenv install --dev

# Install pre-commit hooks
pre-commit install
```

**Start dev server**

Remember to source the .env file before starting Skaffold
To set the content of the .env file as env vars run `export $(grep -v '^#' .env | xargs)`

```shell
# Start Minikube to run a local Kubernetes cluster
minikube start

# Set ENV
export $(grep -v '^#' .env | xargs)

# Run Skaffold
skaffold dev
```

**Run tests locally**

```shell
pytest tests/
```

**Make migration**
Skaffold should be running!

```shell
./local_migration.sh
```

**Export GraphQL schema**

```shell
./export_schema.sh
```


# Folder Structure

```plaintext
alembic/  # Contains migrations
graphql/  # Contains graphql schema for the gateway
helm/  # helm chart for deployment
src/  # source code
    core/  # code related to FastAPI/webserver
    exceptions/  # custom exceptions
    models/  # database models
    routes/  # api routes
    schema/  # graphql schema definitions
tests/  # test code
```

# License

Unless otherwise described, the code in this repository is licensed under the Apache-2.0 License. Please note that some
modules, extensions or code herein might be otherwise licensed. This is indicated either in the root of the containing
folder under a different license file, or in the respective file's header. If you have any questions, don't hesitate to
get in touch with us via [email](mailto:chrk@arkitema.com).