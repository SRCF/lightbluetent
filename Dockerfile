FROM python:3.8-buster

RUN python3 -m pip install flask python-ucam-webauth werkzeug==0.16

VOLUME /app

EXPOSE 5000

WORKDIR /app
ENTRYPOINT ["flask"]
ENV FLASK_APP /app/lightbluetent/webapp/app.py
ENV FLASK_ENV development

CMD ["run", "--host", "0.0.0.0"]

# docker image build -t lightbluetent . 
# docker container run --rm -v ~/lightbluetent:/app -p 5000:5000 lightbluetent