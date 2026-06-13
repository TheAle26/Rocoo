import PyPDF2
import pandas as pd

# Notice I changed 'csv_path' to 'df_memory'
def build_upc_to_page_dictionary(pdf_path, df_memory):
    """
    1. Takes the memory_df to get the UPCs and Amazon Labels.
    2. Scans the PDF to find which page each Amazon Label is on.
    3. Returns a dictionary: {UPC: [Amazon Label, Page Number]}
    """
    
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
                # Ensure the parentheses are here!
                page_text = reader.pages[page_num].extract_text()
                
                # 'Ctrl+F' through our list of needed labels on this page
                # 'Ctrl+F' through our list of needed labels on this page
                for label in labels_to_find:
                    
                    # --- NEW: Force the label to be a string to prevent the 'float' crash ---
                    safe_label = str(label).strip()
                    
                    # Skip 'nan' or empty labels just in case the CSV has blank rows
                    if safe_label and safe_label.lower() != 'nan' and safe_label in page_text:
                        
                        # If we haven't mapped this label yet, save the page number
                        # Note: We use the original 'label' variable here to maintain the dictionary key
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