import asyncio
import requests
import json

from src.provider.base.BaseProvider import BaseProvider
from src.core.registry.Registry import OptionRegistry

from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


class WayBackProvider(BaseProvider):

    black_list: list = ['woff', 'woff2', 'css', 'js', 'php', 'png', 'gif', 'jpg', 'jpeg', 'svg', 'wav', 'mpg', 'ico']

    def __init__(self, print_queue: asyncio.Queue, domain: str, sub_domains: bool):
        self.print_queue: asyncio.Queue = print_queue
        self.domain: str = domain
        self.session: requests.Session = requests.Session()
        self.sub_domains: bool = sub_domains
        self.option_register: OptionRegistry = OptionRegistry()

    async def get_data_set(self) -> list:
        enabled: bool = True if self.option_register.get_register('way_back_machine') == 'true' else False
        if not enabled:
            await self.print_queue.put(('warning', f"[*] Skipping the 'Way Back Machine' Provider per user option.\n"))
            return []

        await self.print_queue.put(('success', f"[+] Collecting data from the 'Way Back Machine' CDX data set"))
        await asyncio.sleep(1)

        urls: list = []
        domain: str = self.domain
        url: str = f"http://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&collapse=urlkey&fl=original"
        if self.sub_domains:
            url: str = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&collapse=urlkey&fl=original"
        data: str = await self.fetch_url(url)
        try:
            if "Blocked Site Error" in data:
                await self.print_queue.put(('warning', f"[?] The 'Way Back Machine' Provider has blocked this domain."))
                await self.print_queue.put('')
                return []
            json_data = json.loads(data)
            for key in json_data:
                url: str = ''.join(key).replace(':80', '').replace(':443', '')
                if url.endswith(tuple(self.black_list)) or not url.startswith('http'):
                    continue
                urls.append(url)
            urls = list(set(urls))
            await self.print_queue.put(('success', f"[-] Collected {len(urls)} unique URL(s) for domain '{domain}'\n"))
            await asyncio.sleep(1)

            return urls
        except TypeError as e:
            await self.print_queue.put(('error', f"Error decoding JSON - {e.__str__()}\n"))
        except json.JSONDecodeError as e:
            await self.print_queue.put(('error', f"Error decoding the JSON from CDX Provider - {e.__str__()}\n"))

    async def fetch_url(self, url: str) -> str:
        try:
            with self.session as session:
                retry = Retry(connect=3, backoff_factor=1, status_forcelist=[429, 504])
                adapter = HTTPAdapter(max_retries=retry)
                session.mount('http://', adapter=adapter)
                session.mount('https://', adapter=adapter)
                request = self.session.get(url)
                return request.text
        except requests.RequestException as e:
            await self.print_queue.put(('error', f"{e.__str__()}\n"))
