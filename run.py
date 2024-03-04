# Write your code to expect a terminal of 80 characters wide and 24 rows high
import gspread
from google.oauth2.service_account import Credentials
from file_texts import LOGO, DESCRIPTION
import re
from rich.console import Console
from rich.table import Table
import os
from datetime import datetime
import time

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
    ]


CREDS = Credentials.from_service_account_file('creds.json')
SCOPED_CREDS = CREDS.with_scopes(SCOPE)
# Open the google sheets documents
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
SHEET = GSPREAD_CLIENT.open('itat')

console = Console()

def current_stock():
    """
    Display current inventory listing in a table format
    """
    index = 0
    table = Table(title='CURRENT STOCK')
    table.add_column('No.')
    table.add_column('SKU')
    table.add_column('Type')
    table.add_column('Added Stock')
    table.add_column('Check-out Total')
    table.add_column('[red]Unassigned')
    table.add_column('% Available')

    viewstock = SHEET.worksheet('CIL')
    data = viewstock.get_all_values()
    for row in data[1:]:
        index += 1
        table.add_row(str(index), *row)
    
    console.print(table, justify='center')

def view_stock():
    
    clear_screen()
    current_stock() 
    admin_menu()

def current_status():
    """
    Display check-out sheet with status of each assigned stocks
    """
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

def view_status():
    clear_screen()
    current_status()
    admin_menu()

class StockItem():
    """
    Create new stock items base on user input of date, type and quantity
    """
    def __init__(self, date, stock_type, quantity):
        self.date = date
        self.stock_type = stock_type
        self.quantity = quantity

    def display_info(self):
        return f"Date: {self.date}, Type: {self.stock_type}, Quantity: {self.quantity}"

# Get the sheet where the stocks will be added
sheet = SHEET.worksheet('Add Stock')

def add_stock(date, stock_type, quantity):
    """
    Function to add new stock
    """
    sheet.append_row([date, stock_type, quantity])

# Function to validate date
def validate_date(date):
    try:
        datetime.strptime(date, '%d/%m/%Y')
        return True
    except ValueError:
        return False

source_sheet = SHEET.worksheet('source')

# Get the valid stock types from the first column in the source sheet
valid_stock_types = source_sheet.col_values(1)

# Function to validate stock type
def validate_stock_type(stock_type):
    return stock_type.lower() in[stock.lower() for stock in valid_stock_types]

def add_stock_user_input():
    """
    Function to take date, type and quantity input by user
    If valid, adds new stock to the sheet 
    """
    clear_screen()
    index = 0
    table = Table(title='')
    table.add_column('No.')
    table.add_column('Type')

    # Source sheet from which to retrieve valid item types
    stock_type = SHEET.worksheet('source')
 
    # Creates a table to display all stock type from source sheet
    data = stock_type.get_all_values()
    for row in data[1:]:
        index +=1
        table.add_row(str(index), *row[:1])

    console.print("STOCK TYPE", justify='center')
    console.print(table, justify='center')
    print("ADD STOCK:")

    while True:
        date = input("Enter check-in date (DD/MM/YYY): ").strip()
        if validate_date(date):
            break
        else:
            print("Invalid date format. Please enter the date in DD/MM/YYY format.")

    while True:
        stock_type = input("Enter stock type: ").strip()
        if validate_stock_type(stock_type):
            break
        else:
            print("Invalid stock type. Please choose from the table above.")
                        
    while True:
        quantity_input = input("Enter quantity: ").strip()
        if quantity_input.isdigit():
           quantity = int(quantity_input)
           break
        else:
           print("Invalid quantity. Please enter a valid number.")

    print("""
    STOCK ITEM ADDED SUCCESSFULLY!
    """)
    add_stock(date, stock_type, quantity)
    time.sleep(5) # Pause for 5 seconds delay
    view_stock() # Displays updated stock.



def edit_stock():
    clear_screen()
    console.print("EDIT STOCK", justify='center')
    console.print("""
    U - UNASSIGN STOCK
    A - ASSIGN STOCK
    """, justify='center')

def unassign_stock():
    clear_screen()
    current_stock()
 

def assign_stock():
    clear_screen()
    current_status()







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
        add_stock_user_input()
    elif admin_menu_input == ("e"):
        edit_stock()
    elif admin_menu_input == ("b"):
        assign_stock()
    elif admin_menu_input == ("r"):
        welcome_screen()
    elif admin_menu_input == ("q"):
        clear_screen()

def clear_screen():
    """
    Clears the terminal window prior to new content.
    Recommended to me by my mentor, Matt Bodden
    """
    os.system('cls' if os.name == 'nt' else 'clear')



if __name__=="__main__":
    welcome_screen()
    
