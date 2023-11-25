import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import matplotlib.pyplot as plt
import PyPDF2
import pandas as pd
import re
import os


is_processing = False

""" PDF TEXT/READER FUNCTIONS """
def clean_text(text):
    # Implement any specific cleanup here, e.g., replacing known misinterpretations, fixing line breaks
    text = text.replace('\n', ' ')
    text = re.sub(r'\s{2,}', ' ', text) 
    return text

def extract_field(text, pattern):
    match = re.search(pattern, text)
    if match and match.groups():
        # Check if the matched value is exactly "0.00"
        if match.group(1) == "0.00":
            return "0.00"
        return match.group(1)
    return None

def process_text(text):
    patterns = {
        'date': r'HOUSE LEADS(\d{2}/\d{2}/\d{2})',
        'business_name': r'Customer #:\s\d+\s+\((.*?)\)',
        'contact_name': r'Total Product Sales(.*?)(?:PP|\d+\.\d{2})',
        'collection_status': r'Sales\w+ [A-Z]+\s*(PP)?\s*\d',
        'customer_number': r'Customer #:\s(\d+)',
        'phone_number_1': r'Phone 2.*?(\(\d{3}\)\d{3}-\d{4})',
        'phone_number_2': r'\(\d{3}\)\d{3}-\d{4}.*?(\(\d{3}\)\d{3}-\d{4})',
        'collection_status': r'Total Product Sales\s*(PP)?',
        'collection_status': r'Sales\w+ [A-Z]+\s*(PP)?\s*\d',
        'total_product_sales': r'(\d{1,3}(?:,\d{3})*\.\d{2})',
        'balance': r'(\d{1,6}\.\d{2})\s+Invoice #',
        'past_due': r'(\d{1,6}\.\d{2})\s+Invoice #', 
        'address_case_1': r'Collection Notes(.*?)\b(\d+\s[\w\s-]+?)\s*(RD|ST|AVE|LN|DR|BLVD|WAY|CT|PL)([\w\s]+?,\s*[A-Z]{2}\s*\d{5})',
        'address_case_2': r'(\d{1,5} [A-Z0-9 ]+ (RD|ST|AVE|LN|DR|BLVD|WAY|CT|PL) [A-Z]+, [A-Z]{2} \d{5})',
        'address_case_3': r'(\d{1,5} [A-Z0-9]+ [A-Z]+, [A-Z]{2} \d{5})',
        'address_case_4': r'(\d{3,} [A-Z0-9 ]+ (RD|ST|AVE|LN|DR|BLVD|WAY|CT|PL)[A-Z]+, [A-Z]{2} \d{5})', 
    }

    extracted_data = {field: extract_field(text, pattern) for field, pattern in patterns.items()}

    addresses = [extracted_data.get(case) for case in ['address_case_1', 'address_case_2', 'address_case_3', 'address_case_4'] if extracted_data.get(case)]

    # Evaluate and select the best address
    best_address = select_best_address(addresses)
    extracted_data['address'] = best_address

    return extracted_data

def correct_address_spacing(address):
    # Insert space before city and after street type
    corrected_address = re.sub(r'(\b(RD|ST|AVE|LN|DR|BLVD|WAY|CT|PL))([A-Z])', r'\1 \3', address)
    return corrected_address

def select_best_address(addresses):
    corrected_addresses = [correct_address_spacing(address) for address in addresses]
    # Select the address that best matches the desired format
    # Example: Select the longest address after correction
    return max(corrected_addresses, key=len, default=None)


def reader(filename, progress_callback):
    with open(filename, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)
        all_data = []

        for start_page in range(0, total_pages, 20):
            end_page = min(start_page + 20, total_pages)
            chunk_data = []

            for page_number in range(start_page, end_page):
                page = pdf_reader.pages[page_number]
                page_text = page.extract_text()
                if page_text:
                    cleaned_text = clean_text(page_text)
                    page_data = process_text(cleaned_text)
                    chunk_data.append(page_data)

            if chunk_data:
                chunk_df = pd.DataFrame(chunk_data)
                all_data.append(chunk_df)
            
            progress_callback(start_page, total_pages)

        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

""" GUI FUNCTIONS """

def process_single_file(file_path):
    global is_processing
    is_processing = True
    try:
        data = reader(file_path, update_progress)
        if data.empty:
            messagebox.showinfo("Info", "No data found in the PDF.")
        return data
    except Exception as e:
        messagebox.showerror("Error", f'Error processing file: {str(e)}')
    finally:
        is_processing = False
        return None

    
def process_directory(directory):
    global is_processing
    is_processing = True
    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    all_data = []
    for pdf_file in pdf_files:
        full_path = os.path.join(directory, pdf_file)
        try: 
            pdf_data = reader(full_path, update_progress)
            if not pdf_data.empty:
                preview_choice = messagebox.askyesno("Preview", f"Do you want to preview the data from {pdf_file}?")
                if preview_choice:
                    print(pdf_data)  # Show the first few rows of this file
            all_data.append(pdf_data)
        except Exception as e:
            messagebox.showerror("Error", f'Error processing {pdf_file}: {e}')
        finally: 
            is_processing = False
    return pd.concat(all_data, ignore_index=True) if all_data else None
    
def analyze_single_file():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        data = process_single_file(file_path)
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
            print(data.head())  # Show the first few rows

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
    progress_label.config(text=f"{progress}%")  # Update the label
    root.update_idletasks()  # Update GUI

def update_loading_indicator():
    global is_processing  # Ensure this line is present
    if is_processing:
        current_text = loading_label.cget("text")
        num_dots = current_text.count(".")
        new_text = "Processing" + "." * ((num_dots + 1) % 4)  # Cycle through 0 to 3 dots
        loading_label.config(text=new_text)
    else:
        loading_label.config(text="Idle")
    root.after(500, update_loading_indicator)  # Update every 500 ms

""" MAIN PROGRAM """
if __name__ == '__main__':
    root = tk.Tk()
    root.title("PDF Reader")
    root.geometry("300x300")
    
    # Initialize the 'loading_label'
    loading_label = tk.Label(root, text="Idle")
    loading_label.pack()
    
    progress_label = tk.Label(root, text="0%")
    progress_label.pack()

    progress_var = tk.IntVar()
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", variable=progress_var)
    progress_bar.pack()

    tk.Button(root, text="Analyze Single File", command=analyze_single_file).pack()
    tk.Button(root, text="Analyze Directory", command=analyze_directory).pack()
    update_loading_indicator()
    root.mainloop()