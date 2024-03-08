# Write your code to expect a terminal of 80 characters wide and 24 rows high
import gspread
import time
import re
import os

from google.oauth2.service_account import Credentials
from file_texts import LOGO, DESCRIPTION
from rich.console import Console
from rich.table import Table
from datetime import datetime


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

# Accessing Add Stock worksheet where new stock will be added
addstock = SHEET.worksheet('Add Stock')

#Accessing the CIL worksheet
viewstock = SHEET.worksheet('CIL')

# Accessing the Assigned worksheet
viewstatus = SHEET.worksheet('Assigned')


def current_stock():
    """
    Display current inventory listing in a table format
    """
    index = 0
    table = Table(title='[bold]CURRENT STOCK')
    table.add_column('No.')
    table.add_column('SKU')
    table.add_column('Type')
    table.add_column('Added Stock')
    table.add_column('Assigned')
    table.add_column('[red]Unassigned')
    table.add_column('% Available')
    
    data = viewstock.get_all_values()
    for row in data[1:]:
        index += 1
        # To capitalize the text under the Type column
        row[1] = row[1].capitalize()
        # To convert SKU column to uppercase
        row[0] = row[0].upper()
        table.add_row(str(index), *row)
    
    console.print(table, justify='center')


def view_stock():
    clear_screen()
    app_name()
    current_stock() 
    admin_menu()


def current_status():
    """
    Display check-out sheet with status of each assigned stocks
    """
    index = 0
    table = Table(title='[bold]ASSIGNED STOCK')
    table.add_column('No.')
    table.add_column('Check-out Date')
    table.add_column('SKU')
    table.add_column('Staff')
    table.add_column('ID')
    table.add_column('Type')
    
    data = viewstatus.get_all_values()
    for row in data[1:]:
        index +=1
        # To convert SKU column to uppercase
        row[1] = row[1].upper()
        table.add_row(str(index), *row[:5])
    
    console.print(table, justify='center')


def view_status():
    clear_screen()
    app_name()
    current_status()
    admin_menu()


class StockItem():
    """
    Create new stock items base on user input of date, type and quantity
    """
    def __init__(self, date, stock_type, quantity, sku):
        self.date = date
        self.stock_type = stock_type
        self.quantity = quantity
        self.sku = sku

    def display_info(self):
        return f"Date: {self.date}, Type: {self.stock_type}, Quantity: {self.quantity}, SKU: {self.sku}"


def update_stock(date, stock_type, quantity, sku):
    """
    Function to append Add Stock sheet
    """
    addstock.append_row([date, stock_type, quantity, sku])


# Function to validate date
def validate_date(date):
    try:
        datetime.strptime(date, '%d/%m/%Y')
        return True
    except ValueError:
        return False


# Get the sheet where to pull the stock types 
source_sheet = SHEET.worksheet('source')


# Get the valid stock types from the first column in the source sheet
valid_stock_types = source_sheet.col_values(1)


# Get the valid stock code from the second column in the source sheet
valid_stock_code = source_sheet.col_values(2)


def add_stock_menu():
    clear_screen()
    app_name()
    console.print("[bold]ADD STOCK CENTER", justify='center')
    console.print("""
    [bold]N - ADD NEW STOCK TYPE   A - ADD EXISTING STOCK    M - MENU    Q - QUIT   
    """, justify='center')

    while True:
        add_stock_menu_input = input("Enter Command Letter: ").strip().lower()
        if add_stock_menu_input not in ("n", "a", "m", "q"):
            print("Please enter N, A, M, Q")
        else:
            break   
       
    if add_stock_menu_input == ("n"):
        add_new_stock()
    elif add_stock_menu_input == ("a"):
        add_stock_user_input()
    elif add_stock_menu_input == ("q"):
        clear_screen()
    else:
        clear_screen()
        app_name()
        admin_menu()


def non_blank_input(prompt):
    """
    Fucntion to not allow user to enter blank input
    """
    while True:
        user_input = input(prompt).strip()
        if user_input:
            return user_input
        else:
            print("Error: Input cannot be blank. Please try again.")


