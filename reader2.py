import PyPDF2
import pandas as pd
import re


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


def reader(filename):
    with open(filename, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        print('Number of pages:', len(pdf_reader.pages))
        all_data = []
        for page_number, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if page_text:
                cleaned_text = clean_text(page_text)
                page_data = process_text(cleaned_text)
                all_data.append(page_data)
    # Create a DataFrame with all data
    full_df = pd.DataFrame(all_data)
    # Exclude individual address case columns
    columns_to_display = [col for col in full_df.columns if not col.startswith('address_case')]
    return full_df[columns_to_display]

if __name__ == '__main__':
    print('\nAssuming the file is in the current working directory\n')    
    while True:
        print("\nMenu:")
        print("1. Analyze PDF file")
        print("2. Exit")
        
        choice = input("Enter your choice (1 or 2): ")
        
        if choice == "1":
            filename = input("Enter the name of the PDF file: ")
            try:
                df = reader(filename)
                print("\nData processed successfully.\n")
                
                preview_choice = input("Do you want to preview the data? (yes/no): ").lower()
                if preview_choice == 'yes':
                    print(df.head())  # Show the first few rows

                save_choice = input("Do you want to save the data to a CSV file? (yes/no): ").lower()
                if save_choice == 'yes':
                    output_filename = input("Enter a name for the output file (default 'output.csv'): ")
                    output_filename = output_filename if output_filename else 'output.csv'
                    df.to_csv(output_filename, index=False)
                    print(f"Data saved to {output_filename}")
            except Exception as e:
                print(f"An error occurred: {e}")
        elif choice == "2":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")