## import modules
from argparse import ArgumentParser, RawTextHelpFormatter
import argparse
from calendar import day_name as weekday_names
from calendar import monthrange
from datetime import date as date_type
from datetime import datetime, timedelta
from json import dumps, loads
from os import chdir, system
from pathlib import Path
from sys import _MEIPASS as root_dir
from sys import exit

# from gooey import Gooey
from pyperclip import copy as copy_to_clipboard

## set up path constants for some files
# CONFIG_FILEPATH = Path('data') / 'config.json'
CONFIG_FILEPATH = Path.home() / '.npbc' / 'config.json'  # main config file with other paths
HELP_FILEPATH = Path(f'includes/undelivered_help.pdf')  # help file for undelivered strings

## core functionality—limited UI
class NPBC_core():

    ## set properties
    month = 0  # month to calculate for
    year = 0  # year to calculate for
    totals = {'TOTAL': 0.0}  # total cost for each newspaper
    undelivered_dates = {}  # dates when newspapers weren't delivered

    ## load in source data files
    def load_files(self) -> None:

        ## open main config file
        with open(CONFIG_FILEPATH, 'r') as config_file:
            self.config = loads(config_file.read())

        ## if app has been run for the first time, set root path to .npbc inside users home directory
        if self.config['root_folder'] == 'UNSET':

            ## save new path to config file
            self.config['root_folder'] = f"{str(Path.home())}/.npbc"

            with open(CONFIG_FILEPATH, 'w') as config_file:
                config_file.write(dumps(self.config))

        ## set up files and folders if they do not exist
        self.define_file_structure()

        ## open papers data file, which has keys, names, days of delivery, and cost per day
        with open(Path(f"{self.config['root_folder']}/{self.config['papers_data']}"), 'r') as papers_file:
            self.papers = loads(papers_file.read())

        ## open undelivered strings file, which has undelivered strings
        with open(Path(f"{self.config['root_folder']}/{self.config['undelivered_strings']}"), 'r') as undelivered_file:
            self.undelivered_strings = loads(undelivered_file.read())

        ## populate undelivered dates and totals as zeros/empty values
        for paper_key in self.papers:
            self.totals[paper_key] = 0.0
            self.undelivered_dates[paper_key] = []

    ## set up files and folders if they do not exist
    def define_file_structure(self) -> None:
        Path(f"{self.config['records_folder']}").mkdir(parents=True, exist_ok=True)  # records folder (and root folder, because it is parent)
        Path(f"{self.config['root_folder']}/{self.config['papers_data']}").touch(exist_ok=True)  # papers data file
        Path(f"{self.config['root_folder']}/{self.config['undelivered_strings']}").touch(exist_ok=True)  # undelivered strings file
        Path(f"{self.config['root_folder']}/{self.config['cost_record_file']}").touch(exist_ok=True)  # cost record file
        Path(f"{self.config['root_folder']}/{self.config['delivery_record_file']}").touch(exist_ok=True)  # delivery record file

    ## set up a list of all dates in month, and populate undelivered strings dictionary
    def prepare_dated_data(self) -> list:

        ## set up undelivered strings dictionary for concerned month and year
        if f"{self.month}/{self.year}" not in self.undelivered_strings:
            self.undelivered_strings[f"{self.month}/{self.year}"] = {}

        ## set up undelivered dates dictionary for each paper
        for paper_key in self.papers:
            if paper_key not in self.undelivered_strings[f"{self.month}/{self.year}"]:
                self.undelivered_strings[f"{self.month}/{self.year}"][paper_key] = []

        ## include an entry for all papers
        if "all" not in self.undelivered_strings[f"{self.month}/{self.year}"]:
            self.undelivered_strings[f"{self.month}/{self.year}"]["all"] = []

        ## set up dates list for concerned month and year
        return self.get_list_of_all_dates()

    ## create a list of all dates in concerned month and year
    def get_list_of_all_dates(self) -> list:
        ## initialize empty list of dates
        self.dates_in_active_month = []

        for date_number in range(monthrange(self.year, self.month)[1]):  # for each date in month
            date = date_type(self.year, self.month, date_number + 1)  # create date object
            self.dates_in_active_month.append(date)  # add date to list

        ## return list of dates
        return self.dates_in_active_month

    ## get the previous month
    def get_previous_month(self) -> date_type:

        ## select current day
         # set the day to the first day of the (current) month
         # subtract one day
         # set the day to the first day of the (previous) month
        return (datetime.today().replace(day=1) - timedelta(days=1)).replace(day=1)

    ## create an entry for a new newspaper
    def create_new_paper(self, paper_key: str,paper_name: str,  paper_days: dict) -> None:
        
        ## add new paper to papers dictionary
        self.papers[paper_key] = {
            'name': paper_name,  # name of newspaper
            'key': paper_key,  # key of newspaper (used for indexing)
            'days': paper_days  # days of delivery, and associated costs per day
        }

        ## save papers dictionary to file
        with open(Path(f"{self.config['root_folder']}/{self.config['papers_data']}"), 'w') as papers_file:
            papers_file.write(dumps(self.papers))

    ## edit an existing newspaper
    def edit_existing_paper(self, paper_key: str, paper_name: str, days: dict) -> None:
        
        ## check if paper exists
        if paper_key in self.papers:  # if it does

            ## update paper dictionary
            self.papers[paper_key] = {
                'name': paper_name,  # name of newspaper
                'days': days  # days of delivery, and associated costs per day
            }

            ## save papers dictionary to file
            with open(Path(f"{self.config['root_folder']}/{self.config['papers_data']}"), 'w') as papers_file:
                papers_file.write(dumps(self.papers))
        
        else:  # if it doesn't

            ## let the user know that the paper does not exist
            print(f"\n{paper_name} does not exist, please create it.")

    ## delete an existing newspaper
    def delete_existing_paper(self, paper_key: str) -> None:

        ## check if paper exists
        if paper_key in self.papers:  # if it does

            ## delete paper from papers dictionary
            del self.papers[paper_key]

            ## save papers dictionary to file
            with open(Path(f"{self.config['root_folder']}/{self.config['papers_data']}"), 'w') as papers_file:
                papers_file.write(dumps(self.papers))
        
        else: # if it doesn't

            ## let the user know that the paper does not exist
            print(f"\nPaper with key {paper_key} does not exist, please create it.")


    def parse_undelivered_string(self, string: str) -> list:
        undelivered_dates = []
        durations = string.split(',')

        for duration in durations:
            duration = f"{duration[0].upper()}{duration[1:].lower()}"
            
            if duration.isdigit():
                day = int(duration)

                if day > 0:
                    undelivered_dates.append(date_type(self.year, self.month, day))

            elif '-' in duration:
                start, end = duration.split('-')
                start = f"{start[0].upper()}{start[1:].lower()}"

                if start.isdigit() and end.isdigit():
                    start_date = int(start)
                    end_date = int(end)

                    if start_date > 0 and end_date > 0:
                        for day in range(start_date, end_date + 1):
                            undelivered_dates.append(date_type(self.year, self.month, day))

                elif (start in weekday_names) and end.isdigit():
                    print(start)
                    all_dates_with_matching_name = [i for i in self.dates_in_active_month if list(weekday_names)[i.weekday()] == start]
                    undelivered_dates.append(all_dates_with_matching_name[int(end) - 1])

            elif duration[:-1] in list(weekday_names):
                day_number = list(weekday_names).index(duration[:-1]) + 1

                for date in self.dates_in_active_month:
                    if date.weekday() == day_number:
                        undelivered_dates.append(date)

            elif duration == 'all':
                undelivered_dates = self.dates_in_active_month

        return undelivered_dates

    def undelivered_strings_to_dates(self) -> None:
        all_papers_strings = self.undelivered_strings[f"{self.month}/{self.year}"].pop('all')
        dates_of_no_paper = []

        for all_papers_string in all_papers_strings:
            dates_of_no_paper += self.parse_undelivered_string(all_papers_string)

        for date in dates_of_no_paper:
            for paper_key in self.papers:
                if date not in self.undelivered_dates[paper_key]:
                    self.undelivered_dates[paper_key].append(date)

        for paper_key in self.undelivered_strings[f"{self.month}/{self.year}"]:
            for string in self.undelivered_strings[f"{self.month}/{self.year}"][paper_key]:
                undelivered_dates = self.parse_undelivered_string(string)

                for date in undelivered_dates:
                    if date not in self.undelivered_dates[paper_key]:
                        self.undelivered_dates[paper_key].append(date)

    def calculate_one_paper(self, paper_key: str) -> float:
        self.totals[paper_key] = 0.0

        for date in self.dates_in_active_month:
            week_day_name = weekday_names[date.weekday()]

            if (date not in self.undelivered_dates[paper_key]) and (int(self.papers[paper_key]['days'][week_day_name]['sold']) != 0):
                self.totals[paper_key] += float(self.papers[paper_key]['days'][week_day_name]['cost'])

        return self.totals[paper_key]

    def calculate_all_papers(self) -> None:
        self.totals['TOTAL'] = 0.0

        for paper_key in self.papers:
            self.totals['TOTAL'] += self.calculate_one_paper(paper_key)

    def save_results(self) -> None:
        timestamp = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
        current_month = date_type(self.year, self.month, 1).strftime("%m/%Y")

        total = 0.0

        for paper_key, value in self.totals.items():
            if len(self.undelivered_dates[paper_key]) > 0:

                delivery_record = ""

                for date in self.undelivered_dates[paper_key]:
                    delivery_record += f",{date.day}"

                delivery_record = f"{timestamp},{current_month},{self.papers[paper_key]['name']}{delivery_record}"
                with open(Path(f"{self.config['root_folder']}/{self.config['delivery_record_file']}"), 'a') as delivery_record_file:
                    delivery_record_file.write(delivery_record + "\n")

            cost_record = f"{timestamp},{current_month},{self.papers[paper_key]['name']},{self.totals[paper_key]}"

            with open(Path(f"{self.config['root_folder']}/{self.config['cost_record_file']}"), 'a') as cost_record_file:
                cost_record_file.write(cost_record + "\n")

            total += self.totals[paper_key]

        with open(Path(f"{self.config['root_folder']}/{self.config['cost_record_file']}"), 'a') as cost_record_file:
            cost_record_file.write(f"{timestamp},{current_month},TOTAL,{total}\n")

    def calculate(self) -> None:
        self.undelivered_strings_to_dates()
        self.calculate_all_papers()
        self.save_results()

    def addudl(self) -> None:
        with open(Path(f"{self.config['root_folder']}/{self.config['undelivered_strings']}"), 'w') as undelivered_file:
            undelivered_file.write(dumps(self.undelivered_strings))

    def deludl(self) -> None:
        del self.undelivered_strings[f"{self.month}/{self.year}"]

        with open(Path(f"{self.config['root_folder']}/{self.config['undelivered_strings']}"), 'w') as undelivered_file:
            undelivered_file.write(dumps(self.undelivered_strings))

    def update(self) -> None:
        pass

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

    def define_and_read_args(self) -> argparse.Namespace:
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

    def format_and_copy(self) -> None:
        string = f"For {datetime(self.year, self.month, 1):%B %Y}\n\n"
        string += f"*TOTAL: {self.totals.pop('TOTAL')}*\n"

        for paper_key, value in self.totals.items():
            string += f"{self.papers[paper_key]['name']}: {value}\n"

        print(string)

        if not self.args.nocopy:
            copy_to_clipboard(string)
            print("\nSummary copied to clipboard.")

    def calculate(self) -> None:
        self.undelivered_strings_to_dates()
        self.calculate_all_papers()
        self.format_and_copy()

        if not self.args.nolog:
            self.save_results()
            print("Saved results to logs.")        

