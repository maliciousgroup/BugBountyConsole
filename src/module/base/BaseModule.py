from src.core.registry.Registry import ModuleRegistry


class BaseModule(object):

    helper: dict = {}
    options: dict = {}

    def __init_subclass__(cls, **kwargs):
        try:
            assert isinstance(cls, type(BaseModule))
            ModuleRegistry().register_module(cls)
            super().__init_subclass__(**kwargs)
        except AssertionError:
            pass

    async def register(self) -> None:
        pass

    async def unregister(self) -> None:
        pass

    async def main(self) -> None:
        pass

    async def module_shell(self) -> None:
        pass

    async def execute(self) -> None:
        pass
