from flask import Flask, request, render_template, jsonify, redirect, url_for
import os
import pandas as pd

from shoe_box import print_label
from search_cvs import search_barcode

app = Flask(__name__, static_folder='static')
df_memory = None  
# Define the path to the output folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')

if not os.path.exists(OUTPUT_FOLDER):
    try:
        os.makedirs(OUTPUT_FOLDER)
    except FileExistsError:
        pass

# Nombres fijos para que se sobreescriban siempre y no ocupen espacio extra
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
            
            # now we go to the procesing page
            return redirect(url_for('processing_page'))

    return render_template('index.html')

@app.route('/processing')
def processing_page():
    # Solo renderizamos la vista. El escáner se comunicará por AJAX.
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
    path_box_pdf = os.path.join(OUTPUT_FOLDER, BOX_PDF_FILENAME)
    path_shoe_pdf = os.path.join(OUTPUT_FOLDER, SHOE_PDF_FILENAME)
    
    try:
        # We attempt to print the labels
        print_label(FNSKU, quantity, path_shoe_pdf) 
        
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



if __name__ == '__main__':
    app.run(debug=True)