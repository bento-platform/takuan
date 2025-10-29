ARG PYTHON_VERSION=3.12
ARG DEBIAN_VERSION=slim-bookworm

FROM python:${PYTHON_VERSION}-${DEBIAN_VERSION}

LABEL Maintainer="Bento Project"

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

RUN mkdir /tds /run/secrets
WORKDIR /tds

COPY pyproject.toml .
COPY poetry.lock .

RUN poetry config virtualenvs.create false && \
    poetry --no-cache install --without dev --no-root

COPY transcriptomics_data_service transcriptomics_data_service
COPY gosu_entrypoint.bash .
COPY run.bash .
COPY LICENSE .
COPY README.md .

# Install the module itself, locally (similar to `pip install -e .`)
RUN poetry install --without dev

RUN chmod +x ./*.bash

ENTRYPOINT [ "bash", "./gosu_entrypoint.bash" ]
CMD [ "bash", "./run.bash" ]
