#!/bin/bash

# Setup non-root user
USER_NAME=${TDS_USER_NAME}
USER_ID=${TDS_UID:-1000}
GROUP_ID=${TDS_GID:-$USER_ID}
groupadd -g "${GROUP_ID}" -r ${USER_NAME}
useradd --shell /bin/bash -u "${USER_ID}" -r -g "${GROUP_ID}" --non-unique -c "TDS container user" -m ${USER_NAME}
export HOME=/home/${USER_NAME}
echo "PATH=/home/${USER_NAME}/.local/bin/:\$PATH" >> "/home/${USER_NAME}/.bashrc"

chown -R ${USER_NAME}:${USER_NAME} /tds
chown -R ${USER_NAME}:${USER_NAME} /run/secrets

# Drop into ${USER_NAME} from root and execute the CMD specified for the image
exec gosu "${USER_NAME}" "$@"
