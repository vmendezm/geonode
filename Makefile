# Set variables to pass
DOCKER_HOST := $(DOCKER_HOST)
DOCKER_HOST_IP := `docker run --net=host codenvy/che-ip:nightly`

auto-up:
	# bring up the services with proper environment variables
	unset DOCKERHOST; \
	export DOCKERHOST=$(DOCKER_HOST); \
	echo Docker daemon is running at the following address $$DOCKERHOST; \
	unset GEONODE_LB_HOST_IP; \
	export GEONODE_LB_HOST_IP=$(DOCKER_HOST_IP); \
	echo GeoNode will be available at the following address http://$$GEONODE_LB_HOST_IP; \
	echo If you want to run it on localhost then remember to add this line "localhost $$GEONODE_LB_HOST_IP" to /etc/hosts; \
	docker-compose up -d --build

up:
	docker-compose up -d

build:
	docker-compose build django
	docker-compose build celery

sync: up
	# set up the database tables
	docker-compose exec django django-admin.py migrate --noinput
	docker-compose exec django django-admin.py loaddata sample_admin
	docker-compose exec django django-admin.py loaddata geonode/base/fixtures/default_oauth_apps_docker.json
	docker-compose exec django django-admin.py loaddata geonode/base/fixtures/initial_data.json

migrate:
	django-admin.py migrate --noinput

migrate_setup: migrate
	django-admin.py loaddata sample_admin

wait:
	sleep 5

logs:
	docker-compose logs --follow

down:
	docker-compose down

pull:
	docker-compose pull

smoketest: up
	docker-compose exec django python manage.py test geonode.tests.smoke --noinput --nocapture --detailed-errors --verbosity=1 --failfast

unittest: up
	docker-compose exec django python manage.py test geonode.people.tests geonode.base.tests geonode.layers.tests geonode.maps.tests geonode.proxy.tests geonode.security.tests geonode.social.tests geonode.catalogue.tests geonode.documents.tests geonode.api.tests geonode.groups.tests geonode.services.tests geonode.geoserver.tests geonode.upload.tests geonode.tasks.tests --noinput --failfast

test: smoketest unittest

reset: down up wait sync

hardreset: pull build reset

develop: pull build up sync

setup_worldmap:
	# setup databases for using the worldmap application
	export PG_USERNAME=$(PG_USERNAME); \
	export PG_PASSWORD=$(PG_PASSWORD); \
	export PG_WORLDMAP_DJANGO_DB=$(PG_WORLDMAP_DJANGO_DB); \
	export PG_WORLDMAP_UPLOADS_DB=$(PG_WORLDMAP_UPLOADS_DB); \
	export OWNER=$(OWNER); \
	sudo -u postgres psql -c "CREATE USER $(PG_USERNAME) WITH SUPERUSER PASSWORD '$(PG_PASSWORD)';" ;
	sudo -u postgres psql -c "CREATE DATABASE $(PG_WORLDMAP_DJANGO_DB) WITH OWNER $(OWNER);"
	sudo -u postgres psql -d $(PG_WORLDMAP_DJANGO_DB) -c "CREATE EXTENSION postgis;"
	sudo -u postgres psql -d $(PG_WORLDMAP_DJANGO_DB) -c "CREATE EXTENSION dblink;"
	sudo -u postgres psql -c "CREATE DATABASE $(PG_WORLDMAP_UPLOADS_DB) WITH OWNER $(OWNER);"
	sudo -u postgres psql -d $(PG_WORLDMAP_UPLOADS_DB) -c "CREATE EXTENSION postgis;"
	python manage.py migrate --noinput
	python manage.py loaddata sample_admin
	python manage.py loaddata geonode/base/fixtures/default_oauth_apps_docker.json
	python manage.py loaddata geonode/base/fixtures/initial_data.json

remove_worldmap:
	# remove databases for using the worldmap application
	sudo -u postgres psql -c "DROP DATABASE $(PG_WORLDMAP_DJANGO_DB);"
	sudo -u postgres psql -c "DROP DATABASE $(PG_WORLDMAP_UPLOADS_DB);"
	sudo -u postgres psql -c "DROP ROLE $(PG_USERNAME);"
	unset PG_USERNAME; \
	unset PG_PASSWORD; \
	unset PG_WORLDMAP_DJANGO_DB; \
	unset PG_WORLDMAP_UPLOADS_DB; \
	unset OWNER; \
