# StarHub Telegram Bot (Python)

## Documentation

- [Encryption Algorithm](/docs/encryption-algorithm.md)
- [Endpoints](/docs/endpoints.md)

## To build Docker image

```bash
docker build -t vantablack/starhub-tg-bot .
```

### To remove intermediate stage image

Reason why there is a intermediate stage is because of the attempt to reduce the
final image size of the bot by using the Alpine image instead of the full Python
image.

[Building Minimal Docker Containers for Python Applications](https://blog.realkinetic.com/building-minimal-docker-containers-for-python-applications-37d0272c52f3)

See: https://github.com/moby/moby/issues/34513

```bash
docker image prune --filter label=stage=removeme
```

## To run Docker image

https://github.com/moby/moby/issues/4830#issuecomment-264366876

```bash
docker run -d --name starhub-bot -v `pwd`/config:/app/config:ro vantablack/starhub-tg-bot
```

```bash
docker run -d --name starhub-bot -v `pwd`/config:/app/config:ro vantablack/starhub-tg-bot && docker logs -f starhub-bot
```

```bash
docker run -d --rm --name starhub-bot -v `pwd`/config:/app/config:ro vantablack/starhub-tg-bot && docker logs -f starhub-bot
```
