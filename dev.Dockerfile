ARG PYTHON_VERSION=3.12
ARG DEBIAN_VERSION=slim-bookworm

FROM python:${PYTHON_VERSION}-${DEBIAN_VERSION}

# LABELS
LABEL Maintainer="Bento Project"
LABEL org.opencontainers.image.description="Local development image for the Transcriptomics Data Service."
LABEL devcontainer.metadata='[{ \
  "customizations": { \
    "vscode": { \
      "extensions": ["ms-python.python", "eamodio.gitlens", "ms-python.black-formatter"], \
      "settings": {"workspaceFolder": "/tds"} \
    } \
  }, \
  "remoteUser": "tds" \
}]'

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
    rm -rf /var/lib/apt/lists/*;

RUN pip install --no-cache-dir -U pip; \
    pip install --no-cache-dir poetry==2.2.1; \
    pip install --no-cache-dir 'uvicorn[standard]>=0.38.0,<0.39'

# INIT DIRECTORIES
RUN mkdir /tds /run/secrets
WORKDIR /tds

COPY pyproject.toml .
COPY poetry.lock .
COPY gosu_entrypoint.bash .
COPY run.dev.bash .

# Install production + development dependencies
# Without --no-root, we get errors related to the code not being copied in yet.
# But we don't want the code here, otherwise Docker cache doesn't work well.
RUN poetry config virtualenvs.create false && \
    poetry --no-cache install --no-root

RUN chmod +x ./*.bash

# Don't copy in actual code, since it'll be mounted in via volume for development
ENTRYPOINT [ "bash", "./gosu_entrypoint.bash" ]
CMD [ "bash", "./run.dev.bash" ]
