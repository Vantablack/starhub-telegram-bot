# References
#
# https://runnable.com/docker/python/dockerize-your-python-application
# https://gist.github.com/justingood/020e24222fa1653f5cd0

FROM python:3.6.5

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

VOLUME /app/config

CMD [ "python", "./starhub_bot.py" ]