# References
#
# https://runnable.com/docker/python/dockerize-your-python-application
# https://gist.github.com/justingood/020e24222fa1653f5cd0
# https://blog.realkinetic.com/building-minimal-docker-containers-for-python-applications-37d0272c52f3
# https://pythonspeed.com/articles/multi-stage-docker-python/
#
# Adding -u flag for Python:
# https://stackoverflow.com/questions/29663459/python-app-does-not-print-anything-when-running-detached-in-docker
#
# Pipenv
# https://pythonspeed.com/articles/pipenv-docker/

FROM python:3.6-slim as base
FROM base as builder
COPY Pipfile* /tmp/
RUN pip install pipenv
RUN cd /tmp && pipenv lock --requirements > requirements.txt
RUN pip install --user --no-warn-script-location -r /tmp/requirements.txt
COPY src /app
WORKDIR /app
VOLUME /app/config
# Expose port 80 for WebHook server
EXPOSE 80
CMD [ "python", "-u", "starhub_bot.py" ]
