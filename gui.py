# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter import simpledialog
import os
import pandas as pd
import reader  # Importing the reader module
import numpy as np

is_processing = False

def process_multiple_files(file_path):
    global is_processing
    is_processing = True
    try:
        # Set view=False to disable printing processed text
        data = reader.reader(file_path, update_progress, view=False)
        if data.empty:
            messagebox.showinfo("Info", "No data found in the PDF.")
        else:
            # Add additional processing or exporting logic here if needed
            pass
        return data
    except Exception as e:
        messagebox.showerror("Error", f'Error processing file: {str(e)}')
        return None
    finally:
        is_processing = False

def process_directory(directory):
    global is_processing
    is_processing = True
    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    all_data = []

    for pdf_file in pdf_files:
        full_path = os.path.join(directory, pdf_file)
        try:
            pdf_data = reader.reader(full_path, update_progress, view=True)
            if not pdf_data.empty:
                all_data.append(pdf_data)
        except Exception as e:
            messagebox.showerror("Error", f'Error processing {pdf_file}: {e}')

    combined_data = pd.concat(all_data, ignore_index=True) if all_data else None

    # Preview option after processing all files
    if combined_data is not None:
        preview_choice = messagebox.askyesno("Preview", "Do you want to preview the combined data from all files?")
        if preview_choice:
            print("Please choose columns:\n\n", combined_data.columns, "\n")
            preview_data_with_user_input(combined_data)

    is_processing = False
    return combined_data

def preview_data_with_user_input(pdf_data):
    user_input = input("Enter the types of columns you want to preview, separated by commas (e.g., 'balance, customer_number'): ")
    column_types = [col_type.strip() for col_type in user_input.strip(',').split(',')]

    columns_to_show = []
    for column_type in column_types:
        # Check for the main column
        if column_type in pdf_data.columns:
            columns_to_show.append(column_type)
        # Add any 'case' columns related to the main column
        columns_to_show.extend([col for col in pdf_data.columns if col.startswith(f'{column_type}_case')])

    existing_columns = [col for col in columns_to_show if col in pdf_data.columns]

    if existing_columns:
        print("\n\nRefined DataFrame:\n\n")
        # Refine the entire DataFrame, not just the existing columns
        refined_df, omitted_cases = reader.refine_dataframe(pdf_data)
        # Ensure only existing columns are accessed
        safe_refined_columns = [col for col in existing_columns if col in refined_df.columns]
        safe_omitted_columns = [col for col in existing_columns if col in omitted_cases.columns]

        # Display the desired columns from the refined DataFrame
        print(refined_df[safe_refined_columns].head(50))

        # Display the desired columns from the omitted cases DataFrame
        print("\n\nOmitted Cases:\n\n")
        print(omitted_cases[safe_omitted_columns].head(50))
    else:
        print("No matching columns found for the given input.")


def analyze_multiple_files():
    file_paths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])  # For multiple file selection
    if file_paths:
        all_data = []
        for file_path in file_paths:
            data = process_multiple_files(file_path)
            if data is not None:
                all_data.append(data)
        combined_data = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
        process_data(combined_data)

def analyze_directory():
    directory = filedialog.askdirectory()
    if directory:
        data = process_directory(directory)
        process_data(data)

def process_data(data):
    if data is not None and not data.empty:
        # Ask user for the type of DataFrame to export
        export_choice = messagebox.askyesno("Export", "Choose 'Yes' for final DataFrame or 'No' for debugging DataFrame.")
        if export_choice:
            # Ask user for cutoff value
            cutoff = simpledialog.askfloat("Input", "Enter the cutoff value:", parent=root)
            if cutoff is None:  # If the user closes the dialog or clicks Cancel
                cutoff = 7000  # Use a default value

            # Refine DataFrame and export
            refined_data, omitted_cases = reader.refine_dataframe(data, cutoff)
            export_dataframe(refined_data)
        else:
            # Export full DataFrame for debugging
            export_dataframe(data)

def export_dataframe(df):
    save_choice = messagebox.askyesno("Save", "Do you want to save the data to a CSV file?")
    if save_choice:
        output_filename = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')])
        if output_filename:
            df.to_csv(output_filename, index=False)
            messagebox.showinfo("Saved", f"Data saved to {output_filename}")
    else:
        print(df.head(100))  # Display the first 100 rows in the console for preview

def update_progress(start_page, total_pages):
    progress = int((start_page / total_pages) * 100)
    progress_var.set(progress)
    progress_label.config(text=f"{progress}%")
    root.update_idletasks()

def update_loading_indicator():
    if is_processing:
        current_text = loading_label.cget("text")
        num_dots = current_text.count(".")
        new_text = "Processing" + "." * ((num_dots + 1) % 4)
        loading_label.config(text=new_text)
    else:
        loading_label.config(text="Idle")
    root.after(500, update_loading_indicator)

if __name__ == '__main__':
    root = tk.Tk()
    root.title("PDF Reader")
    root.geometry("500x300")

    loading_label = tk.Label(root, text="Idle")
    loading_label.pack()

    progress_label = tk.Label(root, text="0%")
    progress_label.pack()

    progress_var = tk.IntVar()
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", variable=progress_var)
    progress_bar.pack()

    tk.Button(root, text="Analyze Single/Multiple Files", command=analyze_multiple_files, height=1).pack()
    tk.Button(root, text="Analyze Directory", command=analyze_directory, height=1).pack()

    update_loading_indicator()
    root.mainloop()
