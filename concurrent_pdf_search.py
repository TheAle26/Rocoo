import os
import concurrent.futures

# Make sure these are declared at the top of your script if they aren't already
label_map = {}
bix_box_map = {}

def process_pdfs_concurrently(output_folder, shoe_pdf, box_pdf, memory_df):
    """
    Runs both PDF parsers at the exact same time using 2 background threads.
    """
    global label_map
    global bix_box_map
    
    shoe_path = os.path.join(output_folder, shoe_pdf)
    box_path = os.path.join(output_folder, box_pdf)
    
    print("🚀 Starting parallel PDF processing...")
    
    # Create a pool with exactly 2 workers (threads)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        
        # 1. Dispatch both tasks immediately
        # executor.submit(function_name, arg1, arg2...)
        future_shoes = executor.submit(map_all_labels_in_pdf, shoe_path)
        future_boxes = executor.submit(build_upc_to_page_dictionary, box_path, memory_df)
        
        # 2. Wait for them to finish and grab their return values.
        # .result() will block the main thread until the specific background thread is done.
        label_map = future_shoes.result()
        bix_box_map = future_boxes.result()
        
    print("✅ Both PDFs successfully processed in the background!")

# --- Where you actually call it in your code ---
# process_pdfs_concurrently(OUTPUT_FOLDER, SHOE_PDF_FILENAME, BOX_PDF_FILENAME, df_memory)