import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np

class PlayerAnalyzer:
    def __init__(self):
        self.df = None
        self.processed_df = None
        
        # Use the role attributes from your filtering selection file
        self.role_attributes = {
            'GK': ['Wor', 'Vis', 'Thr', 'Tec', 'Tea'],
            'DEF': ['Wor', 'Vis', 'Thr'],
            'DM': ['Wor', 'Thr', 'Tec'],
            'MF': ['Vis', 'Tec', 'Tea'],
            'AM': ['Wor', 'Vis', 'Tea'],
            'ST': ['Wor', 'Thr', 'Tea']
        }
        
        # Extended role names mapping to the base roles
        self.position_mapping = {
            'Goalkeeper': 'GK',
            'Sweeper Keeper': 'GK',
            'Centre Back': 'DEF',
            'Ball Playing Defender': 'DEF',
            'Libero': 'DEF',
            'Wing Back': 'DEF',
            'Full Back': 'DEF',
            'Defensive Midfielder': 'DM',
            'Anchor Man': 'DM',
            'Half Back': 'DM',
            'Central Midfielder': 'MF',
            'Box to Box Midfielder': 'MF',
            'Deep Lying Playmaker': 'MF',
            'Roaming Playmaker': 'MF',
            'Attacking Midfielder': 'AM',
            'Advanced Playmaker': 'AM',
            'Enganche': 'AM',
            'Winger': 'AM',
            'Inside Forward': 'AM',
            'Striker': 'ST',
            'Advanced Forward': 'ST',
            'Complete Forward': 'ST',
            'Target Man': 'ST',
            'False 9': 'ST',
            'Pressing Forward': 'ST'
        }
        
        self.setup_gui()
    
    def parse_attribute_value(self, value):
        """Parse attribute values and return min, max, and estimated values"""
        if pd.isna(value) or value == '-' or value == '':
            return 0, 0, 0
        
        value_str = str(value).strip()
        
        if '-' not in value_str:
            # Single value
            try:
                val = int(value_str)
                return val, val, val
            except ValueError:
                return 0, 0, 0
        else:
            # Range value
            parts = value_str.split('-')
            try:
                min_val = int(parts[0]) if parts[0] else 0
                max_val = int(parts[1]) if len(parts) > 1 and parts[1] else 0
                est_val = (min_val + max_val) / 2
                return min_val, max_val, est_val
            except ValueError:
                return 0, 0, 0
    
    def load_file(self):
        """Load HTML file and process the data"""
        file_path = filedialog.askopenfilename(
            title="Select HTML file",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # Read HTML file
            dfs = pd.read_html(file_path)
            self.df = dfs[0]  # Assuming data is in first table
            
            # Process the data
            self.process_data()
            
            messagebox.showinfo("Success", f"Loaded {len(self.df)} players successfully!")
            
            # Enable role selection
            self.role_dropdown.config(state='normal')
            self.analyze_button.config(state='normal')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def process_data(self):
        """Process the raw data and create min/max/est columns"""
        self.processed_df = self.df.copy()
        
        # Get all attribute columns (exclude Name and status columns)
        attribute_columns = [col for col in self.df.columns 
                           if col not in ['Name', 'Inf'] and len(col) <= 3]
        
        # Process each attribute column
        for col in attribute_columns:
            if col in self.df.columns:
                # Apply parsing function
                parsed_values = self.df[col].apply(self.parse_attribute_value)
                
                # Create new columns
                self.processed_df[f'{col}_min'] = [x[0] for x in parsed_values]
                self.processed_df[f'{col}_max'] = [x[1] for x in parsed_values]
                self.processed_df[f'{col}_est'] = [x[2] for x in parsed_values]
        
        # Remove original attribute columns
        self.processed_df.drop(columns=attribute_columns, inplace=True, errors='ignore')
    
    def analyze_role(self):
        """Analyze players for selected role"""
        if self.processed_df is None:
            messagebox.showerror("Error", "Please load a file first!")
            return
        
        selected_position = self.role_var.get()
        if not selected_position:
            messagebox.showerror("Error", "Please select a position!")
            return
        
        # Map the selected position to base role
        base_role = self.position_mapping.get(selected_position, selected_position)
        
        # Get attributes for the base role
        role_attrs = self.role_attributes.get(base_role, [])
        
        if not role_attrs:
            messagebox.showerror("Error", "Invalid position selected!")
            return
        
        # Calculate scores for each player
        result_df = self.processed_df[['Name']].copy()
        
        # Add individual attribute scores and calculate sums
        sum_min = 0
        sum_max = 0
        sum_est = 0
        
        for attr in role_attrs:
            min_col = f'{attr}_min'
            max_col = f'{attr}_max'
            est_col = f'{attr}_est'
            
            if min_col in self.processed_df.columns:
                result_df[f'{attr}_min'] = self.processed_df[min_col]
                result_df[f'{attr}_max'] = self.processed_df[max_col]
                result_df[f'{attr}_est'] = self.processed_df[est_col]
                
                # Add to sums
                sum_min += self.processed_df[min_col]
                sum_max += self.processed_df[max_col]
                sum_est += self.processed_df[est_col]
        
        # Add sum columns (like in your original script)
        result_df['sum_min'] = sum_min
        result_df['sum_max'] = sum_max
        result_df['sum_est'] = sum_est
        
        # Sort by estimated sum
        result_df = result_df.sort_values('sum_est', ascending=False)
        
        # Display results
        self.display_results(result_df, selected_position)
    
    def display_results(self, dataframe, role):
        """Display analysis results in a new window"""
        # Create new window
        result_window = tk.Toplevel(self.root)
        result_window.title(f"Best {role} Players")
        result_window.geometry("1200x600")
        
        # Create treeview with scrollbars
        tree_frame = ttk.Frame(result_window)
        tree_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        tree = ttk.Treeview(tree_frame)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and treeview
        tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Configure columns
        columns = list(dataframe.columns)
        tree["columns"] = columns
        tree["show"] = "headings"
        
        # Set column headings and widths
        for col in columns:
            tree.heading(col, text=col)
            if 'Name' in col:
                tree.column(col, width=150)
            elif 'overall' in col:
                tree.column(col, width=100)
            else:
                tree.column(col, width=80)
        
        # Insert data
        for index, row in dataframe.iterrows():
            values = []
            for col in columns:
                val = row[col]
                if isinstance(val, float):
                    values.append(f"{val:.2f}")
                else:
                    values.append(str(val))
            tree.insert("", "end", values=values)
        
        # Add export button
        export_button = ttk.Button(result_window, text="Export to CSV", 
                                 command=lambda: self.export_results(dataframe, role))
        export_button.pack(pady=5)
    
    def export_results(self, dataframe, role):
        """Export results to CSV"""
        file_path = filedialog.asksavename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialname=f"{role}_analysis.csv"
        )
        
        if file_path:
            try:
                dataframe.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Results exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def setup_gui(self):
        """Setup the main GUI"""
        self.root = tk.Tk()
        self.root.title("Football Manager Player Analyzer")
        self.root.geometry("400x300")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Title
        title_label = ttk.Label(main_frame, text="Football Manager Player Analyzer", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Load file button
        load_button = ttk.Button(main_frame, text="Load HTML File", command=self.load_file)
        load_button.pack(pady=5)
        
        # Role selection
        role_frame = ttk.Frame(main_frame)
        role_frame.pack(pady=20)
        
        ttk.Label(role_frame, text="Select Position:").pack()
        
        self.role_var = tk.StringVar()
        self.role_dropdown = ttk.Combobox(role_frame, textvariable=self.role_var, 
                                         values=list(self.position_mapping.keys()),
                                         state='disabled', width=25)
        self.role_dropdown.pack(pady=5)
        
        # Analyze button
        self.analyze_button = ttk.Button(main_frame, text="Analyze Players", 
                                        command=self.analyze_role, state='disabled')
        self.analyze_button.pack(pady=10)
        
        # Instructions
        instructions = """
Instructions:
1. Click 'Load HTML File' to select your player data
2. Choose a position from the dropdown
3. Click 'Analyze Players' to see results
4. Results show players ranked by weighted attributes
5. Export results to CSV if needed
        """
        
        instruction_label = ttk.Label(main_frame, text=instructions, 
                                    justify=tk.LEFT, font=("Arial", 9))
        instruction_label.pack(pady=20)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

# Create and run the application
if __name__ == "__main__":
    app = PlayerAnalyzer()
    app.run()