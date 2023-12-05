# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os
import pandas as pd
import reader  # Importing the reader module

is_processing = False

def process_multiple_files(file_path):
    global is_processing
    is_processing = True
    try:
        data = reader.reader(file_path, update_progress, view=False)
        if data.empty:
            messagebox.showinfo("Info", "No data found in the PDF.")
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
                preview_choice = messagebox.askyesno("Preview", f"Do you want to preview the data from {pdf_file}?")
                if preview_choice:
                    print(f'\n\nPreviewing data from {pdf_file}:\n')
                    print(pdf_data.columns)
                    print('\n\n', pdf_data.head(100))
                # preview for debugging purposes
                # if preview_choice: # FOR ADDRESS CASES  
                #     address_case_columns = [col for col in pdf_data.columns if 'address_case' in col]
                #     address_columns = [col for col in pdf_data.columns if col == 'address']
                #     print('\n\n FOR ADDRESS CASES \n\n', pdf_data[address_case_columns + address_columns].tail(50))
                if preview_choice: # FOR BALANCE CASES
                    balance_case_columns = [col for col in pdf_data.columns if 'balance_case' in col]
                    balance_columns = [col for col in pdf_data.columns if col == 'balance']
                    print('\n\n FOR BALANCE CASES \n\n', pdf_data[balance_case_columns + balance_columns].tail(50))
                # if preview_choice: # FOR PAST DUE CASES
                #     past_due_case_columns = [col for col in pdf_data.columns if 'past_due_case' in col]
                #     past_due_columns = [col for col in pdf_data.columns if col == 'past_due']
                #     print('\n\n FOR PAST DUES CASES \n\n', pdf_data[past_due_case_columns + past_due_columns].tail(50))
                # if preview_choice: # FOR TOTAL PRODUCT CASES
                #     total_product_case_columns = [col for col in pdf_data.columns if 'total_product_sales_case' in col]
                #     total_product_columns = [col for col in pdf_data.columns if col == 'total_product']
                #     print('\n\n FOR TOTAL PRODUCT CASES \n\n', pdf_data[total_product_case_columns + total_product_columns].tail(50))
            all_data.append(pdf_data)
        except Exception as e:
            messagebox.showerror("Error", f'Error processing {pdf_file}: {e}')
    is_processing = False
    return pd.concat(all_data, ignore_index=True) if all_data else None

def analyze_multiple_files():
    file_paths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
    if file_paths:
        for file_path in file_paths:
            data = process_multiple_files(file_path)
            process_data(data) 

def analyze_directory():
    directory = filedialog.askdirectory()
    if directory:
        data = process_directory(directory)
        process_data(data)

def process_data(data):
    if data is not None and not data.empty:
        preview_choice = messagebox.askyesno("Preview", "Do you want to preview the data?")
        if preview_choice:
            print(data.head(100))

        save_choice = messagebox.askyesno("Save", "Do you want to save the data to a CSV file?")
        if save_choice:
            output_filename = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')])
            if output_filename:
                data.to_csv(output_filename, index=False)
                messagebox.showinfo("Saved", f"Data saved to {output_filename}")
    else:
        messagebox.showinfo("Info", "No PDF files found or an error occurred.")

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
