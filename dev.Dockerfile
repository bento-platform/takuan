FROM python:3.12

ARG USERNAME=tds-user
ARG USER_UID=1000
ARG USER_GID=${USER_UID}

LABEL org.opencontainers.image.description="Local development image for the Transcriptomics Data Service."
LABEL devcontainer.metadata='[{ \
  "remoteUser": ${USERNAME}, \
  "customizations": { \
    "vscode": { \
      "extensions": ["ms-python.python", "eamodio.gitlens", "ms-python.black-formatter"], \
      "settings": {"workspaceFolder": "/tds"} \
    } \
  } \
}]'

# SETUP NON-ROOT USER
RUN groupadd --gid ${USER_GID} ${USERNAME} \
    && useradd --uid ${USER_UID} --gid ${USER_GID} ${USERNAME} \
    && apt-get update -y \
    && apt-get install -y sudo \
    && echo ${USERNAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USERNAME} \
    && chmod 0440 /etc/sudoers.d/${USERNAME}
USER ${USERNAME}

# Install dev utils
RUN apt-get update -y; \
    apt-get upgrade -y; \
    apt-get install -y \
            bash \
            build-essential \
            curl \
            git \
            gosu \
            jq \
            libpq-dev \
            perl \
            procps \
            vim; \
    rm -rf /var/lib/apt/lists/*; \
    pip install --no-cache-dir -U pip; \
    pip install --no-cache-dir poetry==1.8.5; \
    pip install --no-cache-dir 'uvicorn[standard]>=0.34.0,<0.35'

# FastAPI uses uvicorn for a development server as well
RUN pip install --upgrade pip && pip install --no-cache-dir "uvicorn[standard]==0.30.1"
WORKDIR /tds

COPY pyproject.toml .
COPY poetry.lock .

COPY run.dev.bash .

# Install production + development dependencies
# Without --no-root, we get errors related to the code not being copied in yet.
# But we don't want the code here, otherwise Docker cache doesn't work well.
RUN poetry config virtualenvs.create false && \
    poetry --no-cache install --no-root

# Tell the service that we're running a local development container
ENV BENTO_CONTAINER_LOCAL=true

# Don't copy in actual code, since it'll be mounted in via volume for development
CMD [ "bash", "./run.dev.bash" ]
