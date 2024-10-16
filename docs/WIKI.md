

# Application run
## Build images
```commandline
docker compose -f docker-compose.yaml build
```
## Run application
```commandline
docker stop $(docker ps -q)
docker compose -f docker-compose.yaml up -d
```
# Tests run
## Build images
```commandline
docker compose -f docker-compose-tests.yaml build
```
## Run tests
```commandline
docker stop $(docker ps -q)
docker compose -f docker-compose-tests.yaml run backend sh -c "python src/manage.py wait_for_db && python src/manage.py migrate && python src/manage.py migrate"
```
