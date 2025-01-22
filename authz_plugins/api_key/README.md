# API key authorization example

This sample authorization plugin authorizes requests with an API key header.

## Contents
- [Authz plugin](authz.module.py)
- [Extra configuration](example.env)

## Instructions

```bash
# Copy the module to the mount directory
cp authz_plugins/api_key/authz.module.py lib/

# Copy the extra environment variables file to the mount directory
cp authz_plugins/api_key/example.env lib/.env

# optional: modify the API key value in lib/.env

# Start the service
docker compose up --build
```
