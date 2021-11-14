import calendar
from argparse import ArgumentParser, RawTextHelpFormatter
from datetime import datetime
from json import dumps
from os import chdir, system
from pathlib import Path
from sys import _MEIPASS as root_dir, exit

from pyperclip import copy as copy_to_clipboard

from npbc_core import NPBC_core

# from gooey import Gooey

CONFIG_FILEPATH = Path(Path.home()) / '.npbc' / 'config.json'
# CONFIG_FILEPATH = Path('data') / 'config.json'
HELP_FILEPATH = Path(f'includes/undelivered_help.pdf')

class NPBC_cli(NPBC_core):
    functions = {
        'calculate': {
            'choice': 'calculate',
            'help': "Calculate the bill for one month. Previous month will be used if month or year flags are not set."
        },
        'addudl': {
            'choice': 'addudl',
            'help': "Store a date when paper(s) were not delivered. Previous month will be used if month or year flags are not set."
        },
        'deludl': {
            'choice': 'deludl',
            'help': "Delete a stored date when paper(s) were not delivered. Previous month will be used if month or year flags are not set."
        },
        'editpaper': {
            'choice': 'editpaper',
            'help': "Edit a newspaper's name, key, and other delivery data."
        },
        'addpaper': {
            'choice': 'addpaper',
            'help': "Add a new newspaper to the list of newspapers."
        },
        'delpaper': {
            'choice': 'delpaper',
            'help': "Delete a newspaper from the list of newspapers."
        },
        'editconfig': {
            'choice': 'editconfig',
            'help': "Edit filepaths of record files and newspaper data."
        },
        'update': {
            'choice': 'update',
            'help': "Update the application."
        },
        'ui': {
                'choice': 'ui',
                'help': "Launch interactive CLI."
        }
    }

    arguments = {
        'month': {
            'short': '-m',
            'long': '--month',
            'type': int,
            'help': "Month to calculate bill for. Must be between 1 and 12.",
        },
        'year': {
            'short': '-y',
            'long': '--year',
            'type': int,
            'help': "Year to calculate bill for. Must be between 1 and 9999.",
        },
        'undelivered': {
            'short': '-u',
            'long': '--undelivered',
            'type': str,
            'help': "Dates when you did not receive any papers.",
        },
        'files': {
            'short': '-f',
            'long': '--files',
            'type': str,
            'help': "Data for filepaths to be edited.",
        },
        'key': {
            'short': '-k',
            'long': '--key',
            'type': str,
            'help': "Key for paper to be edited, deleted, or added.",
        },
        'name': {
            'short': '-n',
            'long': '--name',
            'type': str,
            'help': "Name for paper to be edited or added.",
        },
        'days': {
            'short': '-d',
            'long': '--days',
            'type': str,
            'help': "Number of days the paper to be edited or added, is delivered. Monday is the first day, and all seven weekdays are required. A 'Y' means it is delivered, and an 'N' means it isn't. No separator required.",
        },
        'price': {
            'short': '-p',
            'long': '--price',
            'type': str,
            'help': "Daywise prices of paper to be edited or added. Monday is the first day. Values must be separated by semicolons, and 0s are ignored.",
        },
        'nolog': {
            'short': '-l',
            'long': '--nolog',
            'help': "Don't log the result of the calculation.",
            'action': 'store_true'
        },
        'nocopy': {
            'short': '-c',
            'long': '--nocopy',
            'help': "Don't copy the result of the calculation to the clipboard.",
            'action': 'store_true'
        }
    }

    def __init__(self):
        chdir(root_dir)
        self.load_files()
        self.args = self.define_and_read_args()

    def define_and_read_args(self):
        self.parser = ArgumentParser(
            description="Calculates your monthly newspaper bill.",
            formatter_class=RawTextHelpFormatter
        )

        self.parser.add_argument(
            'command',
            # nargs='?',
            choices=[value['choice'] for key, value in self.functions.items()],
            help='\n'.join([f"{value['choice']}: {value['help']}" for key, value in self.functions.items()])
        )

        for key, value in self.arguments.items():
            if 'action' in value:
                self.parser.add_argument(
                    value['short'],
                    value['long'],
                    action=value['action'],
                    help=value['help']
                )

            else:
                self.parser.add_argument(
                    value['short'],
                    value['long'],
                    type=value['type'],
                    help=value['help']
                )

        return self.parser.parse_args()

    def format_and_copy(self):
        string = f"For {datetime(self.year, self.month, 1):%B %Y}\n\n"
        string += f"*TOTAL: {self.totals.pop('TOTAL')}*\n"

        for paper_key, value in self.totals.items():
            string += f"{self.papers[paper_key]['name']}: {value}\n"

        print(string)

        if not self.args.nocopy:
            copy_to_clipboard(string)

    def calculate(self):
        self.undelivered_strings_to_dates()
        self.calculate_all_papers()
        self.format_and_copy()

        if not self.args.nolog:
            self.save_results()

