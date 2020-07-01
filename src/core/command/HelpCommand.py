import asyncio

from src.core.utility.Utility import Utility

from src.core.command.base.BaseCommand import BaseCommand
from src.core.registry.Registry import CommandRegistry, ModuleRegistry

ansi = Utility.colors()


class HelpCommand(BaseCommand):

    helper: dict = {
        'name': 'help',
        'help': 'This command will print all the available help information',
        'usage': 'help'
    }

    def __init__(self, command: str, print_queue: asyncio.Queue):
        super().__init__()
        self.command: str = command
        self.print_queue: asyncio.Queue = print_queue
        self.module_register: ModuleRegistry = ModuleRegistry()
        self.command_register: CommandRegistry = CommandRegistry()

    async def main(self) -> None:
        await self.execute()

    async def execute(self) -> None:

        await self.print_queue.put(f"\n{ansi['red']}Command List\n{ansi['red']}{'=' * 12}{ansi['reset']}")
        field_names = [f'{"Command":<20}', f'{"Usage":<20}', f'{"Description":<30}']
        field_values = []
        commands_list = self.command_register.dump_register()
        for cls in commands_list:
            info = commands_list[cls].helper
            field_values.append([info['name'], info['usage'], info['help']])
        output: str = Utility.create_table(field_names, field_values)
        await self.print_queue.put(f"{output}\n")

        if len(self.module_register.dump_register()) <= 0:
            return

        await self.print_queue.put(f"\n{ansi['red']}Module List\n{ansi['red']}{'=' * 11}{ansi['reset']}")
        field_names = [f'{"Module":<20}', f'{"Usage":<20}', f'{"Description":<30}']
        field_values = []
        modules_list = self.module_register.dump_register()
        for cls in modules_list:
            info = modules_list[cls].helper
            field_values.append([info['name'], info['usage'], info['help']])
        output: str = Utility.create_table(field_names, field_values)
        await self.print_queue.put(f"{output}\n")
