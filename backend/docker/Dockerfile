FROM python:3.11.4-slim-buster
LABEL maintainer="mateusiakdawid@gmail.com"

WORKDIR /backend

ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/usr/local/bin/poetry" \
    POETRY_VERSION=1.6.1 \
    PATH="$PATH:$POETRY_HOME/bin"

# Install system dependencies
RUN apt-get update && apt-get install -y netcat

# Copy app and settings
COPY ./backend/src /backend/src

# Install dependencies
ARG DEV="false"
RUN pip install "poetry==$POETRY_VERSION"
COPY ./backend/poetry.lock ./backend/pyproject.toml ./backend/settings.yaml /backend/
RUN poetry config virtualenvs.create false && \
    if [ $DEV = "true" ]; \
    then poetry install; \
    else poetry install --no-dev; \
    fi

# copy entrypoint.sh
COPY ./backend/docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh  \
    && chmod +x /entrypoint.sh

WORKDIR /backend/src

ENTRYPOINT ["/entrypoint.sh"]
