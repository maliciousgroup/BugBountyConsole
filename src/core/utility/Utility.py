from prettytable import PrettyTable


class Utility(object):

    @staticmethod
    def create_table(field_names: list, field_values: list) -> str:
        t = PrettyTable()
        t.border = False
        t.padding_width = 2
        t.field_names = field_names
        sep = []
        for _value in field_names:
            sep += ['-' * len(_value)]
        t.add_row(sep)
        for _value in field_values:
            t.add_row(_value)
            t.align = 'l'
        return "{}".format(t.get_string())

    @staticmethod
    def colors() -> dict:
        _colors: dict = {
            'red': '\x1b[31;1m',
            'green': '\x1b[32;1m',
            'yellow': '\x1b[33;1m',
            'bold': '\x1b[1m',
            'reset': '\x1b[0m'
        }
        return _colors
