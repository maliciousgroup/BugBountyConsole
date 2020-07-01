import asyncio

from src.core.utility.Utility import Utility
from src.core.registry.Registry import OptionRegistry
from src.core.command.base.BaseCommand import BaseCommand

ansi = Utility.colors()


class OptionsCommand(BaseCommand):

    helper: dict = {
        'name': 'options',
        'help': 'This command will print the currently available options',
        'usage': 'options'
    }

    def __init__(self, command: str, print_queue: asyncio.Queue):
        super().__init__()
        self.command: str = command
        self.print_queue: asyncio.Queue = print_queue
        self.options_register: OptionRegistry = OptionRegistry()

    async def main(self) -> None:
        await self.execute()

    async def execute(self) -> None:
        approved_keys: list = ['provider', 'module', 'console']
        used_keys: list = []
        options: dict = self.options_register.dump_register()
        for x in options.keys():
            if x not in approved_keys:
                continue

            if 'module' in options.keys():
                used_keys.append('module') if 'module' not in used_keys else None
                await self.print_queue.put('')
                await self.print_queue.put(('error', f"Module Options"))
                await self.print_queue.put(('error', f"==============\n"))
                field_names: list = [
                    f"{'Option':<20}",
                    f"{'Setting':<20}",
                    f"{'Description':<30}"
                ]
                field_values: list = []
                for item in options['module'].items():
                    field_values.append([item[0], item[1][0], item[1][1]])
                output: str = Utility.create_table(field_names, field_values)
                await self.print_queue.put(output)
                await self.print_queue.put('')
                return

            if 'provider' in options.keys() and 'provider' not in used_keys:
                used_keys.append('provider') if 'provider' not in used_keys else None
                await self.print_queue.put('')
                await self.print_queue.put(('error', f"Provider Options"))
                await self.print_queue.put(('error', f"================\n"))
                field_names: list = [
                    f"{'Option':<20}",
                    f"{'Setting':<20}",
                    f"{'Description':<30}"
                ]
                field_values: list = []
                for item in options['provider'].items():
                    field_values.append([item[0], item[1][0], item[1][1]])
                output: str = Utility.create_table(field_names, field_values)
                await self.print_queue.put(output)
                await self.print_queue.put('')

            if 'console' in options.keys() and 'console' not in used_keys:
                used_keys.append('console') if 'console' not in used_keys else None
                await self.print_queue.put('')
                await self.print_queue.put(('error', f"Console Options"))
                await self.print_queue.put(('error', f"===============\n"))
                field_names: list = [
                    f"{'Option':<20}",
                    f"{'Setting':<20}",
                    f"{'Description':<30}"
                ]
                field_values: list = []
                for item in options['console'].items():
                    field_values.append([item[0], item[1][0], item[1][1]])
                output: str = Utility.create_table(field_names, field_values)
                await self.print_queue.put(output)
                await self.print_queue.put('')
