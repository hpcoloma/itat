# Write your code to expect a terminal of 80 characters wide and 24 rows high
import gspread
from google.oauth2.service_account import Credentials
from file_texts import LOGO, DESCRIPTION
import re
from rich.console import Console
from rich.table import Table
import os
from datetime import datetime

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
    clear_screen()

    index = 0
    table = Table(title='CURRENT STOCK')
    table.add_column('No.')
    table.add_column('SKU')
    table.add_column('Type')
    table.add_column('Added Stock')
    table.add_column('Check-out Total')
    table.add_column('Unassigned')
    table.add_column('% Available')

    viewstock = SHEET.worksheet('CIL')
    data = viewstock.get_all_values()
    for row in data[1:]:
        index += 1
        table.add_row(str(index), *row)
    
    console.print(table, justify='center')
    
    admin_menu()

def view_status():
    """
    Display check-out sheet with status of each assigned stocks
    """
    clear_screen()

    index = 0
    table = Table(title='ASSIGNED STOCK')
    table.add_column('No.')
    table.add_column('Check-out Date')
    table.add_column('SKU')
    table.add_column('Staff')
    table.add_column('ID')
    table.add_column('Type')
    
    viewstatus = SHEET.worksheet('Check-out')
    data = viewstatus.get_all_values()
    for row in data[1:]:
        index +=1
        table.add_row(str(index), *row[:5])
    
    console.print(table, justify='center')
    admin_menu()

class StockItem():
    """
    Create new stock items base on user input of date, type and quantity
    """
    def __init__(self, date, item_type, quantity):
        self.date = date
        self.item_type = item_type
        self.quantity = quantity

    def display_info(self):
        return f"Date: {self.date}, Type: {self.item_type}, Quantity: {self.quantity}"

def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%d/%m/%Y')
        return True
    except ValueError:
        return False

def add_stock():
    """
    Checks user input type and quantity
    if valid adds the data to the spreadsheet
    """
    clear_screen()
    index = 0
    table = Table(title='')
    table.add_column('No.')
    table.add_column('Type')
    
    stock_type = SHEET.worksheet('source')
    data = stock_type.get_all_values()
    for row in data[1:]:
        index +=1
        table.add_row(str(index), *row[:1])

    console.print(table, justify='center')

    while True:
        date_input = input("Enter date (DD/MM/YYY): ").strip()
        if not validate_date(date_input):
            print("Invalid date format. Please enter the date in DD/MM/YYY format.")
        continue

        item_type_input = input("Enter stock type: ")

    admin_menu()

def welcome_screen():
    """
    Displays logo made from ASCII art and description of the program
    """
    console.print(LOGO, justify='center')
    console.print(DESCRIPTION, justify='center')
    
    admin_menu()


def admin_menu():
    """
    Admin menu functions where input will be validated base on the letter assigned
    for each menu option
    """
    console.print("""
    [bold]
    C.O.M.M.A.N.D   C.E.N.T.E.R
        V - VIEW STOCK      A - ADD STOCK    B - BOOK REQUEST  
         S - VIEW STATUS     E - EDIT STOCK   R - REVIEW REQUEST
        Q - QUIT
    """, justify='center')

    while True:
        admin_menu_input = input("\n").strip().lower()
        if admin_menu_input not in ("v","s","q","a","e","b","r"):
            print("Invalid input. Please enter the correct letter.")
        else:
            break
    
    if admin_menu_input == ("v"):
        view_stock()
    elif admin_menu_input == ("s"):
        view_status()
    elif admin_menu_input == ("a"):
        add_stock()
    elif admin_menu_input == ("e"):
        welcome_screen()
    elif admin_menu_input == ("b"):
        welcome_screen()
    elif admin_menu_input == ("r"):
        welcome_screen()
    elif admin_menu_input == ("q"):
        clear_screen()

def clear_screen():
    """
    Clears the terminal window peior to new content.
    Recommended to me by my mentor, Matt Bodden
    """
    os.system('cls' if os.name == 'nt' else 'clear')



if __name__=="__main__":
    welcome_screen()
    #view_stock()
    #view_status()
