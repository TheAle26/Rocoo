import PyPDF2
import re
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
from zebra_print import zebra_printer


def print_label(FNSKU, quantity, product_name):
    
    output_filename = f"current_label"
    
    if product_name:
        save_label_as_picture(FNSKU, product_name, output_filename)
        zebra_printer(FNSKU, product_name,quantity)

    else:
        print(f"❌ FNSKU '{FNSKU}' not found in the PDF.")


def map_all_labels_in_pdf(pdf_path):
    """
    Reads the PDF ONCE and creates a dictionary of {FNSKU: Product Name}.
    This is hundreds of times faster if you need to look up multiple codes.
    """
    # Regex to find ANY standard FNSKU (they start with X and are usually 10 chars)
    # and capture the name beneath it.
    pattern = re.compile(r'(X[A-Z0-9]{9})\s*\n(.*?)(?=\n\s*New)', re.DOTALL)
    
    label_map = {}
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            print(f"Scanning {len(reader.pages)} pages...")
            
            for page in reader.pages:
                text = page.extract_text()
                
                # finditer gets EVERY match on the page, not just the first one
                matches = pattern.finditer(text)
                
                for match in matches:
                    fnsku = match.group(1)
                    product_name = match.group(2).replace('\n', ' ').strip()
                    
                    # Add to our dictionary
                    if fnsku not in label_map:
                        label_map[fnsku] = product_name
                        
        print(f"✅ Successfully mapped {len(label_map)} unique FNSKUs.")
        return label_map
        
    except FileNotFoundError:
        print(f"Error: The file '{pdf_path}' was not found.")
        return {}
    

# def find_fnsku_in_pdf(FNSKU, pdf_path):
#     """
#     Looks up the FNSKU in the PDF and returns the product name.
#     """
#     try:
#         with open(pdf_path, 'rb') as file:
#             reader = PyPDF2.PdfReader(file)
            
#             for page_num, page in enumerate(reader.pages):
#                 text = page.extract_text()
                
#                 # Regex looks for the FNSKU, captures everything until the word "New"
#                 pattern = re.compile(re.escape(FNSKU) + r'\s*\n(.*?)(?=\n\s*New)', re.DOTALL)
#                 match = pattern.search(text)
                
#                 if match:
#                     # Clean up the text (remove extra line breaks)
#                     product_name = match.group(1).replace('\n', ' ').strip()
#                     print(f"✅ Found '{FNSKU}' -> {product_name}")
#                     return product_name
                    
#         print(f"❌ FNSKU '{FNSKU}' not found in the PDF.")
#         return None
        
#     except FileNotFoundError:
#         print(f"Error: The file '{pdf_path}' was not found.")
#         return None
    

def save_label_as_picture(FNSKU, product_name, output_filename="label"):
    """
    Method 1: Generates a PNG image with the barcode and the product name underneath.
    """
    try:
        # 1. Generate the Code 128 barcode
        code128 = barcode.get_barcode_class('code128')
        bc = code128(FNSKU, writer=ImageWriter())
        
        # Save the initial barcode (it automatically appends .png)
        filename = bc.save(output_filename)
        
        # 2. Open the image to add the product name
        img = Image.open(filename)
        width, height = img.size
        
        # Create a new, taller image to fit the text at the bottom
        text_space = 60
        new_img = Image.new('RGB', (width, height + text_space), 'white')
        new_img.paste(img, (0, 0))
        
        # 3. Draw the product name
        draw = ImageDraw.Draw(new_img)
        try:
            # Cambia '20' para hacer el texto más grande o pequeño
            font = ImageFont.truetype("arial.ttf", 20) 
        except IOError:
            print("Arial font not found, falling back to default.")
            font = ImageFont.load_default()
        
        # Truncate text if it's too long for the image width
        display_text = product_name[:60] + "..." if len(product_name) > 60 else product_name
        
        # Calculamos las posiciones verticales (Y)
        # 'height' es donde termina el código de barras original
        posicion_y_nombre = height + 5   # Justo debajo del código de barras
        posicion_y_new = height + 35     # Un poco más abajo para dar espacio a la primera línea
        
        # Dibujamos el nombre del producto
        draw.text((10, posicion_y_nombre), display_text, fill="black", font=font)
        
        # Dibujamos la palabra "NEW" debajo
        draw.text((10, posicion_y_new), "NEW", fill="black", font=font)
        
        # Save the final image
        new_img.save(filename)
        print(f"✅ Picture successfully saved as: {filename}")
        
    except Exception as e:
        print(f"❌ Error generating picture: {e}")