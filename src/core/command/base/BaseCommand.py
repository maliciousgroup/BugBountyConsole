from src.core.registry.Registry import CommandRegistry


class BaseCommand(object):

    def __init_subclass__(cls, **kwargs):
        try:
            assert isinstance(cls, type(BaseCommand))
            CommandRegistry().register_command(cls)
            super().__init_subclass__(**kwargs)
        except AssertionError:
            pass

    async def execute(self) -> None:
        pass

    async def main(self) -> None:
        pass