def all_stock_types():
    """
    Function to display source sheet
    """
    # To access global varaibles
    global stock_type

    index = 0
    table = Table(title='[bold]STOCK TYPE')
    table.add_column('No.')
    table.add_column('Type')
    table.add_column('Code')

    # Source sheet from which to retrieve valid item types
    stock_type = SHEET.worksheet('source')
 
    # Creates a table to display all stock type from source sheet
    data = stock_type.get_all_values()
    for row in data[1:]:
        index +=1
        table.add_row(str(index), *row[:2])

    console.print(table, justify='center')


def add_new_stock():
    """
    Function to add new stock item in the database
    """
    clear_screen()
    app_name()
    all_stock_types()

    # Input new stock type and code
    console.print("[bold]ADD NEW STOCK")

    while True:
        new_stock_type = non_blank_input("Enter Stock Type:  ").strip().capitalize()
        if new_stock_type in valid_stock_types:
            print("Error: Stock already exist. Please enter new stock type.")
        else:
            break
    
    while True:
        new_stock_code = non_blank_input("Enter Code:  ").strip().upper()
        if new_stock_code in valid_stock_code:
            print("Error: Code already exist. Please enter new code.")
        else:
            break
    
    stock_type.append_row([new_stock_type, new_stock_code])
    console.print("[bold]NEW STOCK ADDED SUCCESSFULLY!", justify='center')
    
    clear_screen()
    app_name()
    all_stock_types()
    admin_menu()


# Function to validate stock type
def validate_stock_type(stock_type):
    return stock_type.lower() in[stock.lower() for stock in valid_stock_types]


def generate_sku(stock_type, date):
    """
    Fucntion to generate SKU based on stock type and date input
    """
    # Get the corresponding value type in column 1 of the source sheet
    stock_types_column = source_sheet.col_values(1)
    index = stock_types_column.index(stock_type) + 1

    # get corresponding value in column 2
    sku = source_sheet.cell(index, 2).value

    # Add the year in YYYY format to the SKU
    day, month, year = date.split("/")
    new_sku = sku + year

    return new_sku


def add_stock_user_input():
    """
    Function to take date, type and quantity input by user
    If valid, adds new stock to the sheet 
    """
    clear_screen()
    app_name()
    all_stock_types()    
    console.print("[bold]ADD STOCK:")

    while True:
        date = non_blank_input("Enter check-in date (DD/MM/YYYY): ").strip()
        if validate_date(date):
            break
        else:
            print("Invalid date format. Please enter the date in DD/MM/YYYY format.")

    while True:
        stock_type = non_blank_input("Enter stock type: ").strip().capitalize()
        if validate_stock_type(stock_type):
            break
        else:
            print("Invalid stock type. Please choose from the table above.")
                        
    while True:
        quantity_input = non_blank_input("Enter quantity: ").strip()
        if quantity_input.isdigit():
           quantity = int(quantity_input)
           break
        else:
           print("Invalid quantity. Please enter a valid number.")
    
    sku = generate_sku(stock_type, date)
    update_stock(date, stock_type, quantity, sku)
    console.print("[bold][red]UPDATING STOCK...", justify='center')

    time.sleep(2) # Pause for 2 seconds delay

    console.print("[bold][red]STOCK ITEM ADDED SUCCESSFULLY!", justify='center')
    
    time.sleep(2) # Pause for 2 seconds delay
    view_stock() # Displays updated stock.


# Get the valid sku from the first column in the CIL sheet
valid_sku = viewstock.col_values(1)


# Function to validate the sku
def validate_sku(sku):
    return sku.lower() in[sku.lower() for sku in valid_sku]


def edit_stock():
    clear_screen()
    app_name()
    edit_stock_menu()


def edit_stock_menu():
    console.print("[bold]EDIT STOCK", justify='center')
    console.print("""
    [bold]A - ASSIGN STOCK    U - UNASSIGN STOCK    M - MENU    Q - QUIT   
    """, justify='center')

    while True:
        edit_stock_input = non_blank_input("Enter Command Letter: ").strip().lower()
        if edit_stock_input not in ("a", "u", "m", "q"):
            print("Please enter A, U, M, Q")
        else:
            break   
       
    if edit_stock_input == ("u"):
        unassign_stock()
    elif edit_stock_input == ("a"):
        assign_stock()
    elif edit_stock_input == ("q"):
        clear_screen()
    else:
        clear_screen()
        app_name()
        admin_menu()


# Function to validate staff name
def validate_name(prompt, max_length):
    while True:
        value = non_blank_input(prompt).strip()
        if len(value) <= max_length and value.isalpha() or "'" in value:
            return value
        else:
            print("Please enter letters only and length is within", max_length, "characters.")


