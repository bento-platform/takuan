FROM ghcr.io/bento-platform/bento_base_image:python-debian-2024.07.09

RUN pip install --no-cache-dir "uvicorn[standard]==0.30.1"

WORKDIR /tds

COPY pyproject.toml .
COPY poetry.lock .

RUN poetry config virtualenvs.create false && \
    poetry --no-cache install --without dev --no-root

COPY transcriptomics_data_service transcriptomics_data_service
COPY entrypoint.bash .
COPY run.bash .
COPY LICENSE .
COPY README.md .

# Install the module itself, locally (similar to `pip install -e .`)
RUN poetry install --without dev

ENTRYPOINT [ "bash", "./entrypoint.bash" ]
CMD [ "bash", "./run.bash" ]
