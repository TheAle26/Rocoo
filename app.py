from flask import Flask, request, render_template, jsonify, redirect, url_for
import os
import pandas as pd

app = Flask(__name__, static_folder='static')

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
            
            # Redirigimos a la página de procesamiento
            return redirect(url_for('processing_page'))

    return render_template('index.html')

@app.route('/processing')
def processing_page():
    # Solo renderizamos la vista. El escáner se comunicará por AJAX.
    return render_template('processing.html')

@app.route('/scan', methods=['POST'])
def scan_barcode():
    # Esta ruta recibe el código escaneado desde el frontend
    data = request.get_json()
    barcode = data.get('barcode', '').strip()

    if not barcode:
        return jsonify({"status": "error", "message": "Código vacío"}), 400

    # ---------------------------------------------------------
    # # codigo para buscar en pandas (usando shipment_actual.csv)
    # # codigo para imprimir fnsku / box label
    # ---------------------------------------------------------

    # De momento devolvemos un éxito simulado para probar la interfaz
    return jsonify({
        "status": "success",
        "barcode": barcode,
        "message": f"Código {barcode} recibido correctamente."
    })
    
    
def search_barcode(barcode):
    UPC = barcode
    # leer shipment_actual.csv
    df = pd.read_csv(CSV_FILENAME)
    # codigo para buscar en pandas (usando shipment_actual.csv)
    # buscar FNSKU y Quantity
    FNSKU = df[df['UPC'] == UPC]['FNSKU'].values[0]
    Quantity = df[df['UPC'] == UPC]['Quantity'].values[0]
    # buscar Amazon Labels
    #la amazon label se imprime solo si toca el boton de opcion de imprimir amazon labels en la interfaz
    amazon_labels = df[df['UPC'] == UPC]['Amazon Labels'].values[0]
    # imprimir FNSKU y Quantity para chekear que se haya encontrado
    print(f"FNSKU: {FNSKU}, Quantity: {Quantity}")
    print("---------------------------------------------------------")
    
    #para mandar a la impresora hay que buscar en el pdf el barcode
    print_label(FNSKU, Quantity) 
    # ---------------------------------------------------------
    return barcode

def print_label(FNSKU, quantity):
    # codigo para imprime en al zebra. para eso hay que buscar en el pdf el barcode
    # ---------------------------------------------------------
    return 

def print_amazon_labels(amazon_label):
    # codigo para imprimir amazon labels
    # ---------------------------------------------------------
    return 20



if __name__ == '__main__':
    app.run(debug=True)