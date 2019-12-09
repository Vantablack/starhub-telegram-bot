# StarHub Telegram Bot (Python)

## Why?

I created this bot back when the old StarHub app was horrible. Navigating to the data usage page takes a few taps and
every movement was being tracked (analytics).

Since I spend more time on Telegram, why not create a bot that improves
that experience of retrieving that information?

![screenshot](/images/screenshot.png)

## Documentation

- [Encryption Algorithm](/docs/encryption-algorithm.md)
- [Endpoints 2018](/docs/endpoints.md)
- [Endpoint 2019 Changes](/docs/starhub_2019_changes.md)

## To build Docker image

```bash
docker build -t starhub-tg-bot .
```

### To remove intermediate stage image

Reason why there is a intermediate stage is because of the attempt to reduce the
final image size of the bot by using the Python-Slim image instead of the full Python
image.

[Building Minimal Docker Containers for Python Applications](https://blog.realkinetic.com/building-minimal-docker-containers-for-python-applications-37d0272c52f3)

See: https://github.com/moby/moby/issues/34513

```bash
docker image prune --filter label=stage=removeme
```

## To run Docker image

https://github.com/moby/moby/issues/4830#issuecomment-264366876

```bash
docker run -d --name starhub-bot -v `pwd`/config:/app/config:ro starhub-tg-bot
```

```bash
docker run -d --name starhub-bot -v `pwd`/config:/app/config:ro starhub-tg-bot && docker logs -f starhub-bot
```

```bash
docker run -d --rm --name starhub-bot -v `pwd`/config:/app/config:ro starhub-tg-bot && docker logs -f starhub-bot
```
