from flask import Flask, request, render_template, jsonify, redirect, url_for, send_file
import os
import concurrent.futures
import pandas as pd
from shoe_box import print_label, map_all_labels_in_pdf
from search_cvs import (
    build_lookup_index,
    build_amazon_label_to_page_dict,
    resolve_query,
    MAX_CHOICES,
)
import signal
from printer import print_amazon_label



app = Flask(__name__, static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB cap on uploads


@app.errorhandler(413)
def too_large(e):
    return render_template('index.html', error="Upload too large. The total upload must be under 50 MB."), 413

# Global Variables for our Memory Hash Maps
df_memory = None
label_map = None          # Shoe box map {FNSKU: Product Name}
bix_box_map = None        # Big box map {Amazon Label: Page Number}
lookup_index = None       # Shipment index: see search_cvs.build_lookup_index

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

CSV_FILENAME = 'actual_shipment.csv'
BIG_BOX_PDF_FILENAME = 'box_labels_actual_shipment.pdf'
SMALL_BOX_PDF_FILENAME = 'shoe_labels_actual_shipment.pdf'


def process_pdfs_concurrently(small_label_path, bix_box_path, memory_df):
    """
    Runs all 3 parsers at the exact same time using 3 background threads.
    """
    global label_map, bix_box_map, lookup_index
    print("Starting parallel processing (Shoe PDF, Box PDF, and CSV Map)...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # 1. Dispatch all three tasks
        future_shoes = executor.submit(map_all_labels_in_pdf, small_label_path)
        future_boxes = executor.submit(build_amazon_label_to_page_dict, bix_box_path, memory_df)
        future_master = executor.submit(build_lookup_index, memory_df)

        # 2. Wait and grab results
        label_map = future_shoes.result()
        bix_box_map = future_boxes.result()
        lookup_index = future_master.result()

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
        df_memory.columns = df_memory.columns.str.strip()
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


def public_box(box):
    """Strips the internal search blob before a box goes over the wire."""
    return {k: v for k, v in box.items() if not k.startswith('_')}


# --- SCAN ROUTE ---
# Handles the barcode gun and anything a worker types by hand: a partial UPC,
# a Master Box #, an FNSKU, or a style plus size. See search_cvs.resolve_query.
@app.route('/scan', methods=['POST'])
def scan_barcode():
    data = request.get_json(silent=True) or {}
    query = str(data.get('barcode', '')).strip()

    if not query:
        return jsonify({"status": "error", "message": "Empty code"}), 400

    global lookup_index
    if lookup_index is None:
        return jsonify({"status": "error", "message": "CSV data is not in memory"}), 400

    kind, payload = resolve_query(query, lookup_index)

    if kind == 'boxes':
        upcs = {b['UPC'] for b in payload}
        return jsonify({
            "status": "success",
            "query": query,
            # Kept for the plain barcode case, where every box shares one UPC.
            "UPC": upcs.pop() if len(upcs) == 1 else None,
            "boxes": [public_box(b) for b in payload],
        })

    if kind == 'choices':
        return jsonify({
            "status": "choose",
            "query": query,
            "choices": payload[:MAX_CHOICES],
            "total": len(payload),
        })

    return jsonify({
        "status": "error",
        "message": f"No match for '{query}'.",
        "suggestions": payload[:MAX_CHOICES],
        "total": len(payload),
    }), 404


# --- ROUTE 1: PRINT SHOES ONLY (Stateless) ---
@app.route('/print_shoes', methods=['POST'])
def print_shoes():
    data = request.get_json()
    fnsku = data.get('fnsku')
    quantity = data.get('quantity')

    if not fnsku or quantity is None:
        return jsonify({"status": "error", "message": "Missing FNSKU or quantity."}), 400
        
    global label_map
    
    # We still use label_map to find the name, but we don't need the CSV memory anymore!
    product_name = label_map.get(fnsku, "Unknown Product")
    
    if product_name == "Unknown Product":
        return jsonify({"status": "error", "message": f"FNSKU {fnsku} not found in PDF."}), 404
    
    try:
        print_label(fnsku, int(quantity), product_name)
        return jsonify({
            "status": "success", 
            "message": f"Sent {quantity} shoe labels to the printer!"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Shoe printer error: {str(e)}"}), 500


# Make sure to import your new function at the top of app.py!
# from big_box import print_amazon_label 

# --- ROUTE 2: PRINT BIG BOX ONLY (Stateless) ---
@app.route('/print_big_box', methods=['POST'])
def print_big_box():
    data = request.get_json()
    amazon_label = data.get('amazon_label')

    if not amazon_label:
        return jsonify({"status": "error", "message": "Missing Amazon Label."}), 400
        
    global bix_box_map
    
    # Translate the label to a page number using our O(1) dictionary
    big_box_page_num = bix_box_map.get(amazon_label)
    
    if big_box_page_num is None:
        return jsonify({"status": "error", "message": f"Page for label {amazon_label} not found in PDF."}), 404

    try:
        # Construct the full path to the Big Box PDF
        pdf_path = os.path.join(OUTPUT_FOLDER, BIG_BOX_PDF_FILENAME) # Adjust this variable if your PDF is named differently!
        
        # Call our new extraction and printing function
        print_amazon_label(pdf_path, big_box_page_num)
        
        return jsonify({
            "status": "success",
            "message": f"Sent Big Box label (Page {big_box_page_num + 1}) to printer!",
            "page": big_box_page_num + 1
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Big Box printer error: {str(e)}"}), 500

# --- ROUTE 3: MARK DONE ONLY (Needs row_index to update CSV) ---
@app.route('/mark_done', methods=['POST'])
def mark_done():
    data = request.get_json(silent=True) or {}
    row_index = data.get('row_index')

    if row_index is None:
        return jsonify({"status": "error", "message": "Missing data."}), 400

    global df_memory, lookup_index
    if df_memory is None or lookup_index is None:
        return jsonify({"status": "error", "message": "Session data not loaded."}), 400

    try:
        row_index = int(row_index)
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid row index."}), 400

    if row_index not in df_memory.index:
        return jsonify({"status": "error", "message": "Invalid row index."}), 404

    df_memory.at[row_index, 'DONE'] = 'True'
    path_csv = os.path.join(OUTPUT_FOLDER, CSV_FILENAME)
    df_memory.to_csv(path_csv, index=False)

    # Keyed on the row rather than the UPC, so this works no matter which way
    # the worker found the box. Every index shares the same dict, so this one
    # assignment is visible through all of them.
    box = lookup_index['by_row'].get(row_index)
    if box is not None:
        box['DONE'] = 'True'

    return jsonify({"status": "success", "message": "Box marked DONE."})
    
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
    

@app.route('/view_data')
def view_data():
    global df_memory
    
    # If there is no active session, redirect back to home
    if df_memory is None:
        return redirect(url_for('index'))

    # Define EXACTLY which columns you want to display to the user
    columns_to_show = [
        'Master Box #',
        'UPC/EAN (GTIN)',
        'FNSKU',
        'Quantity',
        'Amazon Labels',
        'DONE'
    ]

    # Filter to only include columns that actually exist in the dataframe (safety check)
    available_cols = [col for col in columns_to_show if col in df_memory.columns]
    df_subset = df_memory[available_cols]

    # Convert the dataframe to a list of dictionaries so Jinja/HTML can easily read it
    table_data = df_subset.to_dict(orient='records')

    return render_template('view_data.html', table_data=table_data, columns=available_cols)



@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Gracefully shuts down the Flask server."""
    print("🛑 Shutting down server by user request...")
    # Sends a termination signal to the current process
    os.kill(os.getpid(), signal.SIGTERM)
    return jsonify({"status": "success", "message": "Server is shutting down. You can close this window."})

if __name__ == '__main__':
    app.run(debug=False)