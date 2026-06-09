from flask import Flask, request, render_template, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import io
import os
import uuid


app = Flask(__name__, static_folder='static')

# Define the path to the output folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')

# Ensure the output folder exists
if not os.path.exists(OUTPUT_FOLDER):
    try:
        os.makedirs(OUTPUT_FOLDER)
    except FileExistsError:
        pass  # Directory already exists


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the file and user inputs
        shipment = request.files.get('shipment')
        box_label_pdf = request.form.get('box_label_pdf')  # Salesperson
        shoe_label_pdf = request.form.get('shoe_label_pdf')  # Team ID

        if shipment and shipment.filename and box_label_pdf and shoe_label_pdf:
            # Save uploaded file with a unique name
           
            # Redirect to the processing page with filename and form data
            return redirect(url_for('processing_page', shipment=shipment, box_label_pdf=box_label_pdf, shoe_label_pdf=shoe_label_pdf))

    return render_template('index.html')



@app.route('/processing')
def processing_page():
    filename = request.args.get('filename')
    box_label_pdf = request.args.get('box_label_pdf')
    shoe_label_pdf = request.args.get('shoe_label_pdf')



    # Here you could add processing logic (parsing, generating labels, etc.)
    # For now, render a download page with the uploaded filename and metadata
    return render_template('processing.html')

if __name__ == '__main__':    app.run(debug=True)