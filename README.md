# Servant Bot

**Simple All‑in‑One Discord Bot**

This repository is simple discord bot.  
This bot is based on [Python-Discord-Bot-Template](https://github.com/kkrypt0nn/Python-Discord-Bot-Template) by [kkrypt0nn](https://github.com/kkrypt0nn)

## How to set up

### `.env` file

To set up the token you will have to either make use of the [`.env.example`](.env.example) file, either copy or rename it to `.env` and replace `YOUR_BOT_TOKEN_HERE` with your bot's token.

Alternatively you can simply create an environment variable named `TOKEN`.

### Docker

Before you start, make sure you have [Docker](https://www.docker.com/) installed.

```bash
docker -v .env:/bot/.env -v status.txt:/bot/status.txt --name servant-bot ghcr.io/yubinmoon/servant_bot:latest
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE.md](LICENSE.md) file for details
