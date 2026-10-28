import PyPDF2
import re
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import textwrap
from zebra_print import zebra_printer
from printer import print_image_to_printer


# Text sizes (in label pixels) offered by the "Label text" picker on the scan page.
LABEL_FONT_SIZES = range(16, 33, 2)
DEFAULT_LABEL_FONT_SIZE = 24
# The label has room for this many lines of product name under the barcode.
MAX_NAME_LINES = 3


def print_label(FNSKU, quantity, product_name, font_size=DEFAULT_LABEL_FONT_SIZE):
    
    output_filename = f"current_label"
    
    if product_name:
        save_label_as_picture(FNSKU, product_name, output_filename, font_size)
        print(f"Shoe box label generated for FNSKU: {FNSKU}, Product: {product_name}, Quantity: {quantity}")
        #zebra_printer(FNSKU, product_name,quantity)
        filename = f"{output_filename}.png"
        success = print_image_to_printer(filename, quantity, printer_type="shoe_printer")
        if not success:
            raise RuntimeError("Windows Spooler failed to print the shoe label.")

        return True

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
    

def _cut_middle(text, room, font):
    """
    Cuts text from the middle with "..." until it fits in `room` pixels,
    keeping as much of the end as possible, because that's where the size
    usually is.
    """
    front = int(len(text) * 0.4)
    back = len(text) - front
    while front > 0 or back > 0:
        cut = text[:front] + "..." + (text[-back:] if back else "")
        if font.getlength(cut) <= room:
            return cut
        # Drop characters next to the "..." - from the front first, so the
        # end of the name survives longest.
        if front >= back // 2 and front > 0:
            front -= 1
        else:
            back -= 1
    return "..."


def wrap_name(name, room, font):
    """
    Splits the product name into lines of at most `room` pixels, breaking
    between words (a single word wider than a line is broken by characters).

    Uses up to MAX_NAME_LINES lines. If the name needs more, the last line
    holds the rest of it cut from the middle, so the size at the end still
    shows.
    """
    lines = []
    line = ""
    words = name.split()
    while words:
        word = words[0]
        candidate = f"{line} {word}" if line else word
        if font.getlength(candidate) <= room:
            line = candidate
            words.pop(0)
        elif line:
            lines.append(line)
            line = ""
        else:
            # One word wider than the whole line: take what fits of it.
            fit = 1
            while fit < len(word) and font.getlength(word[:fit + 1]) <= room:
                fit += 1
            lines.append(word[:fit])
            words[0] = word[fit:]
    if line:
        lines.append(line)

    if len(lines) > MAX_NAME_LINES:
        rest = " ".join(lines[MAX_NAME_LINES - 1:])
        lines = lines[:MAX_NAME_LINES - 1] + [_cut_middle(rest, room, font)]
    return lines or [""]


def save_label_as_picture(fnsku, product_name, output_filename="label",
                          font_size=DEFAULT_LABEL_FONT_SIZE):
    """
    Generates a PNG image matching the Amazon PDF layout.
    The product name is written at `font_size` on up to MAX_NAME_LINES
    lines; see wrap_name for how a long name is made to fit.
    """
    try:
        # 1. Generate the Code 128 barcode
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

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            print("Arial font not found, falling back to default.")
            font = ImageFont.load_default()
        # 10px margin each side.
        lines = wrap_name(product_name, width - 20, font)
        line_height = font_size + 4

        # Create a new, taller image with room for the name lines and "New"
        extra_height = (len(lines) + 1) * line_height + 6
        new_img = Image.new('RGB', (width, height + extra_height), 'white')
        new_img.paste(img, (0, 0))
        
        # 4. Draw the product name directly below the barcode, then "New"
        # below its last line
        draw = ImageDraw.Draw(new_img)
        pos_y = height + 2
        for text in lines + ["New"]:
            draw.text((10, pos_y), text, fill="black", font=font)
            pos_y += line_height
        
        # Save the final image
        new_img.save(filename)
        print(f"✅ Picture successfully saved as: {filename}")
        
    except Exception as e:
        print(f"❌ Error generating picture: {e}")
        # Re-raise so print_label does NOT send a stale current_label.png
        # (left over from a previous product) to the printer.
        raise
        
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