class NPBC_cli_args(NPBC_cli):
    def __init__(self):
        NPBC_cli.__init__(self)

    def check_args(self) -> None:
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

                        self.undelivered_strings[f"{self.month}/{self.year}"][paper_key].append(undelivered_string)

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

    def extract_days_and_cost(self) -> dict:
        sold = [int(i == 'Y') for i in str(self.args.days).upper()]
        prices = self.args.price.split(';')

        days = {}
        prices = [float(price) for price in prices if float(price) != 0.0]

        delivered_count = -1

        for day in range(7):
            delivered = sold[day]
            delivered_count += delivered
            
            day_name = weekday_names[day]
            days[day_name] = {}

            days[day_name]['cost'] = prices[delivered_count] if delivered else 0
            days[day_name]['sold'] = delivered

        return days

    def edit_config_files(self) -> None:
        filepaths = self.args.files.split(';')

        for filepath in filepaths:
            path_key, path = filepath.split(':')

            if path_key in self.config:
                self.config[path_key] = path

        with open(CONFIG_FILEPATH, 'w') as config_file:
            config_file.write(dumps(self.config))

    def run(self) -> None:
        if self.args.command != 'ui' and self.args.command in self.functions:
            self.check_args()
        
        else:
            exit(1)

class NPBC_cli_interactive(NPBC_cli):
    def __init__(self):
        NPBC_cli.__init__(self)
        
    def run_ui(self) -> None:
        task = input("What do you want to do right now? ([c]alculate, edit the [p]apers, edit the [f]iles configuration, [a]dd undelivered data, [r]emove undelivered data, [u]pdate, or e[x]it) ").strip().lower()

        if task in ['c', 'calculate', 'a', 'add', 'r', 'remove']:
            month = input("\nPlease enter the month you want to calculate (either enter a number, or leave blank to use the previous month): ")

            if month.isdigit():
                self.month = int(month)

            else:
                self.month = self.get_previous_month().month

            year = input("\nPlease enter the year you want to calculate (either enter a number, or leave blank to use the year of the previous month): ")

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

    def edit_papers(self) -> None:
        print ("The following papers currently exist.\n")

        for paper_key in self.papers:
            print (f"{paper_key}: {self.papers[paper_key]['name']}")
        

        mode = input("\n Do you want to create a [n]ew newspaper, [e]dit an existing one, [d]elete an existing one, or e[x]it? ").lower().strip()

        if (mode in ['n', 'ne', 'new']) or (mode in ['e', 'ed', 'edi', 'edit']) or (mode in ['d', 'de', 'del', 'dele', 'delet', 'delete']):
            paper_key = input("\nEnter the key of the paper to edit: ")

            if mode in ['n', 'ne', 'new']:
                if paper_key in self.papers:
                    print(f"{paper_key} already exists. Please try editing it.")
                    exit(1)

                paper_name = input("\nWhat is the name of the newspaper? ")

                paper_days = self.get_days_and_cost()
                self.create_new_paper(paper_key, paper_name, paper_days)
                print(f"\n{paper_name} has been added.")

            elif mode in ['e', 'ed', 'edi', 'edit']:
                if paper_key not in self.papers:
                    print(f"{paper_key} does not exist. Please try again.")
                    exit(1)

                new_paper_name = input("Enter a new name for the paper, or leave blank to retain: ")

                if not new_paper_name:
                    new_paper_name = self.papers[paper_key]['name']

                paper_days = self.get_days_and_cost()
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

    def get_days_and_cost(self) -> dict:
        paper_days = {}

        for day in weekday_names:
            sold = input(f"\nIs the newspaper sold on {day}? ([y]es/[N]o) ")

            if sold.lower() in ['y', 'ye', 'yes']:
                sold = int(True)
                cost = float(input(f"What is the cost on {day}? "))

            else:
                sold = int(False)
                cost = 0.0

            paper_days[day] = {'sold': sold, 'cost': cost}
        return paper_days

    def acquire_undelivered_papers(self) -> None:
        confirmation = input("\nDo you want to report any undelivered data? ([Y]es/[n]o) ")

        while confirmation.lower() in ['y', 'ye,' 'yes']:
            print("These are the available newspapers:\n")

            for paper_key, value in self.papers.items():
                print(f"\t{paper_key}: {value['name']}")

            print("\tall: ALL NEWSPAPERS\n")

            paper_key = input("Please enter the key of the newspaper you want to report, or press Return to cancel: ")

            if paper_key == '':
                pass

            elif (paper_key in self.papers) or (paper_key == 'all'):
                self.report_undelivered_dates(paper_key)

            else:
                print("Invalid key. Please try again.")

            confirmation = input("Do you want to report any more undelivered data? ([Y]es/[n]o) ")

    def report_undelivered_dates(self, paper_key: str) -> None:
        finished = False
        string = ""

        while not finished:
            string = input(f"Please tell us when {paper_key} was undelivered, or enter '?' for help: ").strip()

            if string == '?' or string == '':
                system(HELP_FILEPATH)

            else:
                self.undelivered_strings[f"{self.month}/{self.year}"][paper_key].append(string)

                finished = True

    def edit_config_files(self) -> None:
        print("\nThe following filepaths can be edited:")

        for key in self.config:
            print(f"{key}: {self.config[key]}")

        confirmation = input("\nDo you want to edit any of these paths? ([Y]es/[n]o) ").lower().strip()

        while confirmation in ['y', 'ye', 'yes']:

            invalid = True

            while invalid:
                path_key = input("\nPlease enter the path key to edit: ")

                if path_key in self.config:
                    self.config[path_key] = input(f"Please enter the new path for {path_key}: ")
                    invalid = False

                else:
                    print("Invalid key. Please try again.")

            confirmation = input("\nDo you want to edit any more of these paths? ([Y]es/[n]o) ").lower().strip()

        with open(CONFIG_FILEPATH, 'w') as config_file:
            config_file.write(dumps(self.config))

    def run(self) -> None:
        if self.args.command == 'ui':
            self.run_ui()

def interactive() -> None:
    calculator = NPBC_cli_interactive()
    calculator.run()
    del calculator

# @Gooey
def args() -> None:
    calculator = NPBC_cli_args()
    calculator.run()
    del calculator

def main() -> None:
    interactive()
    args()
    exit(0)

if __name__ == '__main__':
    main()
