# Write your code to expect a terminal of 80 characters wide and 24 rows high
import gspread
import time
import re
import os
import sys
import datetime

from google.oauth2.service_account import Credentials
from file_texts import LOGO, DESCRIPTION
from rich.console import Console
from rich.table import Table
from datetime import datetime, timedelta


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

# Accessing the CIL worksheet
viewstock = SHEET.worksheet('CIL')

# Accessing the Assigned worksheet
viewstatus = SHEET.worksheet('Assigned')

# Get the sheet where to pull the stock types
source_sheet = SHEET.worksheet('source')

# Get the valid stock types from the first column in the source sheet
valid_stock_types = source_sheet.col_values(1)

# Get the valid stock code from the second column in the source sheet
valid_stock_code = source_sheet.col_values(2)


def current_stock():
    """
    Display current inventory listing in a table format
    """
    console.print("[bold]CURRENT STOCK CENTER", justify='center')
    index = 0
    table = Table(title='')
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
    console.print("[bold]ASSIGNED STOCK CENTER", justify='center')
    index = 0
    table = Table(title='')
    table.add_column('No.')
    table.add_column('Check-out Date')
    table.add_column('SKU')
    table.add_column('Staff')
    table.add_column('Stock ID')
    table.add_column('Type')

    data = viewstatus.get_all_values()
    for row in data[1:]:
        index += 1
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
        return (
            f"Date: {self.date}, Type: {self.stock_type}, "
            f"Quantity: {self.quantity}, SKU: {self.sku}"
        )


def update_stock(date, stock_type, quantity, sku):
    """
    Function to append Add Stock sheet
    """
    addstock.append_row([date, stock_type, quantity, sku])


