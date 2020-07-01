import asyncio

from src.core.command.base.BaseCommand import BaseCommand
from src.core.registry.Registry import OptionRegistry


class SetCommand(BaseCommand):

    helper: dict = {
        'name': 'set',
        'help': 'This command will allow the user to set key values',
        'usage': 'set <key> <value>'
    }

    def __init__(self, command: str, print_queue: asyncio.Queue):
        super().__init__()
        self.command: str = command
        self.print_queue: asyncio.Queue = print_queue
        self.option_register: OptionRegistry = OptionRegistry()

    async def main(self) -> None:
        await self.execute()

    async def execute(self) -> None:
        if len(self.command.split()) < 3:
            return
        params: list = self.command.split()
        if params[2] == '=':
            params.remove('=')
        if params[2] == '\"\"':
            params[2] = ''
        _, key, *value = tuple(params)

        if key in self.option_register.dump_register_pairs().keys():
            await self.print_queue.put(('bold', self.option_register.set_register(key, ' '.join(value))))
