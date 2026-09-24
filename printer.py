import win32print
import win32ui
from PIL import Image, ImageWin
import time
import json
import os
import fitz  # This is PyMuPDF



# GetDeviceCaps indices from wingdi.h: the size of the printable area in
# device units. A printer DC's origin is already the top-left of that area,
# so nothing needs to be offset by the physical margin.
HORZRES = 8
VERTRES = 10


class PrinterConfigError(RuntimeError):
    """Raised when printers.json is missing or does not name a real printer."""


# Text carried by the untouched entries in printers.example.json.
PLACEHOLDER_MARKER = "PUT THE EXACT WINDOWS NAME"


def get_printer_names():
    """Reads the exact printer names from the JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'printers.json')

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise PrinterConfigError(
            "printers.json is missing on this PC. Copy printers.example.json to "
            "printers.json and fill in the two printer names."
        )
    except json.JSONDecodeError as e:
        raise PrinterConfigError(f"printers.json is not valid JSON ({e}).")


def resolve_printer_name(printer_type):
    """
    Returns the Windows printer name configured for 'shoe_printer' or
    'big_box_printer'.

    A missing or placeholder entry is a hard error. Falling back to the Windows
    default printer would send labels to whatever device happens to be default,
    which is worse than not printing at all.
    """
    printer_name = get_printer_names().get(printer_type)

    if not printer_name or PLACEHOLDER_MARKER in printer_name:
        raise PrinterConfigError(
            f"printers.json does not name a printer for '{printer_type}'. "
            "Fill it in with the exact name from the Windows printer list."
        )

    installed = {
        p[2] for p in win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
    }
    if printer_name not in installed:
        raise PrinterConfigError(
            f"'{printer_name}' (configured as {printer_type}) is not installed on "
            f"this PC. Installed printers: {', '.join(sorted(installed)) or 'none'}."
        )

    return printer_name

def fit_rect(image_size, printable_size):
    """
    Largest rectangle keeping the label's proportions inside the printable
    area, centred.

    Drawing straight to (0, 0, HORZRES, VERTRES) stretches the label to the
    shape of whatever media is loaded, and stretches the barcode with it. A
    barcode read by a scanner has to keep its bar widths in proportion.
    """
    img_w, img_h = image_size
    area_w, area_h = printable_size

    if img_w <= 0 or img_h <= 0 or area_w <= 0 or area_h <= 0:
        return (0, 0, area_w, area_h)

    scale = min(area_w / img_w, area_h / img_h)
    draw_w = max(1, int(img_w * scale))
    draw_h = max(1, int(img_h * scale))
    left = (area_w - draw_w) // 2
    top = (area_h - draw_h) // 2

    return (left, top, left + draw_w, top + draw_h)


def print_image_to_printer(image_path, quantity, printer_type="shoe_printer"):
    """
    Silently sends a saved image directly to a specific Windows printer based on its type.
    """
    # 1. Resolve the printer before the try block, so a configuration problem
    # reaches the UI as a clear message instead of being flattened into "False".
    printer_name = resolve_printer_name(printer_type)
    print(f"🖨️ Connecting to {printer_type}: '{printer_name}'")

    try:
        # 3. Open the PNG label you generated
        img = Image.open(image_path)
        img = img.convert('L') # Pure black & white
        
        # 4. Send to printer 'quantity' times
        for _ in range(quantity):
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)
            
            printable_area = hDC.GetDeviceCaps(HORZRES), hDC.GetDeviceCaps(VERTRES)
            target = fit_rect(img.size, printable_area)

            hDC.StartDoc(image_path)
            hDC.StartPage()

            dib = ImageWin.Dib(img)
            dib.draw(hDC.GetHandleOutput(), target)

            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()
            
            time.sleep(0.2) 
            
        print(f"✅ Successfully printed {quantity} labels to {printer_name}!")
        return True
        
    except Exception as e:
        print(f"❌ Windows Printer Error on '{printer_name}': {e}")
        return False

# --- HELPER FUNCTION FOR WORKERS ---
def list_available_printers():
    """Workers can run this to see what to type into printers.json."""
    print("\n--- AVAILABLE WINDOWS PRINTERS ---")
    printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
    for p in printers:
        print(f'"{p[2]}"')
    print("----------------------------------\n")
    
    


def print_amazon_label(pdf_path, page_num):
    """
    Extracts a single page from the Big Box PDF, converts it to a crisp PNG, 
    and sends it to the dedicated Big Box thermal printer.
    """
    output_filename = "current_big_box_label.png"
    
    try:
        # 1. Open the PDF file
        doc = fitz.open(pdf_path)
        
        # 2. Go to the exact page (PyMuPDF uses 0-based indexing, just like your dictionary!)
        page = doc.load_page(page_num)
        
        # 3. Render the page as an image. 
        # dpi=300 ensures the barcodes are razor sharp for the thermal printer.
        pix = page.get_pixmap(dpi=300)
        
        # 4. Save the image to the disk
        pix.save(output_filename)
        doc.close()
        
        print(f"✅ Successfully extracted Page {page_num + 1} to {output_filename}")
        
        # 5. Send it to the Windows print spooler!
        # Notice we are explicitly targeting the "big_box_printer" from your JSON config
        success = print_image_to_printer(output_filename, quantity=1, printer_type="big_box_printer")
        
        if not success:
            raise Exception("Windows Spooler failed to print the image.")
            
    except Exception as e:
        print(f"❌ Error extracting and printing Big Box label: {e}")
        raise e  # Re-raise so app.py can catch it and show the error on the UI