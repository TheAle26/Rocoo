from flask import Flask, request, render_template, jsonify, redirect, url_for
import os
import concurrent.futures
import pandas as pd
from big_box import build_upc_to_page_dictionary
from shoe_box import print_label , map_all_labels_in_pdf
from search_cvs import search_barcode

app = Flask(__name__, static_folder='static')
df_memory = None  
label_map = None
bix_box_map = None

# Define the path to the output folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')

if not os.path.exists(OUTPUT_FOLDER):
    try:
        os.makedirs(OUTPUT_FOLDER)
    except FileExistsError:
        pass

# fix names. the files are overwritten every time, so we can use the same name and just replace the old one. This way we don't have to worry about cleaning up old files.
CSV_FILENAME = 'actual_shipment.csv'
BOX_PDF_FILENAME = 'box_labels_actual_shipment.pdf'
SHOE_PDF_FILENAME = 'shoe_labels_actual_shipment.pdf'

last_row = 0 # global variable to keep track of the current row in the csv file, so we can print the big box label

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Corregido: usamos request.files para todos los archivos
        shipment = request.files.get('shipment')
        box_label_pdf = request.files.get('box_label_pdf') 
        shoe_label_pdf = request.files.get('shoe_label_pdf') 

        if shipment and box_label_pdf and shoe_label_pdf:
            # Al guardar con el mismo nombre, se pisa el archivo viejo automáticamente
            
            shipment.save(os.path.join(OUTPUT_FOLDER, CSV_FILENAME))
            box_label_pdf.save(os.path.join(OUTPUT_FOLDER, BOX_PDF_FILENAME))
            shoe_label_pdf.save(os.path.join(OUTPUT_FOLDER, SHOE_PDF_FILENAME))
            
            
            global df_memory
            path_csv = os.path.join(OUTPUT_FOLDER, CSV_FILENAME)
        
            if shipment.filename.endswith('.xlsx'):
                df_memory = pd.read_excel(path_csv, dtype=str)
            else:
                df_memory = pd.read_csv(path_csv, dtype=str)
                
            
            process_pdfs_concurrently(os.path.join(OUTPUT_FOLDER, SHOE_PDF_FILENAME), os.path.join(OUTPUT_FOLDER, BOX_PDF_FILENAME), df_memory)
            
            #old code
            # now we map all the labels in the shoe pdf to a dictionary, so we can access them by FNSKU when we need to print
            # global label_map
            # label_map = map_all_labels_in_pdf(os.path.join(OUTPUT_FOLDER, SHOE_PDF_FILENAME))
            
            # global bix_box_map
            # #the dictonary structure is {UPC: [Amazon Label, Page Number]} 
            # bix_box_map = build_upc_to_page_dictionary(os.path.join(OUTPUT_FOLDER, BOX_PDF_FILENAME),df_memory)
            
            # now we go to the procesing page
            return redirect(url_for('processing_page'))

    return render_template('index.html')

@app.route('/processing')
def processing_page():
    # just for rendering
    return render_template('processing.html')

@app.route('/scan', methods=['POST'])
def scan_barcode():
    
    data = request.get_json()
    barcode = data.get('barcode', '').strip()

    if not barcode:
        return jsonify({"status": "error", "message": "Empty code"}), 400


    global df_memory
    if df_memory is None:
        return jsonify({"status": "error", "message": "CVS fyle is not in memory"}), 400
    
    # now we search the barcode in the csv file
    resultado = search_barcode(barcode, df_memory)
    
    
    if resultado["status"] == "error":

        return jsonify({
            "status": "error",
            "message": resultado["message"]
        }), 404
    
    global last_row
    
    last_row = resultado["row"].index[0] # get the index of the row found
    
    # unpack the values that came from the other file
    FNSKU = resultado["FNSKU"]
    quantity = resultado["Quantity"]
    amazon_labels = resultado["Amazon Labels"]
    
    #for debugging
    print(f"FNSKU: {FNSKU}, Quantity: {quantity}")
    
    # now we print the labels
    
    path_shoe_pdf = os.path.join(OUTPUT_FOLDER, SHOE_PDF_FILENAME)
    
    
    product_name = label_map.get(FNSKU, "Unknown Product")
    # get the product name from the label map, if it doesn't exist we put "Unknown Product"
    try:
        # We attempt to print the labels
        print_label(FNSKU, quantity, product_name) 
        
        # If no exception is raised, it means the socket successfully sent the ZPL
        message = f"Found! Sent {quantity} label(s) to printer."
        
        return {
            "status": "success",
            "FNSKU": str(FNSKU), 
            "Quantity": int(quantity), 
            "Amazon Labels": str(amazon_labels),
            "Row": int(last_row), 
            "message": message
        }
        
    except Exception as e:
        # If the printer is disconnected or unreachable, it fails here
        print(f"Printer Error: {e}")
        return {
            "status": "error",
            "message": f"Item found, but printer is disconnected or unreachable."
        }, 500
    
    



def print_amazon_labels(amazon_label):
    # codigo para imprimir amazon labels
    # ---------------------------------------------------------
    return 20


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



if __name__ == '__main__':
    app.run(debug=True)