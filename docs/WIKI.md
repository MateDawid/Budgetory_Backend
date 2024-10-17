# 1. Application run locally

1. Setup and activate venv
```commandline
$ python -m venv venv
$ venv\Scripts\activate
```
2. Install poetry
```commandline
$(venv) pip install poetry
```
3. Install dependencies
```commandline
$(venv) poetry install
```
4. Load data
```commandline
$(venv) python src/manage.py loaddata src/test_data.json
```
5. Run API
```commandline
$(venv) python src/manage.py runserver
```
# 2. Application run in Docker
## Build images
```commandline
docker compose -f docker-compose.yaml build
```
## Run application
```commandline
docker stop $(docker ps -q)
docker compose -f docker-compose.yaml up -d
```
Additionally load data:
```commandline
docker compose exec backend "python manage.py loaddata test_data.json"
```

# 3. Tests run in Docker
## Build images
```commandline
docker compose -f docker-compose-tests.yaml build
```
## Run tests
```commandline
docker stop $(docker ps -q)
docker compose -f docker-compose-tests.yaml run backend sh -c "python src/manage.py wait_for_db && python src/manage.py migrate && python src/manage.py migrate"
```
