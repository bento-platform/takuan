# OPA authorization example

This sample authorization plugin showcases how to use OPA as the authorization service for TDS.
While this could be done in pure Python with HTTP, 
using the [OPA client for Python](https://github.com/Turall/OPA-python-client) can offer advantages.

As described in the authz module docs, additional dependencies can be provided for the authorization plugin.
In this example, we include the OPA client as an additional dependency.

Furthermore, the OPA server details are provided with extra environment configurations.

## Contents
- [Authz plugin](authz.module.py)
- [Extra configuration](example.env)
- [Additional python dependencies](requirements.txt)

## Instructions

```bash
# Copy the module to the mount directory
cp authz_plugins/opa/authz.module.py lib/

# Copy the extra environment variable file to the mount directory
cp authz_plugins/opa/example.env lib/.env

# Copy the additional Python dependencies to the mount directory
cp authz_plugins/opa/requirements.txt lib/

# Start the service
docker compose up --build
```
