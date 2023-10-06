FROM python:3.11.4-slim-buster
LABEL maintainer="mateusiakdawid@gmail.com"

WORKDIR /usr/src/budget_app

ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/usr/local/bin/poetry" \
    POETRY_VERSION=1.6.1 \
    PATH="$PATH:$POETRY_HOME/bin"

# Install system dependencies
RUN apt-get update && apt-get install -y netcat

# Install dependencies
RUN pip install "poetry==$POETRY_VERSION"
COPY ./poetry.lock ./pyproject.toml ./settings.yaml ./.secrets.yaml /usr/src/budget_app/
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# copy entrypoint.sh
COPY ./entrypoint.sh /usr/src/budget_app/
RUN sed -i 's/\r$//g' /usr/src/budget_app/entrypoint.sh
RUN chmod +x /usr/src/budget_app/entrypoint.sh

# Copy app and settings
COPY ./budget_api /usr/src/budget_app/budget_api/
WORKDIR /usr/src/budget_app/budget_api/

ENTRYPOINT ["/usr/src/budget_app/entrypoint.sh"]
