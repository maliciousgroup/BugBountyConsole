from src.core.registry.Registry import ProviderRegistry


class BaseProvider(object):

    def __init_subclass__(cls, **kwargs):
        try:
            assert isinstance(cls, type(BaseProvider))
            ProviderRegistry().register_provider(cls)
            super().__init_subclass__(**kwargs)
        except AssertionError:
            pass

    async def get_data_set(self):
        pass

    async def fetch_url(self, url: str):
        pass