def add_stock_menu():
    clear_screen()
    app_name()
    console.print("[bold]ADD STOCK CENTER", justify='center')
    console.print("""
    [bold]N - ADD NEW STOCK TYPE   A - ADD EXISTING STOCK
    M - MENU    Q - QUIT
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
        index += 1
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
    console.print("[bold]ADD NEW STOCK TYPE")

    while True:
        new_stock_type = non_blank_input(
            "Enter Stock Type Name:  "
        ).strip().capitalize()
        if new_stock_type in valid_stock_types:
            print("Error: Stock already exist. Please enter new stock type.")
        else:
            break

    while True:
        new_stock_code = non_blank_input(
            "Assign Code (up to 3 characters):  "
        ).strip().upper()
        if len(new_stock_code) > 3:
            print("Error: Code should not exceed 3 characters.")
        elif new_stock_code in valid_stock_code:
            print("Error: Code already exist. Please enter new code.")
        else:
            break

    # Append the new stock type to the worksheet
    stock_type.append_row([new_stock_type, new_stock_code])

    # Refresh the valid_stock_types list
    valid_stock_types.append(new_stock_type)

    console.print("[bold red]NEW STOCK ADDED SUCCESSFULLY!", justify='center')

    time.sleep(2)  # Pause for 2 seconds delay

    clear_screen()
    app_name()
    all_stock_types()
    admin_menu()

    return new_stock_type


# Function to validate stock type
def validate_stock_type(stock_type):
    return stock_type.lower() in [stock.lower() for stock in valid_stock_types]


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


# Function to validate date
def validate_date(date_str):
    try:
        day, month, year = map(int, date_str.split('/'))
        # Adding leading zeros for single-digit day and month
        date_str = f"{day:02d}/{month:02d}/{year}"
        date = datetime.strptime(date_str, "%d/%m/%Y")
        if date > datetime.now():
            print("Date cannot be in the future.")
            return False
        return True
    except ValueError:
        print(
            "Invalid date format. Please enter the date in DD/MM/YYYY format."
        )
        return False


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
        date = non_blank_input("Enter check-in date (DD/MM/YYYY):  ").strip()
        if validate_date(date):
            date_obj = datetime.strptime(date, "%d/%m/%Y")
            five_years_ago = datetime.now() - timedelta(days=5*365)
            if date_obj >= five_years_ago:
                break
            else:
                print(
                    "Stock is now obsolete. "
                    "Stock life expectancy is only 5 years."
                )

    while True:
        stock_type = non_blank_input(
            "Enter stock type:  "
        ).strip().capitalize()
        if validate_stock_type(stock_type):
            break
        else:
            print("Invalid stock type. Please choose from the table above.")

    while True:
        quantity_input = non_blank_input("Enter quantity:  ").strip()
        if quantity_input.isdigit():
            quantity = int(quantity_input)
            break
        else:
            print("Invalid quantity. Please enter a valid number.")

    sku = generate_sku(stock_type, date)
    update_stock(date, stock_type, quantity, sku)
    console.print("[bold][red]UPDATING STOCK...", justify='center')

    global valid_sku
    valid_sku = viewstock.col_values(1)

    time.sleep(2)  # Pause for 2 seconds delay

    console.print(
        "[bold][red]STOCK ITEM ADDED SUCCESSFULLY!",
        justify='center')

    time.sleep(2)  # Pause for 2 seconds delay
    view_stock()  # Displays updated stock.


# Get the valid sku from the first column in the CIL sheet
valid_sku = viewstock.col_values(1)


# Function to validate the sku
def validate_sku(sku):
    return sku.lower() in [sku.lower() for sku in valid_sku]


def edit_stock():
    clear_screen()
    app_name()
    edit_stock_menu()


def edit_stock_menu():
    console.print("[bold]EDIT STOCK CENTER", justify='center')
    console.print("""
    [bold]A - ASSIGN STOCK    U - UNASSIGN STOCK    M - MENU    Q - QUIT
    """, justify='center')

    while True:
        edit_stock_input = non_blank_input(
            "Enter Command Letter: "
            ).strip().lower()
        if edit_stock_input not in ("a", "u", "m", "q"):
            print("Please enter A, U, M, Q")
        else:
            break

    if edit_stock_input == ("u"):
        unassign_stock()
    elif edit_stock_input == ("a"):
        assign_stock()
    elif edit_stock_input == ("m"):
        clear_screen()
        app_name()
        admin_menu()
    elif edit_stock_input == ("q"):
        console.print(
            "[bold red]QUITTING THE APPLICATION...",
            justify='center')
        time.sleep(4)
        clear_screen()
        sys.exit()


# Function to validate staff name
def validate_name(prompt, max_length):
    while True:
        value = non_blank_input(prompt).strip()
        if len(value) <= max_length and value.isalpha() or "'" in value:
            return value
        else:
            print("Please enter letters only and length is within",
                  max_length, "characters.")


def generate_stock_id(sku, viewstatus):
    """
    Function to generate ID based on SKU and incrementing ID
    """
    current_id = 1  # Starting ID value
    existing_ids = viewstatus.col_values(4)[1:]  # Header not included

    # Generate initial ID
    new_id = f"{sku}.{current_id}"

    # Validate if ID exists in the list if existing IDs
    while new_id in existing_ids:
        current_id += 1
        new_id = f"{sku}.{current_id}"

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
            date_obj = datetime.strptime(date, "%d/%m/%Y")
            more_than_one_year = datetime.now() - timedelta(days=365)
            if date_obj >= more_than_one_year:
                break
            else:
                print(
                    "Enter assigned stocks for the last 12 months."
                    )

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

    # Append Assigned sheet
    viewstatus.append_row([date, sku, staff_name, stock_id])

    # Update valid_id list
    global valid_id
    valid_id = viewstatus.col_values(4)

    # Update valid sku list
    global valid_sku
    valid_sku = viewstock.col_values(1)

    console.print("[bold][red]STOCK ASSIGNED SUCCESSFULLY!", justify='center')

    time.sleep(2)  # Pause for 2 seconds delay

    clear_screen()

    view_status()  # Display updated assigned dock


# Get valid stock ID from the assigned sheet
valid_id = viewstatus.col_values(4)


# Function to validate ID
def validate_id(stock_id):
    return stock_id.lower() in [stock_id.lower() for stock_id in valid_id]


def unassign_stock():
    clear_screen()
    app_name()
    current_status()

    console.print("[bold]UNASSIGN STOCK")

    while True:
        stock_id = non_blank_input(
            "\nEnter Stock ID to unassign:  "
            ).strip().upper()
        # Validate stock id entered
        if validate_id(stock_id):
            console.print("VALIDATING ...")
            time.sleep(2)

            # Clear the screen from the word "VALIDATING ..." onwards
            print("\033[J", end='', flush=True)

            # Ask to confirm
            confirmation = non_blank_input(
                f"Are you sure you want to unassign {stock_id}? (Y/N):  "
                ).strip().upper()

            if confirmation == 'Y':
                console.print(
                    "[bold][red]UNASSIGNING STOCK...\n",
                    justify='center')
                time.sleep(2)  # Pause for 2 seconds delay
                delete_assigned_stock(stock_id)
                break
            elif confirmation == 'N':
                continue
            else:
                print("Invalid input. Please enter 'Y' or 'N'.")
        else:
            print("Invalid ID. Please enter a valid ID.")


def delete_assigned_stock(stock_id):
    # Get the row index of the given ID
    data = viewstatus.get_all_values()
    stock_ids = [row[3] for row in data[1:]]

    try:
        row_index = stock_ids.index(stock_id) + 2
        viewstatus.delete_rows(row_index)
        console.print(
            f"[bold red]STOCK WITH ID {stock_id} HAS BEEN UNASSIGNED.\n",
            justify='center')
        time.sleep(2)  # Pause for 2 seconds delay
    except ValueError:
        console.print(
            f"STOCK WITH ID {stock_id} IS NOT ASSIGNED.\n", justify='center')
        time.sleep(2)  # Pause for 2 seconds delay
    clear_screen()
    app_name()
    current_status()
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
    Admin menu functions where input will be validated
    base on the letter assigned for each menu option
    """
    console.print("[bold][red]C.O.M.M.A.N.D   C.E.N.T.E.R", justify='center')
    console.print("""[bold]V - VIEW STOCK     S - VIEW STATUS     N - NEW STOCK
    E - EDIT STOCK    Q - QUIT
    """, justify='center')

    while True:
        admin_menu_input = input("Enter Command Letter:").strip().lower()
        if admin_menu_input not in ("v", "s", "q", "n", "e"):
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
    elif admin_menu_input == ("q"):
        console.print(
            "[bold red]QUITTING THE APPLICATION...", justify='center')
        time.sleep(4)
        clear_screen()
        sys.exit()


def clear_screen():
    """
    Clears the terminal window prior to new content.
    Recommended to me by my mentor, Matt Bodden
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def restart_app():
    python = sys.executable
    os.execl(python, python, *sys.argv)


def app_name():
    console.print("[bold][red]iTAT - IT.ASSET.TRACKER", justify='center')


if __name__ == "__main__":
    clear_screen()
    app_name()
    welcome_screen()