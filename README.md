# SRCF LightBlueTent

A simple Flask webapp to power the 2020 University of Cambridge Freshers' Fair via Timeout

## Development

### Environment variables

* `APPLICATION_CONFIG` is strictly related to the project and is used only to load a JSON configuration file with the name specified in the variable itself.
* `FLASK_CONFIG` is used to select the Python object that contains the configuration for the Flask application (see application/app.py and application/config.py). The value of the variable is converted into the name of a class.
* `FLASK_ENV` is a variable used by Flask itself, and its values are dictated by it. See the configuration documentation mentioned in the resources of the previous section.


### Getting started

1. Clone this repository:
  
```bash
git clone https://github.com/SRCF/lightbluetent.git
```

1. Start the containers: `cd lightbluetent` and then `./manage.py compose up -d`
1. Navigate to localhost:5000 to see the app
