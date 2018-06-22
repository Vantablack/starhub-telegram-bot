# References
#
# https://runnable.com/docker/python/dockerize-your-python-application
# https://gist.github.com/justingood/020e24222fa1653f5cd0
#
# Adding -u flag for Python:
# https://stackoverflow.com/questions/29663459/python-app-does-not-print-anything-when-running-detached-in-docker

FROM python:3.6.5

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

VOLUME /app/config

CMD [ "python", "-u", "starhub_bot.py" ]