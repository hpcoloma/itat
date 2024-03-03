# Write your code to expect a terminal of 80 characters wide and 24 rows high
import gspread
from google.oauth2.service_account import Credentials
from file_texts import LOGO, DESCRIPTION
import re
from rich.console import Console
from rich.table import Table

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
    ]

CREDS = Credentials.from_service_account_file('creds.json')
SCOPED_CREDS = CREDS.with_scopes(SCOPE)
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
SHEET = GSPREAD_CLIENT.open('itat')

console = Console()

def view_stock():
    """
    Display current inventory listing in a table format
    """
    index = 0
    table = Table(title='CURRENT STOCK')
    table.add_column('SKU')
    table.add_column('Added Stock')
    table.add_column('Check-out Total')
    table.add_column('Unassigned')
    table.add_column('% Available')

    viewstock = SHEET.worksheet('CIL')
    data = viewstock.get_all_values()
    for row in data[1:]:
        index += 1
        table.add_row(str(index), *row)
    
    console.print(table)


def welcome_screen():
    """
    Displays logo made from ASCII art and description of the program
    """
    console.print(LOGO, justify='center')
    console.print(DESCRIPTION, justify='center')


if __name__=="__main__":
    welcome_screen()
    view_stock()
