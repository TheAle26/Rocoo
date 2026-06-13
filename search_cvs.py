import PyPDF2

def build_master_upc_dict(df):
    """
    Maps a UPC to a LIST of Master Boxes.
    Handles the 1-to-Many relationship (One UPC -> Many Boxes).
    """
    master_dict = {}
    print("📊 Building Master UPC Dictionary...")
    
    for index, row in df.iterrows():
        upc = str(row.get('UPC/EAN (GTIN)', '')).strip()
        if not upc or upc == 'nan':
            continue
            
        box_data = {
            "Master Box #": str(row.get('Master Box #', '')).strip(),
            "FNSKU": str(row.get('FNSKU', '')).strip(),
            "Quantity": int(float(row.get('Quantity', 0))),
            "Amazon Labels": str(row.get('Amazon Labels', '')).strip(),
            "DONE": str(row.get('DONE', 'False')).strip(),
            "Row_Index": index
        }
        
        # If the UPC isn't in the dict yet, create an empty list
        if upc not in master_dict:
            master_dict[upc] = []
            
        # Add this box to the UPC's list
        master_dict[upc].append(box_data)
        
    print(f"✅ Mapped {len(master_dict)} unique UPCs to their respective boxes.")
    return master_dict


def build_amazon_label_to_page_dict(pdf_path, df):
    """
    Maps the 'Amazon Label' string to the exact Page Number in the PDF.
    """
    label_map = {}
    
    # FIX: Use .dropna() to completely remove empty cells (float NaNs) 
    # BEFORE we convert to strings and get the unique values.
    labels_to_find = df['Amazon Labels'].dropna().astype(str).str.strip().unique()
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"📄 Scanning {len(reader.pages)} Big Box PDF pages...")
            
            for page_num in range(len(reader.pages)):
                page_text = reader.pages[page_num].extract_text()
                
                # Failsafe: PyPDF2 sometimes returns None for perfectly blank pages. 
                # We need to make sure page_text is a valid string.
                if not page_text:
                    continue
                
                for raw_label in labels_to_find:
                    # Final safety cast to string, just in case
                    label = str(raw_label)
                    
                    if label and label != 'nan' and label in page_text:
                        if label not in label_map:
                            label_map[label] = page_num
                            
        print(f"✅ Successfully mapped {len(label_map)} Big Box Pages.")
        return label_map
        
    except FileNotFoundError:
        print(f"❌ Error: Big box PDF not found at {pdf_path}")
        return {}
    except Exception as e:
        print(f"❌ Unexpected Error scanning Big Box PDF: {e}")
        return {}