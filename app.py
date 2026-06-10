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
CSV_FILENAME = 'shipment_actual.csv'
BOX_PDF_FILENAME = 'box_labels_actual.pdf'
SHOE_PDF_FILENAME = 'shoe_labels_actual.pdf'

last_row = 0 # Variable global para llevar el conteo de la fila actual en shipment_actual.csv

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
            df_memory = pd.read_csv(path_csv, dtype=str)
            
            # Redirigimos a la página de procesamiento
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
    
    # Le pasamos la ruta completa a la función, en lugar de solo el nombre
    resultado = search_barcode(barcode, df_memory)
    
    
    if resultado["status"] == "error":

        return jsonify({
            "status": "error",
            "message": resultado["message"]
        }), 404
    
    global last_row
    
    last_row = resultado["row"].index[0] # Obtenemos el índice de la fila encontrada
    
    # Desempaquetamos los valores que vinieron del otro archivo
    FNSKU = resultado["FNSKU"]
    quantity = resultado["Quantity"]
    amazon_labels = resultado["Amazon Labels"]
    
    print(f"FNSKU: {FNSKU}, Quantity: {quantity}")
    
    # Mandamos a imprimir
    print_label(FNSKU, quantity) 
    message = f"There are {quantity} labels to print." if quantity > 1 else "There is 1 label to print."
    return {
        "status": "success",
        "FNSKU": str(FNSKU), # Forzamos a que sea texto
        "Quantity": int(quantity), # Forzamos a entero de Python
        "Amazon Labels": str(amazon_labels),
        "Row": int(last_row), # Forzamos a entero de Python
        "message": message
    }
    
    



def print_amazon_labels(amazon_label):
    # codigo para imprimir amazon labels
    # ---------------------------------------------------------
    return 20



if __name__ == '__main__':
    app.run(debug=True)