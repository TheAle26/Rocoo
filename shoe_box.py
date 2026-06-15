import PyPDF2
import re
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import textwrap
from zebra_print import zebra_printer
from printer import print_image_to_printer



def print_label(FNSKU, quantity, product_name):
    
    output_filename = f"current_label"
    
    if product_name:
        save_label_as_picture(FNSKU, product_name, output_filename)
        print(f"Shoe box label generated for FNSKU: {FNSKU}, Product: {product_name}, Quantity: {quantity}")
        #zebra_printer(FNSKU, product_name,quantity)
        filename = f"{output_filename}.png"
        print_image_to_printer(filename, quantity, printer_type="shoe_printer")

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
    

def save_label_as_picture(fnsku, product_name, output_filename="label"):
    """
    Generates a PNG image matching the Amazon PDF layout.
    Keeps the product name on a single line and uses middle-truncation 
    for very long names, exactly like the provided PDF.
    """
    try:
        # 1. Replicate Amazon's middle-truncation rule
        # Reduced max_chars slightly to 42 because the font is now bigger
        max_chars = 42 
        if len(product_name) > max_chars:
            keep_front = 20
            keep_back = max_chars - keep_front - 3 
            display_text = product_name[:keep_front] + "..." + product_name[-keep_back:]
        else:
            display_text = product_name

        # 2. Generate the Code 128 barcode
        writer_options = {
            'module_width': 0.25,  
            'module_height': 12.0,
            'font_size': 10,
            'text_distance': 4.0,
            'font_path': 'arial.ttf' # <-- THIS REMOVES THE DOTTED ZERO
        }
        
        code128 = barcode.get_barcode_class('code128')
        bc = code128(fnsku, writer=ImageWriter())
        
        # Save the initial barcode (it automatically appends .png)
        filename = bc.save(output_filename, options=writer_options)
        
        # 3. Open the image to add the product name
        img = Image.open(filename)
        width, height = img.size
        
        # Create a new, taller image to fit the larger text
        extra_height = 60 # <-- Increased from 45 to give the bigger text more room
        new_img = Image.new('RGB', (width, height + extra_height), 'white')
        new_img.paste(img, (0, 0))
        
        # 4. Draw the text
        draw = ImageDraw.Draw(new_img)
        try:
            # <-- Increased font size from 20 to 24
            font = ImageFont.truetype("arial.ttf", 24) 
        except IOError:
            print("Arial font not found, falling back to default.")
            font = ImageFont.load_default()
        
        # Draw the single-line product name directly below the barcode
        pos_y_name = height + 2
        draw.text((10, pos_y_name), display_text, fill="black", font=font)
        
        # Draw "New" directly below the product name
        pos_y_new = pos_y_name + 26 # <-- Increased from 20 to account for taller letters
        draw.text((10, pos_y_new), "New", fill="black", font=font)
        
        # Save the final image
        new_img.save(filename)
        print(f"✅ Picture successfully saved as: {filename}")
        
    except Exception as e:
        print(f"❌ Error generating picture: {e}")
        
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
    