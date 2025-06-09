import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.style as style

# Import the roles data and attribute mapping from your separate files
try:
    from roles_data import roles_data
    from attribute_mapping import attribute_mapping
except ImportError as e:
    messagebox.showerror("Error", f"Could not import required files: {e}\nPlease ensure roles_data.py and attribute_mapping.py are in the same directory.")
    roles_data = {}
    attribute_mapping = {}

class PlayerAnalyzer:
    def __init__(self):
        self.df = None
        self.processed_df = None
        self.current_results = None
        self.current_role = None
        self.selected_player = None
        
        # Initialize matplotlib components as None first
        self.fig = None
        self.ax = None
        self.canvas = None
        
        # Use the imported roles_data and attribute mapping
        self.roles_data = roles_data
        self.attribute_mapping = attribute_mapping
        
        # Create reverse mapping (full name to abbreviation)
        self.reverse_mapping = {v: k for k, v in attribute_mapping.items()}
        
        self.setup_gui()
    
    def parse_attribute_value(self, value):
        """Parse attribute values and return abs (single value) and est (midpoint) values"""
        try:
            if pd.isna(value) or value == '-' or value == '' or value is None:
                return 0, 0  # abs, est
            
            value_str = str(value).strip()
            
            # Handle empty string after stripping
            if not value_str or value_str == '-':
                return 0, 0
            
            if '-' not in value_str:
                # Single value - use for both abs and est
                try:
                    val = int(value_str)
                    return val, val  # abs, est (same for single values)
                except ValueError:
                    return 0, 0
            else:
                # Range value - abs=0 (no absolute value), est=midpoint
                parts = value_str.split('-')
                
                # Ensure we have at least 2 parts for a range
                if len(parts) < 2:
                    return 0, 0
                
                try:
                    min_val = int(parts[0]) if parts[0].strip() else 0
                    max_val = int(parts[1]) if parts[1].strip() else 0
                    est_val = (min_val + max_val) / 2
                    return 0, est_val  # abs=0 for ranges, est=midpoint
                except (ValueError, IndexError):
                    return 0, 0
                    
        except Exception as e:
            print(f"Error parsing value '{value}': {e}")
            return 0, 0
    
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
            
            # Update status
            self.status_label.config(text=f"Loaded {len(self.df)} players successfully!")
            
            # Enable role selection and analysis
            self.role_dropdown.config(state='normal')
            self.analyze_button.config(state='normal')
            self.export_button.config(state='normal')
            
            # Clear any existing results
            self.clear_results()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def process_data(self):
        """Process the raw data and create abs/est columns"""
        # Start with a copy of the original data
        self.processed_df = self.df[['Name']].copy()
        
        # Get all attribute columns (exclude Name and status columns)
        attribute_columns = [col for col in self.df.columns 
                           if col not in ['Name', 'Inf'] and len(col) <= 3]
        
        # Collect all new columns to add at once
        new_columns = {}
        
        # Process each attribute column
        for col in attribute_columns:
            if col in self.df.columns:
                # Apply parsing function
                parsed_values = self.df[col].apply(self.parse_attribute_value)
                
                # Add to new columns dictionary
                new_columns[f'{col}_abs'] = [x[0] for x in parsed_values]
                new_columns[f'{col}_est'] = [x[1] for x in parsed_values]
        
        # Add all new columns at once using pd.concat for better performance
        if new_columns:
            additional_df = pd.DataFrame(new_columns, index=self.processed_df.index)
            self.processed_df = pd.concat([self.processed_df, additional_df], axis=1)
        
        # Add any remaining non-attribute columns that might be useful
        other_columns = [col for col in self.df.columns 
                        if col not in ['Name'] + attribute_columns]
        if other_columns:
            other_df = pd.DataFrame({col: self.df[col] for col in other_columns}, 
                                  index=self.processed_df.index)
            self.processed_df = pd.concat([self.processed_df, other_df], axis=1)
    
    def analyze_role(self):
        """Analyze players for selected role"""
        if self.processed_df is None:
            messagebox.showerror("Error", "Please load a file first!")
            return
        
        selected_role = self.role_var.get()
        if not selected_role:
            messagebox.showerror("Error", "Please select a role!")
            return
        
        # Get role data
        role_data = self.roles_data.get(selected_role, {})
        
        if not role_data:
            messagebox.showerror("Error", "Invalid role selected!")
            return
        
        # Flatten all attributes with their importance ratings
        all_attributes = {}
        for category, attributes in role_data.items():
            all_attributes.update(attributes)
        
        # Start with just the Name column
        result_df = self.processed_df[['Name']].copy()
        
        # Initialize importance group sums and absolute counters
        importance_5_sum = np.zeros(len(self.processed_df))
        importance_3_sum = np.zeros(len(self.processed_df))
        importance_1_sum = np.zeros(len(self.processed_df))
        
        # Count absolutes in each importance group for each player
        importance_5_absolutes = np.zeros(len(self.processed_df))
        importance_3_absolutes = np.zeros(len(self.processed_df))
        importance_1_absolutes = np.zeros(len(self.processed_df))
        
        # Count total attributes in each importance group
        importance_5_count = 0
        importance_3_count = 0
        importance_1_count = 0
        
        # Collect all attribute columns to add at once
        attribute_columns = {}
        
        # Process each attribute and collect data
        for full_attr_name, importance in all_attributes.items():
            # Convert full name to abbreviation for column lookup
            attr_abbrev = self.reverse_mapping.get(full_attr_name, full_attr_name)
            
            abs_col = f'{attr_abbrev}_abs'
            est_col = f'{attr_abbrev}_est'
            
            if abs_col in self.processed_df.columns:
                abs_values = self.processed_df[abs_col].values
                est_values = self.processed_df[est_col].values
                
                # Use absolute value if available (non-zero), otherwise use estimated
                best_values = np.where(abs_values > 0, abs_values, est_values)
                
                # Track which values are absolutes (non-zero abs values)
                is_absolute = (abs_values > 0).astype(int)
                
                # Collect attribute columns
                attribute_columns[f'{attr_abbrev}_abs'] = self.processed_df[abs_col]
                attribute_columns[f'{attr_abbrev}_est'] = self.processed_df[est_col]
                attribute_columns[f'{attr_abbrev}_best'] = best_values
                attribute_columns[f'{attr_abbrev}_importance'] = importance
                
                # Add to appropriate importance group
                if importance == 5:
                    importance_5_sum += best_values
                    importance_5_absolutes += is_absolute
                    importance_5_count += 1
                elif importance == 3:
                    importance_3_sum += best_values
                    importance_3_absolutes += is_absolute
                    importance_3_count += 1
                elif importance == 1:
                    importance_1_sum += best_values
                    importance_1_absolutes += is_absolute
                    importance_1_count += 1
            else:
                # Debug: print missing attributes
                print(f"Warning: Attribute '{attr_abbrev}' (from '{full_attr_name}') not found in data")
        
        # Calculate importance group totals and percentages
        attribute_columns['importance_5_total'] = importance_5_sum
        attribute_columns['importance_3_total'] = importance_3_sum
        attribute_columns['importance_1_total'] = importance_1_sum
        
        # Calculate absolute percentages (avoid division by zero)
        attribute_columns['importance_5_abs_pct'] = (importance_5_absolutes / max(importance_5_count, 1)) * 100
        attribute_columns['importance_3_abs_pct'] = (importance_3_absolutes / max(importance_3_count, 1)) * 100
        attribute_columns['importance_1_abs_pct'] = (importance_1_absolutes / max(importance_1_count, 1)) * 100
        
        # Calculate averages (avoid division by zero)
        attribute_columns['importance_5_avg'] = importance_5_sum / max(importance_5_count, 1)
        attribute_columns['importance_3_avg'] = importance_3_sum / max(importance_3_count, 1)
        attribute_columns['importance_1_avg'] = importance_1_sum / max(importance_1_count, 1)
        
        # Calculate overall rating (weighted sum of group averages)
        overall_rating = (attribute_columns['importance_5_avg'] * 5 + 
                         attribute_columns['importance_3_avg'] * 3 + 
                         attribute_columns['importance_1_avg'] * 1) / 9  # 5+3+1=9
        attribute_columns['overall_rating'] = overall_rating
        
        # Add all columns at once using pd.concat for better performance
        if attribute_columns:
            additional_df = pd.DataFrame(attribute_columns, index=result_df.index)
            result_df = pd.concat([result_df, additional_df], axis=1)
        
        # Sort by overall rating
        result_df = result_df.sort_values('overall_rating', ascending=False)
        
        # Store results and display
        self.current_results = result_df
        self.current_role = selected_role
        self.display_results(result_df, selected_role)
    
    def display_results(self, dataframe, role):
        """Display analysis results in the main window"""
        # Clear existing results
        self.clear_results()
        
        # Update the results label
        self.results_label.config(text=f"Best {role} Players ({len(dataframe)} total)")
        
        # Configure columns - show totals with their absolute percentages
        important_columns = ['Name', 'overall_rating', 
                           'importance_5_total', 'importance_5_abs_pct',
                           'importance_3_total', 'importance_3_abs_pct', 
                           'importance_1_total', 'importance_1_abs_pct']
        
        # Add key attributes for the role (first 5-6 most important)
        role_data = self.roles_data.get(role, {})
        all_attributes = {}
        for category, attributes in role_data.items():
            all_attributes.update(attributes)
        
        # Sort attributes by importance and take top 6
        sorted_attrs = sorted(all_attributes.items(), key=lambda x: x[1], reverse=True)[:6]
        for full_attr_name, importance in sorted_attrs:
            attr_abbrev = self.reverse_mapping.get(full_attr_name, full_attr_name)
            important_columns.extend([f'{attr_abbrev}_best', f'{attr_abbrev}_importance'])
        
        # Filter dataframe to show only important columns
        display_df = dataframe[important_columns].copy()
        
        # Configure treeview columns
        self.tree["columns"] = list(display_df.columns)
        self.tree["show"] = "headings"
        
        # Set column headings and widths
        for col in display_df.columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            if 'Name' in col:
                self.tree.column(col, width=150, anchor='w')
            elif 'overall_rating' in col:
                self.tree.column(col, width=120, anchor='center')
            elif 'importance_' in col and 'total' in col:
                self.tree.column(col, width=100, anchor='center')
            elif 'abs_pct' in col:
                self.tree.column(col, width=80, anchor='center')
            elif 'importance' in col:
                self.tree.column(col, width=80, anchor='center')
            else:
                self.tree.column(col, width=80, anchor='center')
        
        # Insert data
        for index, row in display_df.iterrows():
            values = []
            for col in display_df.columns:
                val = row[col]
                if isinstance(val, float):
                    if 'abs_pct' in col:
                        values.append(f"{val:.0f}%")  # Format percentages
                    else:
                        values.append(f"{val:.1f}")
                else:
                    values.append(str(val))
            self.tree.insert("", "end", values=values)
    
    def sort_by_column(self, column):
        """Sort the treeview by the selected column"""
        if self.current_results is None:
            return
        
        # Toggle sort order
        if not hasattr(self, 'sort_order'):
            self.sort_order = {}
        
        ascending = self.sort_order.get(column, True)
        self.sort_order[column] = not ascending
        
        # Sort the dataframe
        sorted_df = self.current_results.sort_values(column, ascending=ascending)
        
        # Update display
        selected_role = self.role_var.get()
        self.current_results = sorted_df
        self.display_results(sorted_df, selected_role)
    
    def on_player_select(self, event):
        """Handle player selection in the treeview"""
        selection = self.tree.selection()
        if selection and self.current_results is not None:
            item = self.tree.item(selection[0])
            player_name = item['values'][0]  # First column is Name
            self.selected_player = player_name
            self.update_player_graph()
    
    def clear_results(self):
        """Clear the results display"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results_label.config(text="No analysis results")
        self.selected_player = None
        if self.ax is not None and self.canvas is not None:
            self.clear_graph()
    
    def clear_graph(self):
        """Clear the graph"""
        if self.ax is not None and self.canvas is not None:
            self.ax.clear()
            self.ax.text(0.5, 0.5, 'Select a player to view attributes', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=12, style='italic')
            self.canvas.draw()
    
    def on_player_select(self, event):
        """Handle player selection in the treeview"""
        selection = self.tree.selection()
        if selection and self.current_results is not None:
            item = self.tree.item(selection[0])
            player_name = item['values'][0]  # First column is Name
            self.selected_player = player_name
            self.update_player_graph()
    
    def update_player_graph(self):
        """Update the graph for the selected player"""
        if (not self.selected_player or self.current_results is None or 
            not self.current_role or self.ax is None or self.canvas is None):
            self.clear_graph()
            return
        
        # Find the player's data
        player_data = self.current_results[self.current_results['Name'] == self.selected_player]
        if player_data.empty:
            self.clear_graph()
            return
        
        player_row = player_data.iloc[0]
        
        # Get role attributes
        role_data = self.roles_data.get(self.current_role, {})
        all_attributes = {}
        for category, attributes in role_data.items():
            all_attributes.update(attributes)
        
        # Collect attribute data for the graph
        attributes = []
        values = []
        importance_colors = []
        
        for full_attr_name, importance in all_attributes.items():
            attr_abbrev = self.reverse_mapping.get(full_attr_name, full_attr_name)
            best_col = f'{attr_abbrev}_best'
            
            if best_col in player_row:
                attributes.append(attr_abbrev)
                values.append(player_row[best_col])
                
                # Color based on importance
                if importance == 5:
                    importance_colors.append('#d32f2f')  # Red for critical
                elif importance == 3:
                    importance_colors.append('#f57c00')  # Orange for moderate
                else:
                    importance_colors.append('#388e3c')  # Green for minor
        
        # Create the graph
        self.plot_player_attributes(attributes, values, importance_colors)
    
    def plot_player_attributes(self, attributes, values, colors):
        """Create a bar chart of player attributes"""
        if self.ax is None or self.canvas is None:
            return
            
        self.ax.clear()
        
        if not attributes:
            self.ax.text(0.5, 0.5, 'No data to display', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=12)
            self.canvas.draw()
            return
        
        # Create bar chart
        bars = self.ax.bar(range(len(attributes)), values, color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
        
        # Customize the plot
        self.ax.set_xlabel('Attributes', fontweight='bold')
        self.ax.set_ylabel('Values', fontweight='bold')
        self.ax.set_title(f'{self.selected_player} - {self.current_role}', fontweight='bold', fontsize=12)
        self.ax.set_xticks(range(len(attributes)))
        self.ax.set_xticklabels(attributes, rotation=45, ha='right')
        self.ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{value:.1f}', ha='center', va='bottom', fontsize=8)
        
        # Add legend
        legend_elements = [
            plt.Rectangle((0,0),1,1, facecolor='#d32f2f', alpha=0.7, label='Critical (5)'),
            plt.Rectangle((0,0),1,1, facecolor='#f57c00', alpha=0.7, label='Moderate (3)'),
            plt.Rectangle((0,0),1,1, facecolor='#388e3c', alpha=0.7, label='Minor (1)')
        ]
        self.ax.legend(handles=legend_elements, loc='upper right', fontsize=8)
        
        plt.tight_layout()
        self.canvas.draw()
    
    def export_results(self):
        """Export current results to CSV"""
        if self.current_results is None:
            messagebox.showerror("Error", "No results to export!")
            return
        
        selected_role = self.role_var.get()
        file_path = filedialog.asksavename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialname=f"{selected_role.replace(' ', '_')}_analysis.csv"
        )
        
        if file_path:
            try:
                self.current_results.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Results exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def setup_gui(self):
        """Setup the main GUI with sidebar layout"""
        self.root = tk.Tk()
        self.root.title("Football Manager Player Analyzer")
        self.root.geometry("1600x900")
        self.root.minsize(1400, 700)
        
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create sidebar (left panel)
        sidebar = ttk.LabelFrame(main_container, text="Filters & Controls", padding="10")
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        sidebar.config(width=300)
        
        # Create main content area with two sections
        content_area = ttk.Frame(main_container)
        content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create top section for results table
        table_section = ttk.Frame(content_area)
        table_section.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Create bottom section for player graph
        graph_section = ttk.LabelFrame(content_area, text="Player Attributes", padding="5")
        graph_section.pack(fill=tk.X, pady=(5, 0))
        graph_section.config(height=300)
        
        # === SIDEBAR CONTENT ===
        
        # Title
        title_label = ttk.Label(sidebar, text="FM Player Analyzer", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # File loading section
        file_frame = ttk.LabelFrame(sidebar, text="Data Source", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        load_button = ttk.Button(file_frame, text="Load HTML File", command=self.load_file)
        load_button.pack(fill=tk.X)
        
        self.status_label = ttk.Label(file_frame, text="No file loaded", 
                                     foreground="gray", wraplength=250)
        self.status_label.pack(pady=(5, 0))
        
        # Role selection section
        role_frame = ttk.LabelFrame(sidebar, text="Position Analysis", padding="10")
        role_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(role_frame, text="Select Position:").pack(anchor='w')
        
        self.role_var = tk.StringVar()
        self.role_dropdown = ttk.Combobox(role_frame, textvariable=self.role_var, 
                                         values=list(self.roles_data.keys()),
                                         state='disabled', width=35)
        self.role_dropdown.pack(fill=tk.X, pady=(5, 10))
        
        self.analyze_button = ttk.Button(role_frame, text="Analyze Players", 
                                        command=self.analyze_role, state='disabled')
        self.analyze_button.pack(fill=tk.X)
        
        # Export section
        export_frame = ttk.LabelFrame(sidebar, text="Export", padding="10")
        export_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.export_button = ttk.Button(export_frame, text="Export to CSV", 
                                       command=self.export_results, state='disabled')
        self.export_button.pack(fill=tk.X)
        
        # Instructions
        instructions_frame = ttk.LabelFrame(sidebar, text="Instructions", padding="10")
        instructions_frame.pack(fill=tk.BOTH, expand=True)
        
        instructions_text = """1. Load your HTML player data file

