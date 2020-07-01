command_registry: dict = {}
option_registry:  dict = {}
module_registry:  dict = {}
provider_registry: dict = {}


class CommandRegistry(object):

    @staticmethod
    def register_command(cls) -> None:
        if cls.__name__ not in command_registry:
            command_registry[cls.__name__] = cls

    @staticmethod
    def dump_register() -> dict:
        return command_registry


class OptionRegistry(object):

    @staticmethod
    def register_options(options: dict) -> None:
        for a in options:
            options[a] = dict((k.lower(), v) for k, v in options[a].items() for a in options)
            option_registry.update(options)

    @staticmethod
    def dump_register() -> dict:
        return option_registry

    @staticmethod
    def dump_register_pairs() -> dict:
        pairs: dict = {}
        for x in option_registry:
            pairs.update(option_registry[x])
        return pairs

    @staticmethod
    def get_register(key: str) -> str:
        for a in option_registry:
            if key in option_registry[a]:
                return option_registry[a][key][0]

    @staticmethod
    def set_register(key: str, value: str) -> str:
        try:
            for a in option_registry:
                if key not in option_registry[a]:
                    continue
                required: str = option_registry[a][key.lower()][2]
                if not required or value in required.replace(' ', '').split(','):
                    option_registry[a][key.lower()][0] = value
                    return f'{key} => {value}\n'
                else:
                    return f"{value} is not in the list of allowed values: [{required}]\n"
        except KeyError:
            pass


class ModuleRegistry(object):

    @staticmethod
    def register_module(cls) -> None:
        if cls.__name__ not in module_registry:
            module_registry[cls.__name__] = cls

    @staticmethod
    def dump_register() -> dict:
        return module_registry


class ProviderRegistry(object):

    @staticmethod
    def register_provider(cls) -> None:
        if cls.__name__ not in provider_registry:
            provider_registry[cls.__name__] = cls

    @staticmethod
    def dump_register() -> dict:
        return provider_registry
