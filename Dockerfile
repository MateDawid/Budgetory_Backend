FROM python:3.11.4-slim-buster
LABEL maintainer="mateusiakdawid@gmail.com"

WORKDIR /usr/src/budget_manager

ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/usr/local/bin/poetry" \
    POETRY_VERSION=1.6.1 \
    PATH="$PATH:$POETRY_HOME/bin"

# Install system dependencies
RUN apt-get update && apt-get install -y netcat

# Install dependencies
ARG DEV="false"
RUN pip install "poetry==$POETRY_VERSION"
COPY ./poetry.lock ./pyproject.toml ./settings.yaml /usr/src/budget_manager/
RUN poetry config virtualenvs.create false && \
    if [ $DEV = "true" ]; \
    then poetry install; \
    else poetry install --no-dev; \
    fi

# copy entrypoint.sh
COPY ./entrypoint.sh /usr/src/budget_manager/
RUN sed -i 's/\r$//g' /usr/src/budget_manager/entrypoint.sh
RUN chmod +x /usr/src/budget_manager/entrypoint.sh

# Copy app and settings
COPY ./backend /usr/src/budget_manager/backend/
WORKDIR /usr/src/budget_manager/backend/

ENTRYPOINT ["/usr/src/budget_manager/entrypoint.sh"]
