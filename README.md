# SRCF LightBlueTent

A simple and elegant Flask webapp that turns managing society fairs and events into a piece of cake!

Features:

* user signup (via Raven) and management
* individual group/society webpages (stalls) for event/fair
* shared editing capabilities for users
* connects directly to Timeout (BigBlueButton)
* directory of registered groups

Upcoming features:

* integration with other video platforms
* administrator panel
* further customization of main page
* streamlined user sign-up process
* pre-signups (interested list) to events/fairs

Known events:

* Cambridge Students' Union Freshers' Fair 2020
* Queens' College JCR society fair

> Must be run within the CUDN for the Lookup queries to work properly

## Installation

### Requirements

* reverse proxy, eg. Apache/nginx
* pipenv
* python >3.8
* a relational database supported by `psycopg2`

### Instructions

1. Clone the repository's `master` branch
2. Copy the `.sample-env` file to `.env` and set variables
3. Copy the `lbt.service` file to the relevant `systemd` location*
4. Copy `.htaccess` to your `public_html` or `www` folder
5. Configure any settings needed in `lightbluetent/config.py`
6. Install the dependencies with `pipenv install`
7. Spawn a shell with the right environment variables `pipenv shell` and initialize and upgrade the database: `flask db init` and `flask db upgrade`
8. Edit the `run.sh` script to match directories of choice for the UNIX socket
9. Start the service

* For deployment on SRCF group accounts, follow instructions here: https://docs.srcf.net/app-hosting/index.html?highlight=systemctl
  
## Customization

### Strings

All strings have been pulled out into a file for easy customization. 

* Modify the required strings in `lightbluetent/translations/en/LC_MESSAGES/messages.po`
* `pybabel compile -d translations` to compile the translations
* Further infomation for using flask-babel is [here](https://flask-babel.tkte.ch/)

### Environment variables

The existing variables are set for development. Remove them and uncomment the ones meant for production. The BigBlueButton server provided is for testing so you should request a secret from mw781.

* `FLASK_ENV` defaults to production
* `FLASK_CONFIG=production` sets which config file to load
* `POSTGRES_DB` leave this field empty, it's meant for `docker-compose`
* Database variables; edit accordingly
  
```env
POSTGRES_USER=postgres
POSTGRES_HOSTNAME=postgres
POSTGRES_PASSWORD=
APPLICATION_DB=lightbluetent
```

* `SQLALCHEMY_URI="postgresql+psycopg2://user@host:port/table"` this overrides the above database variables if provided
* `FLASK_TRUSTED_HOSTS` set this to the domain that will be used
* `FLASK_SECRET_KEY` secret key needed by flask; generate however

### Logging

Logs are made available in `production.log` and the log level can be set accordingly in `run.sh`.

### Change a user's role

Make someone an admin by running `flask change-role [list of crsids] administrator` making sure to load the environment variables with `pipenv shell` beforehand.

## Development

### Getting started

1. Clone this repository:
  
```bash
git clone https://github.com/SRCF/lightbluetent.git
```

1. Start the containers: `cd lightbluetent` and then `docker-compose -p development -f docker/development.yml up -d`
1. Navigate to localhost:5000 to see the app

## Application structure

* the web app lives in `lightbluetent`
  * templates and static files live in their own folders
    * folders correspond to the name of the view that renders them
  * views live in the folder root
* `json` configuration for environment variables live in `config`
* `docker` contains Docker-related files
* `tests` contains unit tests that are run with `py-test`

### Environment variables

* `APPLICATION_CONFIG` is strictly related to the project and is used only to load a JSON configuration file with the name specified in the variable itself. By default is equal to `development` and is set to `testing` when running tests.
* `FLASK_CONFIG` is used to select the Python object that contains the configuration for the Flask application (see application/app.py and application/config.py). The value of the variable is converted into the name of a class. Values are testing, development and production.
* `FLASK_ENV` is a variable used by Flask itself, and its values are dictated by it. See the configuration documentation mentioned in the resources of the previous section.

## Workflow


### Testing

* `./manage.py test` will run all the tests defined in `tests`
* creates a temporary PostgreSQL database but does not run the full web server

### Development

`docker-compose` will automtically look for a .env file and load those environment variables.

* Copy .sample-env to .env and fill in the values (defaults for dev)
* Make sure you have [Pipenv](https://pypi.org/project/pipenv/) installed
* install dependencies with `pipenv install --dev`
* `PIPENV_DONT_LOAD_ENV=1 pipenv shell` to spawn a shell with the dependencies installed
* Remove the env var if you want to perform any database migrations or upgrade, in this case we want to load the variables so psycopg2 can connect
* `docker-compose -p development -f docker/development.yml up -d` to build and run the Flask container and the PostgreSQL container, attach the `-d` flag optionally to run the containers as daemons in the background
* `docker-compose -p development -f docker/development.yml down` to tear down the containers

#### Database management

DB data is preserved in a docker volume. To remove the volume, `docker volume ls` and then use the relevant command to delete the volume. This wipes your local dev DB. The next time the container starts up, it will generate an empty database called `lightbluetent`.

* `flask db init` to fill the `lightbluetent` database with our schema
* `flask db migrate -m "your message"` and `flask db upgrade` to complete a database migration, do this every time you change the DB structure

Note: make sure to spawn a shell with the right env vars before running these commands

Project structure and base code based on [this tutorial](https://www.thedigitalcatonline.com/blog/2020/07/06/flask-project-setup-tdd-docker-postgres-and-more-part-2/)