class NPBC_cli_args(NPBC_cli):
    def __init__(self):
        NPBC_cli.__init__(self)

    def check_args(self):
        if self.args.command == 'calculate' or self.args.command == 'addudl' or self.args.command == 'deludl':

            if self.args.month is None and self.args.year is None:
                self.month = self.get_previous_month().month
                self.year = self.get_previous_month().year

            elif self.args.month is not None and self.args.year is None:
                self.month = self.args.month
                self.year = datetime.today().year

            elif self.args.month is None and self.args.year is not None:
                self.month = datetime.today().month
                self.year = self.args.year

            else:
                self.month = self.args.month
                self.year = self.args.year

            self.prepare_dated_data()

            if self.args.command != 'deludl':

                if self.args.undelivered is not None:
                    undelivered_data = self.args.undelivered.split(';')

                    for paper in undelivered_data:
                        paper_key, undelivered_string = paper.split(':')

                        self.undelivered_strings[f"{self.month}/{self.year}"][paper_key].append(
                            undelivered_string)

                if self.args.command == 'calculate':
                    self.calculate()

                else:
                    self.addudl()

            else:
                self.deludl()

        elif self.args.command == 'addpaper':
            self.create_new_paper(self.args.key, self.args.name, self.extract_days_and_cost())

        elif self.args.command == 'delpaper':
            self.delete_existing_paper(self.args.key)

        elif self.args.command == 'editpaper':
            self.edit_existing_paper(self.args.key, self.args.name, self.extract_days_and_cost())

        elif self.args.command == 'editconfig':
            self.edit_config_files()

        elif self.args.command == 'update':
            self.update()

    def extract_days_and_cost(self):
        sold = [int(i == 'Y') for i in self.args.days]
        prices = self.args.price.split(';')

        days = {}
        prices = [price for price in prices if int(price) != 0]

        delivered_count = 0

        for day in range(7):
            delivered = sold[day]
            
            day_name = calendar.day_name[day]
            days[day_name] = {}

            days[day_name]['cost'] = float(prices[delivered_count])
            days[day_name]['sold'] = delivered

            delivered_count += delivered
        return days

    def edit_config_files(self):
        filepaths = self.args.files.split(';')

        for filepath in filepaths:
            path_key, path = filepath.split(':')

            if path_key in self.config:
                self.config[path_key] = path

        with open(CONFIG_FILEPATH, 'w') as config_file:
            config_file.write(dumps(self.config))

    def run(self):
        if self.args.command != 'ui' and self.args.command in self.functions:
            self.check_args()
        
        else:
            exit(1)

