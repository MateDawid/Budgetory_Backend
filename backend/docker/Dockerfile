FROM python:3.11.4-slim-buster as base-image

# Install system dependencies
RUN apt-get update && apt-get install -y netcat

WORKDIR /backend

ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/usr/local/bin/poetry" \
    POETRY_VERSION=1.6.1 \
    PATH="$PATH:$POETRY_HOME/bin"

# Copy app and settings
COPY ./backend/src /backend/src

# Install poetry
RUN pip install "poetry==$POETRY_VERSION"
COPY ./backend/poetry.lock ./backend/pyproject.toml ./backend/settings.yaml /backend/

FROM base-image as testing-image

# Install dependencies with testing utils
RUN poetry config virtualenvs.create false && \
    poetry install \

COPY ./backend/tests /backend/tests

CMD ['python', '-m', 'pytest']

FROM base-image as release-image

ARG DEV="false"

# Install app dependencies
RUN poetry config virtualenvs.create false && \
    if [ $DEV = "true" ]; \
    then poetry install; \
    else poetry install --no-dev; \
    fi
# Prepare entrypoint.sh
COPY ./backend/docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh  \
    && chmod +x /entrypoint.sh

WORKDIR /backend/src

ENTRYPOINT ["/entrypoint.sh"]