def generate_stock_id(sku, viewstatus):
    """
    Function to generate ID based on SKU and incrementing ID
    """
    current_id=001 #Starting ID value
    existing_ids = viewstatus.col_values(4)[1:] # Header not included

    # Generate initial ID
    new_id = f"{sku}{current_id}"

    # Validate if ID exists in the list if existing IDs
    while new_id in existing_ids:
        current_id += 1
        new_id = f"{sku}{current_id}"
    
    return new_id

def assign_stock():
    clear_screen()
    app_name()
    current_stock()

    max_length = 10

    console.print("[bold]ASSIGN STOCK")
   
    while True:
        date = non_blank_input("Enter Date (DD/MM/YYYY): ").strip()
        if validate_date(date):
            break
        else:
            print("Invalid date format. Please enter the date in DD/MM/YYYY format.")
    
    while True:
        sku = non_blank_input("Enter SKU: ").strip().upper()
        if validate_sku(sku):
            break
        else:
            print("Invalid SKU. Please choose from the table above.")  
    
    # Generate Stock ID
    stock_id = generate_stock_id(sku, viewstatus)

    # Get staff first name
    fname = validate_name("Enter Staff First Name: ", max_length).capitalize()
    lname = validate_name("Enter Staff Last Name: ", max_length).capitalize()  
    staff_name = f"{fname} {lname}"
    
    #Append Assigned sheet
    viewstatus.append_row([date, sku, staff_name, stock_id])
    
    console.print("[bold][red]STOCK ASSIGNED SUCCESSFULLY!", justify='center')

    time.sleep(2) # Pause for 2 seconds delay

    clear_screen()

    view_status() #Display updated assigned dock


#Get valid stock ID from the assigned sheet
valid_id = viewstatus.col_values(4)

#Function to validate ID
def validate_id(stock_id):
    return stock_id.lower() in [stock_id.lower() for stock_id in valid_id]


def unassign_stock():
    clear_screen()
    app_name()
    current_status()
    
    while True:
        stock_id = non_blank_input("\nEnter the stock ID you want to unassign: ").strip()

        #Validate stock id entered   
        if validate_id(stock_id):
            break
        else:
            print("Invalid ID. Please enter a valid ID.")

def delete_assigned_stock(stock_id):
    # Get the row index of the given ID
    data = viewstatus.get_all_values()
    stock_ids =  [row[3] for row in data[1:]]
    try:
        row_index = stock_ids.index(stock_id) + 2
        
        print(row_index)
    except ValueError:
        print(f"Stock with ID {stock_id} is not assigned.")
        return
    
    
    clear_screen()



    # Delete the first three rows of the Assigned sheet base on the given ID
    #viewstatus.delete_rows(2,3)

    #print(f"Stock ID: {stock_id} has been successfully unassigned.")   

    
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
    console.print("[bold][red]C.O.M.M.A.N.D   C.E.N.T.E.R", justify='center')
    console.print("""[bold]V - VIEW STOCK     S - VIEW STATUS     N - NEW STOCK       E - EDIT STOCK      
    B - BOOK REQUEST       R - REVIEW REQUEST      Q - QUIT
    """, justify='center')

    while True:
        admin_menu_input = input("Enter Command Letter:").strip().lower()
        if admin_menu_input not in ("v","s","q","n","e","b","r"):
            print("Invalid input. Please enter the correct letter.")
        else:
            break
    
    if admin_menu_input == ("v"):
        view_stock()
    elif admin_menu_input == ("s"):
        view_status()
    elif admin_menu_input == ("n"):
        add_stock_menu()
    elif admin_menu_input == ("e"):
        edit_stock()
    elif admin_menu_input == ("b"):
        assign_stock() # CHANGE TO BOOK REQUEST
    elif admin_menu_input == ("r"):
        welcome_screen() # CHANGE TO REVIEW REQUEST
    elif admin_menu_input == ("q"):
        clear_screen()


def clear_screen():
    """
    Clears the terminal window prior to new content.
    Recommended to me by my mentor, Matt Bodden
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def app_name():
    console.print("[bold][red]iTAT - IT.ASSET.TRACKER", justify='center')


if __name__=="__main__":
    clear_screen()
    app_name()
    welcome_screen()
    
