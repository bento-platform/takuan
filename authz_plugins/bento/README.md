# Bento authorization

This is the authorization middleware used to authorize TDS requests with the
[Bento Authorization Service](https://github.com/bento-platform/bento_authorization_service).

## Contents
- [Authz plugin](./authz.module.py)

## Instructions

```bash
# Copy the module to the mount directory
cp authz_plugins/bento/authz.module.py lib/

# Start the service
docker compose up --build
```
