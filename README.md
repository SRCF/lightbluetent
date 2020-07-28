# SRCF LightBlueTent

A simple Flask webapp to power the 2020 University of Cambridge Freshers' Fair via Timeout

## Development

You can use Docker to make the development process much simpler.

1. Ensure you have Docker installed
1. Clone this repository:
```
git clone https://github.com/SRCF/lightbluetent.git
```
1. Enter the directory: `cd lightbluetent`
1. Build the Docker image: `docker image build -t lightbluetent .`
1. Run the Docker image:
```
docker container run --rm -v ~/lightbluetent:/app -p 5000:5000 lightbluetent
```
1. Navigate to localhost:5000 to see the app



