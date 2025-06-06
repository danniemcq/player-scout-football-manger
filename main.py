import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np

class PlayerAnalyzer:
    def __init__(self):
        self.df = None
        self.processed_df = None
        
        # Define role importance rankings (1=least important, 5=most important)
        self.role_attributes = {
            'GK': {
                'Kic': 5, 'Thr': 5, 'Pas': 4, 'Han': 5, 'Ref': 5, 'Cmd': 4, 'Com': 4,
                'Dec': 3, 'Cnt': 4, 'Pos': 4, 'Ant': 3, 'Agi': 4, 'Jum': 3
            },
            'DEF': {
                'Tck': 5, 'Mar': 5, 'Pos': 5, 'Ant': 4, 'Hea': 4, 'Str': 4, 'Jum': 4,
                'Dec': 4, 'Cnt': 4, 'Bra': 3, 'Pac': 3, 'Sta': 3, 'Pas': 3
            },
            'DM': {
                'Tck': 4, 'Pas': 5, 'Dec': 5, 'Pos': 4, 'Ant': 4, 'Wor': 4, 'Sta': 4,
                'Tea': 4, 'Cnt': 3, 'Str': 3, 'Bal': 3, 'Tec': 4
            },
            'CM': {
                'Pas': 5, 'Dec': 5, 'Vis': 4, 'Tec': 4, 'Sta': 4, 'Wor': 4, 'Tea': 4,
                'Fir': 4, 'Cnt': 3, 'Bal': 3, 'Ant': 3, 'OtB': 3
            },
            'AM': {
                'Pas': 5, 'Vis': 5, 'Tec': 5, 'Dec': 4, 'Fir': 4, 'OtB': 4, 'Fla': 4,
                'Dri': 4, 'Fin': 3, 'Lon': 3, 'Bal': 3, 'Agi': 3
            },
            'WM': {
                'Pas': 4, 'Cro': 5, 'Sta': 5, 'Wor': 5, 'Pac': 4, 'Tec': 4, 'Dec': 3,
                'Tea': 4, 'Fir': 3, 'Dri': 4, 'Bal': 3, 'Agi': 3
            },
            'ST': {
                'Fin': 5, 'Fir': 5, 'Ant': 4, 'OtB': 4, 'Pac': 4, 'Str': 4, 'Bal': 3,
                'Tec': 4, 'Dec': 3, 'Pos': 3, 'Jum': 3, 'Hea': 3, 'Dri': 3
            }
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
        
        selected_role = self.role_var.get()
        if not selected_role:
            messagebox.showerror("Error", "Please select a role!")
            return
        
        # Get attributes for selected role
        role_attrs = self.role_attributes.get(selected_role, {})
        
        if not role_attrs:
            messagebox.showerror("Error", "Invalid role selected!")
            return
        
        # Calculate weighted scores for each player
        result_df = self.processed_df[['Name']].copy()
        
        # Add individual attribute scores
        total_weight = 0
        weighted_sum_min = 0
        weighted_sum_max = 0
        weighted_sum_est = 0
        
        for attr, importance in role_attrs.items():
            min_col = f'{attr}_min'
            max_col = f'{attr}_max'
            est_col = f'{attr}_est'
            
            if min_col in self.processed_df.columns:
                result_df[f'{attr}_min'] = self.processed_df[min_col]
                result_df[f'{attr}_max'] = self.processed_df[max_col]
                result_df[f'{attr}_est'] = self.processed_df[est_col]
                result_df[f'{attr}_importance'] = importance
                
                # Calculate weighted contributions
                weighted_sum_min += self.processed_df[min_col] * importance
                weighted_sum_max += self.processed_df[max_col] * importance
                weighted_sum_est += self.processed_df[est_col] * importance
                total_weight += importance
        
        # Calculate overall scores
        if total_weight > 0:
            result_df['overall_min'] = weighted_sum_min / total_weight
            result_df['overall_max'] = weighted_sum_max / total_weight
            result_df['overall_est'] = weighted_sum_est / total_weight
        
        # Sort by estimated overall score
        result_df = result_df.sort_values('overall_est', ascending=False)
        
        # Display results
        self.display_results(result_df, selected_role)
    
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
                                         values=list(self.role_attributes.keys()),
                                         state='disabled', width=20)
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