# SRCF LightBlueTent

A simple Flask webapp to power the 2020 University of Cambridge Freshers' Fair via Timeout

## Development

### Environment variables

* `APPLICATION_CONFIG` is strictly related to the project and is used only to load a JSON configuration file with the name specified in the variable itself. By default is equal to `development` and is set to `testing` when running tests.
* `FLASK_CONFIG` is used to select the Python object that contains the configuration for the Flask application (see application/app.py and application/config.py). The value of the variable is converted into the name of a class. Values are testing, development and production.
* `FLASK_ENV` is a variable used by Flask itself, and its values are dictated by it. See the configuration documentation mentioned in the resources of the previous section.

### Getting started

1. Clone this repository:
  
```bash
git clone https://github.com/SRCF/lightbluetent.git
```

1. Start the containers: `cd lightbluetent` and then `docker-compose -f docker/development.yml up`
1. Navigate to localhost:5000 to see the app

## Application structure

* the web app lives in `lightbluetent`
  * templates and static files live in their own folders
    * folders correspond to the name of the view that renders them
  * views live in the folder root
* `json` configuration for environment variables live in `config`
* `docker` contains Docker-related files
* `tests` contains unit tests that are run with `py-test`

## Workflow

### Production

unclear

Must be run within the CUDN for Lookup queries to function correctly.

### Testing

* `./manage.py test` will run all the tests defined in `tests`
* creates a temporary PostgreSQL database but does not run the full web server

### Development

* Make sure you have [Pipenv](https://pypi.org/project/pipenv/) installed
* install dependencies with `pipenv install --dev`
* `pipenv shell` to spawn a shell with the dependencies installed
* `./manage.py flask run` to run the web app locally (not recommended)
* `./manage.py compose up` to build and run the Flask container and the PostgreSQL container, attach the `-d` flag optionally to run the containers as daemons in the background
* `./manage.py compose down` to tear down the containers

#### Database management

DB data is preserved in a docker volume. To remove the volume, `docker volume ls` and then use the relevant command to delete the volume. This wipes your local dev DB. The next time the container starts up, it will generate an empty database called `lightbluetent`.

* `./manage.py flask db init` to fill the `lightbluetent` database with our schema
* `./manage.py flask db migrate -m "your message"` and `./manage.py flask db upgrade` to complete a database migration, do this every time you change the DB structure

Project structure and base code based on [this tutorial](https://www.thedigitalcatonline.com/blog/2020/07/06/flask-project-setup-tdd-docker-postgres-and-more-part-2/)
