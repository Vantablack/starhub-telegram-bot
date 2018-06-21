# StarHub Telegram Bot (Python)

## Documentation

- [Encryption Algorithm](/docs/encryption-algorithm.md)
- [Endpoints](/docs/endpoints.md)

## To build Docker image

```bash
docker build -t vantablack/starhub-tg-bot .
```

## To run Docker image

https://github.com/moby/moby/issues/4830#issuecomment-264366876

```bash
docker run -d --name starhub-bot -v `pwd`/config:/app/config:ro vantablack/starhub-tg-bot
```

```bash
docker run -d --name starhub-bot -v `pwd`/config:/app/config:ro vantablack/starhub-tg-bot && docker logs -f starhub-bot
```