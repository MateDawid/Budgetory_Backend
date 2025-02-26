FROM python:3.12.9-slim-bookworm as base-image

ARG DEV="false"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/usr/local/bin/poetry" \
    POETRY_VERSION=2.1.1 \
    PATH="$PATH:$POETRY_HOME/bin"

# Copy settings
COPY ./poetry.lock ./pyproject.toml ./settings.yaml /app/

# Install poetry
RUN pip install "poetry==$POETRY_VERSION"

# Install app dependencies
RUN poetry config virtualenvs.create false && \
    if [ $DEV = "true" ]; \
    then poetry install; \
    else poetry install --no-dev; \
    fi

# Copy app
COPY ./src /app/src

FROM base-image as test-image

COPY ./tests /app/tests

FROM base-image as release-image

RUN addgroup --gid 1001 --system app && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group app

# Prepare entrypoint.sh
COPY ./docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh  \
    && chmod +x /entrypoint.sh

WORKDIR /app/src

USER app

ENTRYPOINT ["/entrypoint.sh"]
