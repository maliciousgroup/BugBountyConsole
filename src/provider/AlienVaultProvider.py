import asyncio
import requests
import json

from src.provider.base.BaseProvider import BaseProvider
from src.core.registry.Registry import OptionRegistry

from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


class AlienVaultProvider(BaseProvider):

    def __init__(self, print_queue: asyncio.Queue, domain: str, sub_domains: bool):
        self.print_queue: asyncio.Queue = print_queue
        self.domain: str = domain
        self.session: requests.Session = requests.Session()
        self.sub_domains: bool = sub_domains
        self.option_register: OptionRegistry = OptionRegistry()

    async def get_data_set(self) -> list:
        enabled: bool = True if self.option_register.get_register('alien_vault') == 'true' else False
        if not enabled:
            await self.print_queue.put(('warning', f"[*] Skipping the 'Alien Vault' Provider per user option.\n"))
            await asyncio.sleep(1)
            return []

        await self.print_queue.put(('success', f"[+] Collecting data from the 'Alien Vault' OTX data set"))

        urls: list = []
        domain: str = self.domain
        url = f"https://otx.alienvault.com/api/v1/indicators/hostname/{domain}/url_list?limit=9999&matchType=prefix"
        if self.sub_domains:
            url = f"https://otx.alienvault.com/api/v1/indicators/hostname/{domain}/url_list?limit=9999&matchType=domain"
        data: str = await self.fetch_url(url)
        try:
            json_data = json.loads(data)
            for key in json_data['url_list']:
                urls.append(str(key["url"]).replace(':80', '').replace(':443', ''))
            urls = list(set(urls))
            await self.print_queue.put(('success', f"[-] Collected {len(urls)} unique URL(s) for domain '{domain}'\n"))
            await asyncio.sleep(1)

            return urls
        except TypeError as e:
            await self.print_queue.put(('error', f"Error decoding JSON - {e.__str__()}\n"))
        except json.JSONDecodeError:
            await self.print_queue.put(('error', f"Error decoding the JSON from OTX Provider.\n"))

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
