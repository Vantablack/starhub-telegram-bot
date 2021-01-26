# StarHub Telegram Bot (Python)

## Why?

I created this bot back when the old StarHub app was horrible.

Navigating to the data usage page takes a few taps and
every movement was being tracked (analytics).

Since I spend more time on Telegram, why not create a bot that simplifies the experience of retrieving that information?

![screenshot](docs/screenshot.png)

The main tools used were:

- [mitmproxy](https://mitmproxy.org/)
- [\[GitHub\] skylot/jadx](https://github.com/skylot/jadx) to decompile
[My StarHub](https://play.google.com/store/apps/details?id=com.starhub.csselfhelp) app

## Relevant Documentation

- [StarHub Endpoints](docs/endpoints.md)
  - [December 2019 Changes](docs/starhub_2019_changes.md)
- [Encryption Algorithm (WIP)](docs/encryption-algorithm.md)

## Deployment

How this project is deployed is through

### Build Docker Image

```bash
docker build -t starhub-tg-bot .
```

### Run Docker Image

```bash
docker run -d --name starhub-tg-bot -v `pwd`/config:/app/config:ro starhub-tg-bot
```

```bash
docker run -d --name starhub-tg-bot -v `pwd`/config:/app/config:ro starhub-tg-bot && docker logs -f starhub-bot
```

```bash
docker run -d --rm --name starhub-tg-bot -v `pwd`/config:/app/config:ro starhub-tg-bot && docker logs -f starhub-bot
```

https://github.com/moby/moby/issues/4830#issuecomment-264366876

## Development

I am currently using Pipenv to manage the packages required for this project.

**Pipenv sets the Python version to 3.9**.

Follow [this guide](https://pipenv-fork.readthedocs.io/en/latest/install.html#installing-pipenv)
to install Pipenv.

To install all the required packages from Pipfile:

```bash
pipenv install
```

To activate a shell with all the packages:

```bash
pipenv shell
```

To run the bot:

```bash
python3 /src/main.py
```
