import asyncio

from src.core.command.base.BaseCommand import BaseCommand
from src.core.registry.Registry import OptionRegistry


class BackCommand(BaseCommand):

    helper: dict = {
        'name': 'back',
        'help': 'This command will back out to the main console',
        'usage': 'back'
    }

    def __init__(self, command: str, print_queue: asyncio.Queue):
        super().__init__()
        self.command: str = command
        self.print_queue: asyncio.Queue = print_queue
        self.option_register: OptionRegistry = OptionRegistry()

    async def main(self) -> None:
        await self.execute()

    async def execute(self) -> None:
        options: dict = self.option_register.dump_register()
        if 'module' in options.keys():
            options.pop('module')
            self.option_register.register_options(options)