2. Select a position from the dropdown

3. Click 'Analyze Players' to see results

4. Click column headers to sort

5. Export results to CSV if needed

Players are ranked by weighted scores based on position requirements."""
        
        instruction_label = ttk.Label(instructions_frame, text=instructions_text, 
                                    justify=tk.LEFT, wraplength=250,
                                    font=("Arial", 9))
        instruction_label.pack()
        
        # === MAIN CONTENT AREA - TABLE SECTION ===
        
        # Results header
        results_header = ttk.Frame(table_section)
        results_header.pack(fill=tk.X, pady=(0, 10))
        
        self.results_label = ttk.Label(results_header, text="No analysis results", 
                                      font=("Arial", 12, "bold"))
        self.results_label.pack(side=tk.LEFT)
        
        # Results table with scrollbars
        table_frame = ttk.Frame(table_section)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview with scrollbars
        self.tree = ttk.Treeview(table_frame)
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_player_select)
        
        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        
        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and treeview
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # === GRAPH SECTION ===
        
        # Set up matplotlib
        plt.style.use('default')
        self.fig, self.ax = plt.subplots(figsize=(12, 4))
        self.fig.patch.set_facecolor('white')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_section)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initialize with empty graph
        self.clear_graph()
        
        # Style the treeview
        ttk_style = ttk.Style()
        ttk_style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        ttk_style.configure("Treeview", font=("Arial", 9))
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

# Create and run the application
if __name__ == "__main__":
    app = PlayerAnalyzer()
    app.run()