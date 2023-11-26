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
        'address_case_1': r'\d+ Collection Notes.*?(\d{1,5}\s[\w\s-]+?\s(RD|ST|AVE|LN|DR|BLVD|WAY|CT|PL)\s[\w\s-]+?,\s[A-Z]{2}\s\d{5})',
        'address_case_2': r'(\d{1,5} [A-Z0-9 ]+ (RD|ST|AVE|LN|DR|BLVD|WAY|CT|PL) [A-Z]+, [A-Z]{2} \d{5})',
        'address_case_3': r'(\d{1,5} [A-Z0-9]+ [A-Z]+, [A-Z]{2} \d{5})',
        'address_case_4': r'(\d{3,} [A-Z0-9 ]+ (RD|ST|AVE|LN|DR|BLVD|WAY|CT|PL)[A-Z]+, [A-Z]{2} \d{5})', 
        'address_case_5': r'(\d{1,5}\s[\w\s-]+?\s(RD|ST|AVE|LN|DR|BLVD|WAY|CT|PL)\s[\w\s-]+?,\s*[A-Z]{2}\s*\d{5})',
        'address_case_6': r'(\d{1,5}\s[A-Z]+\s[A-Z]+,\s[A-Z]{2}\s\d{5})',  # Simple format with capitalized street and city names
        'address_case_7': r'(\d{1,5}\s[A-Z0-9]+\s[A-Z]{2},\s\d{5})',       # Format without street type
        'address_case_8': r'(\d{1,5}\s[A-Z0-9]+ [A-Z]+ [A-Z]{2} \d{5})',   # Different spacing format
        'address_case_9': r'(P\.O\. BOX \d{1,5},\s[A-Z]+,\s[A-Z]{2}\s\d{5})',  # PO Box format
        'address_case_10': r'\d+ Collection Notes.*?(\d{1,5}\s[\w\s-]+?\s(RD|ST|AVE|LN|DR|BLVD|WAY|CT|PL)\s[\w\s-]+?,\s[A-Z]{2}\s\d{5})',
    }

    extracted_data = {field: extract_field(text, pattern) for field, pattern in patterns.items()}
    addresses = [extracted_data.get(f'address_case_{i}') for i in range(1, 11)]
    best_address = select_best_address(addresses, extracted_data.get('business_name', ''))
    extracted_data['address'] = best_address
    return extracted_data

def select_best_address(addresses, business_name):
    # Filter out None values and trim spaces
    valid_addresses = [address.strip() for address in addresses if address]

    # Exclude any address that matches the business name
    valid_addresses = [address for address in valid_addresses if business_name.lower() not in address.lower()]

    # If there's only one valid address or none, return it
    if len(valid_addresses) == 1:
        return valid_addresses[0]
    elif not valid_addresses:
        return None

    # Among multiple valid addresses, choose the one with the shortest length
    shortest_address = min(valid_addresses, key=len)

    # If there is no entry in any of the address_cases, assign the shortest address
    if all(address is None for address in addresses):
        return shortest_address

    return shortest_address

def reader(filename, progress_callback, view=False):
    def view_processed_text(processed_data):
        if view:  # Only print if view is True
            print("Viewing processed text for debugging purposes:")
            for page_number, text in processed_data.items():
                print(f"Page {page_number}:\n{text}\n{'-'*40}")

    with open(filename, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)
        all_data = []
        processed_text_data = {}  # Dictionary to hold processed text for each page

        for start_page in range(0, total_pages, 20):
            end_page = min(start_page + 20, total_pages)
            chunk_data = []

            for page_number in range(start_page, end_page):
                page = pdf_reader.pages[page_number]
                page_text = page.extract_text()
                if page_text:
                    cleaned_text = clean_text(page_text)
                    # Store the cleaned text with the page number
                    processed_text_data[page_number + 1] = cleaned_text
                    
                    if page_number % 20 == 0:
                        print(f'Processing pages {start_page + 1} through {end_page} of {total_pages}')
                    page_data = process_text(cleaned_text)
                    chunk_data.append(page_data)
            
            if chunk_data:
                chunk_df = pd.DataFrame(chunk_data)
                all_data.append(chunk_df)
            
            progress_callback(start_page, total_pages)

        # After processing all pages, call the viewer function to print the processed text if view is True
        view_processed_text(processed_text_data)

        df = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
        return df


def debug(df):
    print("\nDebugging\n")
    print("DataFrame Columns:\n", df.columns)
    print("\nFirst 10 Addresses:\n", df['address'].head(10))
    print("\nLast 10 Addresses:\n", df['address'].tail(10))
    print("\nAddress Value Counts:\n", df['address'].value_counts())

    # Check for correct address format
    correct_address_pattern = r'^\d+\s[A-Z0-9 ]+\s(RD|ST|AVE|LN|DR|BLVD|WAY|CT|PL)\s[A-Z]+,\s[A-Z]{2}\s\d{5}$'
    incorrect_addresses = df[~df['address'].str.match(correct_address_pattern)]

    if not incorrect_addresses.empty:
        print("\nIncorrect Addresses Found:\n")
        print(incorrect_addresses[['page', 'address']])
        # Print the page numbers of incorrect addresses
        incorrect_pages = incorrect_addresses['page'].unique()
        print("\nPages with Incorrect Addresses:\n", incorrect_pages)