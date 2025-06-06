import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

# Initialize Tkinter root window
root = tk.Tk()
root.withdraw()  # Hide the root window

# Show an "Open" dialog box and return the path to the selected file
file_path = filedialog.askopenfilename()

# Read the HTML file
# file_path = r"C:\Projects\Python\fm\first data.html"

# Read HTML file
dfs = pd.read_html(file_path)

# Assuming the data is in the first table
df = dfs[0]

# List of fields to process for each role
fields_dict = {
    'GK': ['Wor', 'Vis', 'Thr', 'Tec', 'Tea'],
    'DEF': ['Wor', 'Vis', 'Thr'],
    'DM': ['Wor', 'Thr', 'Tec'],
    'MF': ['Vis', 'Tec', 'Tea'],
    'AM': ['Wor', 'Vis', 'Tea'],
    'ST': ['Wor', 'Thr', 'Tea']
}

# Function to split the values into low and high
def split_values(value):
    if value == '-':
        return 0, 0
    elif '-' not in value:
        num = int(value)
        return num, num
    parts = value.split('-')
    low = int(parts[0]) if parts[0] else 0
    high = int(parts[1]) if len(parts) > 1 and parts[1] else 0
    return low, high

# Function to process the selected role
def process_role():
    selected_role = role_var.get()
    if selected_role not in fields_dict:
        print("Please select a valid role.")
        return
    
    # Get the fields for the selected role
    fields = fields_dict[selected_role]
    
    # Create a new dataframe with only the relevant columns
    new_df = df[['Name'] + fields].copy()

    # Apply the low and high logic
    for field in fields:
        new_df[f'{field}_low'], new_df[f'{field}_high'] = zip(*new_df[field].apply(split_values))
    
    # Drop the original columns
    new_df.drop(columns=fields, inplace=True)
    
    # Calculate the sum of all low and high columns
    new_df['sum_low'] = new_df[[f'{field}_low' for field in fields]].sum(axis=1)
    new_df['sum_high'] = new_df[[f'{field}_high' for field in fields]].sum(axis=1)

    # Display the resulting dataframe
    display_dataframe(new_df)

    output_file_path = r'C:\Projects\Python\fm\first data.csv'
    df.to_csv(output_file_path, index=False)

# Function to display the dataframe in a new window
def display_dataframe(dataframe):
    window = tk.Toplevel(root)
    window.title("Processed Data")

    # Create a treeview to display the dataframe
    tree = ttk.Treeview(window)
    tree.pack(expand=True, fill=tk.BOTH)

    # Define the columns
    tree["columns"] = list(dataframe.columns)
    tree["show"] = "headings"

    # Define the column headings
    for col in tree["columns"]:
        tree.heading(col, text=col)

    # Insert the data
    for index, row in dataframe.iterrows():
        tree.insert("", "end", values=list(row))

# Set up the Tkinter GUI
root = tk.Tk()
root.title("Role Selector")

# Create a label
label = tk.Label(root, text="Select a role:")
label.pack(pady=10)

# Create a dropdown menu
role_var = tk.StringVar()
role_dropdown = ttk.Combobox(root, textvariable=role_var, values=list(fields_dict.keys()))
role_dropdown.pack(pady=10)

# Create a button to process the selected role
process_button = tk.Button(root, text="Process", command=process_role)
process_button.pack(pady=10)

# Run the Tkinter event loop
root.mainloop()