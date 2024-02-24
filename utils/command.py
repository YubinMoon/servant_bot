from discord.ext.commands import Command


def get_command_description(prefix: str, command: Command) -> str:
    description = command.description.partition("\n")[0]
    return f"{prefix}{command.name} - {description}"


def get_group_command_description(prefix: str, group: str, command: Command) -> str:
    description = command.description.partition("\n")[0]
    return f"{prefix}{group} {command.name} - {description}"
