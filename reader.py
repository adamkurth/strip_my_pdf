# reader2.py
import PyPDF2
import pandas as pd
import re

def clean_text(text):
    text = text.replace('\n', ' ')
    text = re.sub(r'\s{2,}', ' ', text) 
    return text

def extract_field(text, pattern):
    match = re.search(pattern, text)
    if match and match.groups():
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
    corrected_address = re.sub(r'(\b(RD|ST|AVE|LN|DR|BLVD|WAY|CT|PL))([A-Z])', r'\1 \3', address)
    return corrected_address

def select_best_address(addresses):
    corrected_addresses = [correct_address_spacing(address) for address in addresses]
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
