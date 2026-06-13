import PyPDF2
import pandas as pd

def build_upc_to_page_dictionary(pdf_path, csv_path):
    """
    1. Reads the CSV to get the UPCs and Amazon Labels.
    2. Scans the PDF to find which page each Amazon Label is on.
    3. Returns a dictionary: {UPC: [Amazon Label, Page Number]}
    """
    # Load the CSV data into memory
    # Using dtype=str ensures UPC barcodes don't lose leading zeros
    df_memory = pd.read_csv(csv_path, dtype=str)
    
    # Clean the columns to avoid hidden whitespace issues breaking the text search
    df_memory['Amazon Labels'] = df_memory['Amazon Labels'].astype(str).str.strip()
    df_memory['UPC/EAN (GTIN)'] = df_memory['UPC/EAN (GTIN)'].astype(str).str.strip()
    
    # Get a unique list of all Amazon Labels we need to look for in the PDF
    labels_to_find = df_memory['Amazon Labels'].unique().tolist()
    
    # Dictionary to hold our intermediate mapping {Amazon Label: Page Number}
    label_to_page_map = {}
    
    print(f"🔍 Searching PDF for {len(labels_to_find)} unique Amazon Labels...")
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)
            
            # Scan page by page (Remember: page_num starts at index 0)
            for page_num in range(total_pages):
                page_text = reader.pages[page_num].extract_text()
                
                # 'Ctrl+F' through our list of needed labels on this page
                for label in labels_to_find:
                    # Skip 'nan' or empty labels just in case the CSV has blank rows
                    if label and label != 'nan' and label in page_text:
                        # If we haven't mapped this label yet, save the page number
                        if label not in label_to_page_map:
                            label_to_page_map[label] = page_num
                            
    except FileNotFoundError:
        print(f"❌ Error: The file '{pdf_path}' was not found.")
        return {}

    # Build the final dictionary connecting UPC -> [Label, Page]
    final_dict = {}
    
    for index, row in df_memory.iterrows():
        upc = row['UPC/EAN (GTIN)']
        amazon_label = row['Amazon Labels']
        
        # Skip empty UPC rows
        if not upc or upc == 'nan':
            continue
            
        # Look up the page number we found in the PDF
        page_num = label_to_page_map.get(amazon_label)
        
        # Save to final dictionary (page_num will be None if the label wasn't in the PDF)
        final_dict[upc] = [amazon_label, page_num]
        
    print(f"✅ Successfully built dictionary with {len(final_dict)} UPC entries!")
    return final_dict

# --- Execution ---
if __name__ == "__main__":
    # Using your exact uploaded filenames
    pdf_file = "Box labels-Shipment #4-FBA19D5NG5P4-1778603221535.pdf"
    csv_file = "SHIPMENT #4.xlsx - SHIPMENT #4.csv"

    # 1. Build the dictionary once
    memory_dictionary = build_upc_to_page_dictionary(pdf_file, csv_file)

    # 2. Test a lookup (Simulating a barcode scan)
    # Replace the string below with a real UPC from your CSV to test it
    scanned_upc = "ENTER_A_REAL_UPC_HERE" 
    
    result = memory_dictionary.get(scanned_upc)

    if result:
        found_label = result[0]
        found_page = result[1]
        
        if found_page is not None:
            print(f"🎯 SUCCESS: UPC {scanned_upc} matches label '{found_label}'.")
            print(f"🖨️ Send PDF index {found_page} to the printer!")
        else:
            print(f"⚠️ WARNING: UPC {scanned_upc} maps to '{found_label}', but it was NOT found in the PDF.")
    else:
        print(f"❌ Scanned UPC '{scanned_upc}' not found in the dictionary.")