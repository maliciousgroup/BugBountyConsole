import asyncio

from src.core.command.base.BaseCommand import BaseCommand


class ExitCommand(BaseCommand):

    helper: dict = {
        'name': 'exit',
        'help': 'This command will gracefully exit the application',
        'usage': 'exit'
    }

    def __init__(self, command: str, print_queue: asyncio.Queue):
        super().__init__()
        self.command: str = command
        self.print_queue: asyncio.Queue = print_queue

    async def main(self) -> None:
        await self.execute()

    async def execute(self) -> None:
        raise EOFError
