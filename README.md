# Simple Discord Bot with chatGPT 

This repository is simple discord bot with chatGPT. This bot is based on [Python-Discord-Bot-Template](https://github.com/kkrypt0nn/Python-Discord-Bot-Template) by [kkrypt0nn](https://github.com/kkrypt0nn)

## Disclaimer

Slash commands can take some time to get registered globally, so if you want to test a command you should use
the `@app_commands.guilds()` decorator so that it gets registered instantly. Example:

```py
@commands.hybrid_command(
  name="command",
  description="Command description",
)
@app_commands.guilds(discord.Object(id=GUILD_ID)) # Place your guild ID here
```

When using the template you confirm that you have read the [license](LICENSE.md) and comprehend that I can take down
your repository if you do not meet these requirements.

## How to set up

To set up the bot it was made as simple as possible.

### `config.json` file

There is [`config.json`](config.json) file where you can put the
needed things to edit.

Here is an explanation of what everything is:

| Variable                  | What it is                                     |
| ------------------------- | ---------------------------------------------- |
| YOUR_BOT_PREFIX_HERE      | The prefix you want to use for normal commands |
| YOUR_BOT_INVITE_LINK_HERE | The link to invite the bot                     |

### `.env` file

To set up the token you will have to either make use of the [`.env.example`](.env.example) file, either copy or rename it to `.env` and replace `YOUR_BOT_TOKEN_HERE` with your bot's token.

Alternatively you can simply create an environment variable named `TOKEN`.

## How to start

To start the bot you simply need to launch, either your terminal (Linux, Mac & Windows), or your Command Prompt (
Windows)
.

Before running the bot you will need to install all the requirements with this command:

```
python -m pip install -r requirements.txt
```

After that you can start it with

```
python bot.py
```

> **Note** You may need to replace `python` with `py`, `python3`, `python3.11`, etc. depending on what Python versions you have installed on the machine.

## Built With

- [Python 3.10.13](https://www.python.org/)

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE.md](LICENSE.md) file for details
