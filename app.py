from flask import Flask, request, render_template, jsonify, redirect, url_for, send_file
import os
import concurrent.futures
import pandas as pd

# Import your external functions
from shoe_box import print_label, map_all_labels_in_pdf
# (Make sure to put the two new dictionary builders we just wrote into big_box.py or search_cvs.py and import them here)
from search_cvs import build_master_upc_dict, build_amazon_label_to_page_dict 

app = Flask(__name__, static_folder='static')

# Global Variables for our Memory Hash Maps
df_memory = None  
label_map = None          # Shoe box map {FNSKU: Product Name}
bix_box_map = None        # Big box map {Amazon Label: Page Number}
master_upc_map = None     # Master CSV map {UPC: [List of Master Boxes]}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

CSV_FILENAME = 'actual_shipment.csv'
BIG_BOX_PDF_FILENAME = 'box_labels_actual_shipment.pdf'
SMALL_BOX_PDF_FILENAME = 'shoe_labels_actual_shipment.pdf'


def process_pdfs_concurrently(shoe_path, box_path, memory_df):
    """
    Runs all 3 parsers at the exact same time using 3 background threads.
    """
    global label_map, bix_box_map, master_upc_map
    print("🚀 Starting parallel processing (Shoe PDF, Box PDF, and CSV Map)...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # 1. Dispatch all three tasks
        future_shoes = executor.submit(map_all_labels_in_pdf, shoe_path)
        future_boxes = executor.submit(build_amazon_label_to_page_dict, box_path, memory_df)
        future_master = executor.submit(build_master_upc_dict, memory_df)
        
        # 2. Wait and grab results
        label_map = future_shoes.result()
        bix_box_map = future_boxes.result()
        master_upc_map = future_master.result()
        
    print("✅ All data successfully processed and loaded into memory!")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        mode = request.form.get('mode')
        global df_memory
        path_csv = os.path.join(OUTPUT_FOLDER, CSV_FILENAME)

        if mode == 'scan':
            if not all(os.path.exists(os.path.join(OUTPUT_FOLDER, f)) for f in [CSV_FILENAME, BIG_BOX_PDF_FILENAME, SMALL_BOX_PDF_FILENAME]):
                return render_template('index.html', error="No previous session found.")
            df_memory = pd.read_csv(path_csv, dtype=str)

        else:   
            shipment = request.files.get('shipment')
            big_box_label_pdf = request.files.get('big_box_label_pdf') 
            small_box_label_pdf = request.files.get('small_box_label_pdf') 

            if shipment and big_box_label_pdf and small_box_label_pdf:
                try:
                    shipment.save(path_csv)
                    big_box_label_pdf.save(os.path.join(OUTPUT_FOLDER, BIG_BOX_PDF_FILENAME))
                    small_box_label_pdf.save(os.path.join(OUTPUT_FOLDER, SMALL_BOX_PDF_FILENAME))

                    if shipment.filename.endswith('.xlsx'):
                        df_memory = pd.read_excel(path_csv, dtype=str)
                    else:
                        df_memory = pd.read_csv(path_csv, dtype=str)
                except Exception as e:
                    return render_template('index.html', error=f"Error processing files: {str(e)}")
            else:
                return render_template('index.html', error="Please provide all valid files.")

        if 'DONE' not in df_memory.columns:
            df_memory['DONE'] = 'False'   
                 
        df_memory.to_csv(path_csv, index=False)  
              
        # Launch the background builders
        process_pdfs_concurrently(
            os.path.join(OUTPUT_FOLDER, SMALL_BOX_PDF_FILENAME), 
            os.path.join(OUTPUT_FOLDER, BIG_BOX_PDF_FILENAME), 
            df_memory
        )
                
        return redirect(url_for('processing_page'))

    return render_template('index.html')


@app.route('/processing')
def processing_page():
    return render_template('processing.html')


# --- NEW: SCAN ROUTE (Just returns the list of boxes) ---
@app.route('/scan', methods=['POST'])
def scan_barcode():
    data = request.get_json()
    barcode = data.get('barcode', '').strip()

    if not barcode:
        return jsonify({"status": "error", "message": "Empty code"}), 400

    global master_upc_map
    if master_upc_map is None:
        return jsonify({"status": "error", "message": "CSV data is not in memory"}), 400
    
    boxes_list = master_upc_map.get(barcode)
    
    if not boxes_list:
        return jsonify({"status": "error", "message": f"UPC {barcode} not found."}), 404
    
    # Return the list to the frontend to display the Master Boxes
    return jsonify({
        "status": "success",
        "UPC": barcode,
        "boxes": boxes_list
    })


# --- ROUTE 1: PRINT SHOES ONLY ---
@app.route('/print_shoes', methods=['POST'])
def print_shoes():
    data = request.get_json()
    row_index = data.get('row_index')

    if row_index is None:
        return jsonify({"status": "error", "message": "Missing row_index."}), 400
        
    row_index = int(row_index)
    global df_memory, label_map
    
    fnsku = df_memory.at[row_index, 'FNSKU']
    quantity = int(float(df_memory.at[row_index, 'Quantity']))
    product_name = label_map.get(fnsku, "Unknown Product")
    
    try:
        # Prints the exact quantity specified in the CSV
        print_label(fnsku, quantity, product_name)
        return jsonify({
            "status": "success", 
            "message": f"Sent {quantity} shoe labels to the printer!"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Shoe printer error: {str(e)}"}), 500


# --- ROUTE 2: PRINT BIG BOX ONLY ---
@app.route('/print_big_box', methods=['POST'])
def print_big_box():
    data = request.get_json()
    row_index = data.get('row_index')

    if row_index is None:
        return jsonify({"status": "error", "message": "Missing row_index."}), 400
        
    row_index = int(row_index)
    global df_memory, bix_box_map
    
    amazon_label = df_memory.at[row_index, 'Amazon Labels']
    big_box_page_num = bix_box_map.get(amazon_label)
    
    if big_box_page_num is None:
        return jsonify({"status": "error", "message": f"Page for label {amazon_label} not found."}), 404

    try:
        # Insert your actual big box print logic here!
        # print_amazon_labels(amazon_label, big_box_page_num)
        
        # We return the human-readable page number (+1) just in case the UI wants to show it
        return jsonify({
            "status": "success",
            "message": f"Sent Big Box label (Page {big_box_page_num + 1}) to printer!",
            "page": big_box_page_num + 1
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Big Box printer error: {str(e)}"}), 500


# --- ROUTE 3: MARK DONE ONLY ---
@app.route('/mark_done', methods=['POST'])
def mark_done():
    data = request.get_json()
    row_index = data.get('row_index')
    upc = data.get('upc')

    if row_index is None or upc is None:
        return jsonify({"status": "error", "message": "Missing data."}), 400
        
    row_index = int(row_index)
    global df_memory, master_upc_map
    
    # 1. Update CSV and save to disk
    df_memory.at[row_index, 'DONE'] = 'True'
    path_csv = os.path.join(OUTPUT_FOLDER, CSV_FILENAME)
    df_memory.to_csv(path_csv, index=False)
    
    # 2. Update memory dict so UI stays in sync
    for box in master_upc_map[upc]:
        if box['Row_Index'] == row_index:
            box['DONE'] = 'True'
            break
            
    return jsonify({
        "status": "success",
        "message": f"Box marked DONE in CSV."
    })
    
@app.route('/download_csv')
def download_csv():
    """
    Allows the user to download the updated CSV with the 'DONE' statuses.
    """
    path_csv = os.path.join(OUTPUT_FOLDER, CSV_FILENAME)
    
    if os.path.exists(path_csv):
        # as_attachment=True forces the browser to download instead of trying to display it
        return send_file(path_csv, as_attachment=True, download_name="updated_shipment.csv")
    else:
        return "CSV file not found. Please upload a shipment first.", 404

if __name__ == '__main__':
    app.run(debug=True)