class NPBC_cli_interactive(NPBC_cli):
    def __init__(self):
        NPBC_cli.__init__(self)
        
    def run_ui(self):
        task = input(
            "What do you want to do right now? ([c]alculate, edit the [p]apers, edit the [f]iles configuration, [a]dd undelivered data, [r]emove undelivered data, [u]pdate, or e[x]it) ").strip().lower()

        if task in ['c', 'calculate', 'a', 'add', 'r', 'remove']:
            month = input(
                "\nPlease enter the month you want to calculate (either enter a number, or leave blank to use the previous month): ")

            if month.isdigit():
                self.month = int(month)

            else:
                self.month = self.get_previous_month().month

            year = input(
                "\nPlease enter the year you want to calculate (either enter a number, or leave blank to use the year of the previous month): ")

            if year.isdigit():
                self.year = int(year)

            else:
                self.year = self.get_previous_month().year

            self.prepare_dated_data()

            if task not in ['r', 'remove']:
                self.acquire_undelivered_papers()

                if task in ['c', 'calculate']:
                    self.calculate()

                else:
                    self.addudl()

            else:
                self.deludl()

        elif task in ['p', 'papers']:
            self.edit_papers()

        elif task in ['f', 'files']:
            self.edit_config_files()

        elif task in ['u', 'update']:
            self.update()

        elif task in ['x', 'exit']:
            pass

    def edit_papers(self):
        print ("The following papers currently exist.\n")

        for paper_key in self.papers:
            print (f"{paper_key}: {self.papers[paper_key]['name']}")
        

        mode = input(
            "\n Do you want to create a [n]ew newspaper, [e]dit an existing one, [d]elete an existing one, or e[x]it? ").lower().strip()

        if (mode in ['n', 'ne', 'new']) or (mode in ['e', 'ed', 'edi', 'edit']) or (mode in ['d', 'de', 'del', 'dele', 'delet', 'delete']):
            paper_key = input("\nEnter the key of the paper to edit: ")

            if mode in ['n', 'ne', 'new']:
                if paper_key in self.papers:
                    print(f"{paper_key} already exists. Please try editing it.")
                    exit(1)

                paper_name = input("\nWhat is the name of the newspaper? ")

                paper_days = {}

                for day in calendar.day_name:
                    sold = input(f"\nIs the newspaper sold on {day}? ([y]es/[N]o) ")

                    if sold.lower() in ['y', 'ye', 'yes']:
                        sold = int(True)
                        cost = float(input(f"What is the cost on {day}? "))

                    else:
                        sold = int(False)
                        cost = 0.0

                    paper_days[day] = {'sold': sold, 'cost': cost}

                self.create_new_paper(paper_key, paper_name, paper_days)

                print(f"\n{paper_name} has been added.")

            elif mode in ['e', 'ed', 'edi', 'edit']:
                if paper_key not in self.papers:
                    print(f"{paper_key} does not exist. Please try again.")
                    exit(1)

                new_paper_name = input("Enter a new name for the paper, or leave blank to retain: ")

                if not new_paper_name:
                    new_paper_name = self.papers[paper_key]['name']

                paper_days = {}

                for day in calendar.day_name:
                    sold = input(f"\nIs the newspaper sold on {day}? ([y]es/[N]o) ")

                    if sold.lower() in ['y', 'ye', 'yes']:
                        sold = int(True)
                        cost = float(input(f"What is the cost on {day}? "))

                    else:
                        sold = int(False)
                        cost = 0.0

                    paper_days[day] = {'sold': sold, 'cost': cost}

                self.edit_existing_paper(paper_key, new_paper_name, paper_days)

                print(f"\n{new_paper_name} has been edited.")

            elif mode in ['d', 'de', 'del', 'dele', 'delet', 'delete']:
                if paper_key not in self.papers:
                    print(f"{paper_key} does not exist. Please try again.")
                    exit(1)

                self.delete_existing_paper(paper_key)

                print(f"\n{paper_key} has been deleted.")
            

        elif mode.lower() in ['x', 'ex', 'exi', 'exit']:
            pass

        else:
            print("\nInvalid mode. Please try again.")

    def acquire_undelivered_papers(self):
        confirmation = input(
            "\nDo you want to report any undelivered data? ([Y]es/[n]o) ")

        while confirmation.lower() in ['y', 'ye,' 'yes']:
            print("These are the available newspapers:\n")

            for paper_key, value in self.papers.items():
                print(f"\t{paper_key}: {value['name']}")

            print("\tall: ALL NEWSPAPERS\n")

            paper_key = input(
                "Please enter the key of the newspaper you want to report, or press Return to cancel: ")

            if paper_key == '':
                pass

            elif (paper_key in self.papers) or (paper_key == 'all'):
                self.report_undelivered_dates(paper_key)

            else:
                print("Invalid key. Please try again.")

            confirmation = input(
                "Do you want to report any more undelivered data? ([Y]es/[n]o) ")

    def report_undelivered_dates(self, paper_key: str):
        finished = False
        string = ""

        while not finished:
            string = input(f"Please tell us when {paper_key} was undelivered, or enter '?' for help: ").strip()

            if string == '?' or string == '':
                system(HELP_FILEPATH)

            else:
                self.undelivered_strings[f"{self.month}/{self.year}"][paper_key].append(
                    string)

                finished = True

    def edit_config_files(self):
        print("\nThe following filepaths can be edited:")

        for key in self.config:
            print(f"{key}: {self.config[key]}")

        confirmation = input(
            "\nDo you want to edit any of these paths? ([Y]es/[n]o) ").lower().strip()

        while confirmation in ['y', 'ye', 'yes']:

            invalid = True

            while invalid:
                path_key = input("\nPlease enter the path key to edit: ")

                if path_key in self.config:
                    self.config[path_key] = input(
                        f"Please enter the new path for {path_key}: ")
                    invalid = False

                else:
                    print("Invalid key. Please try again.")

            confirmation = input(
                "\nDo you want to edit any more of these paths? ([Y]es/[n]o) ").lower().strip()

        with open(CONFIG_FILEPATH, 'w') as config_file:
            config_file.write(dumps(self.config))

    def run(self):
        if self.args.command == 'ui':
            self.run_ui()

def ui():
    calculator = NPBC_cli_interactive()
    calculator.run()
    del calculator

# @Gooey
def cli():
    calculator = NPBC_cli_args()
    calculator.run()
    del calculator

def main():
    ui()
    cli()
    exit(0)

if __name__ == '__main__':
    main()
