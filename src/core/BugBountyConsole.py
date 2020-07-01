import asyncio
import signal

from ruamel.yaml import YAML, YAMLError
# noinspection PyUnresolvedReferences
from src.module import *
# noinspection PyUnresolvedReferences
from src.core.command import *
# noinspection PyUnresolvedReferences
from src.provider import *
from src.core.utility.Utility import Utility
from src.core.registry.Registry import *
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.styles import Style

ansi = Utility.colors()
prompt_style = Style.from_dict({"prompt": "ansired bold"})


class BugBountyConsole(object):

    def __init__(self, config_file: str):
        self.config_file: str = config_file
        self.prompt_text: str = ''
        self.print_queue: asyncio.Queue = asyncio.Queue()
        self.module_register: ModuleRegistry = ModuleRegistry()
        self.option_register: OptionRegistry = OptionRegistry()
        self.command_register: CommandRegistry = CommandRegistry()
        self.provider_register: ProviderRegistry = ProviderRegistry()

    def print_numbers(self) -> None:
        pq: asyncio.Queue = self.print_queue
        number_of_providers: int = len(self.provider_register.dump_register())
        number_of_commands: int = len(self.command_register.dump_register())
        number_of_modules: int = len(self.module_register.dump_register())
        pq.put_nowait(('bold', f"+ -- --=[ {number_of_providers:>3} {'Providers':<10} ]"))
        pq.put_nowait(('bold', f"+ -- --=[ {number_of_commands:>3} {'Commands':<10} ]"))
        pq.put_nowait(('bold', f"+ -- --=[ {number_of_modules:>3} {'Modules':<10} ]\n"))
        pq.put_nowait('')

    def register_options(self) -> None:
        try:
            yaml = YAML()
            with open(self.config_file, "r") as conf:
                self.option_register.register_options(yaml.load(conf))
            self.print_numbers()
        except YAMLError:
            print(f"Error processing YAML/JSON configuration file: {self.config_file}\n")
            exit(1)

    async def interactive_shell(self) -> None:
        session: PromptSession = PromptSession()
        while True:
            self.prompt_text = self.option_register.get_register('prompt_text')
            try:
                data: str = await session.prompt_async(f"{self.prompt_text} > ", style=prompt_style)
                if not data:
                    continue
                await self.command_interpreter(data.strip())
            except (EOFError, KeyboardInterrupt):
                return

    async def command_interpreter(self, data: str) -> None:
        module_list: dict = self.module_register.dump_register()
        command_list: dict = self.command_register.dump_register()
        for command in command_list:
            if not asyncio.iscoroutinefunction(command_list[command].main):
                continue
            if data.partition(' ')[0] == command_list[command].helper['name']:
                if command_list[command].helper['name'] == 'shell':
                    task = asyncio.create_task(command_list[command](data, self.print_queue).main())
                    task.set_name(data)
                else:
                    await asyncio.gather(command_list[command](data, self.print_queue).main())

        if data.startswith('use ') and data.split(' ')[1]:
            for module in module_list:
                if not asyncio.iscoroutinefunction(module_list[module].main):
                    continue
                if data.split(' ')[1] == module_list[module].helper['name']:
                    await asyncio.gather(module_list[module](data.split(' ')[1], self.print_queue, self).main())

    async def print_processor(self) -> None:
        while True:
            try:
                while self.print_queue.empty() is not True:
                    msg = await self.print_queue.get()
                    if isinstance(msg, str):
                        print(f"{msg}")
                    elif isinstance(msg, tuple):
                        if msg[0] == 'error':
                            print(f"{ansi['red']}{msg[1]}{ansi['reset']}")
                        elif msg[0] == 'success':
                            print(f"{ansi['green']}{msg[1]}{ansi['reset']}")
                        elif msg[0] == 'warning':
                            print(f"{ansi['yellow']}{msg[1]}{ansi['reset']}")
                        elif msg[0] == 'bold':
                            print(f"{ansi['bold']}{msg[1]}{ansi['reset']}")
                        else:
                            print(f'{msg[1]}')
                await asyncio.sleep(0.00001)
            except asyncio.CancelledError:
                await self.shutdown(asyncio.get_running_loop())

    @staticmethod
    async def shutdown(_loop) -> None:
        print(f"Received exit signal and gracefully shutting down...")
        print(f"Stopping all running tasks...", end="")
        tasks = [t.cancel() for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        await asyncio.gather(*tasks)
        _loop.stop()
        print(f"{ansi['green']}OK!{ansi['reset']}\n")

    async def main(self) -> None:
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        signals = (signal.SIGINT, signal.SIGTERM)
        for sig in signals:
            try:
                loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self.shutdown(loop)))
            except NotImplementedError:
                pass
        with patch_stdout():
            printer_task: asyncio.Task = asyncio.create_task(self.print_processor())
            printer_task.set_name('Task-PrintProcessor')
            try:
                asyncio.current_task().set_name('Task-Main')
                await self.interactive_shell()
            except asyncio.CancelledError:
                pass
            finally:
                printer_task.cancel()
