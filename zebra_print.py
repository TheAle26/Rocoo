import socket
import os

def get_printer_ip():
    """Reads the printer IP from a text file so non-tech users can change it easily."""
    try:
        # Looks for printer_ip.txt in the same folder as the app
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ip_file = os.path.join(base_dir, 'printer_ip.txt')
        with open(ip_file, 'r') as f:
            return f.read().strip()
    except Exception:
        return "192.168.1.100"  # Default fallback if the file is missing
    


def zebra_printer(fnsku, product_name, quantity, port=9100):    
    """
    Exclusively sends ZPL commands to a network Zebra printer.
    Ensures perfect quality, exact sizing, and prevents text cut-offs.
    The ^CI0,26,48 command removes the dot/slash from the zero.
    """
    printer_ip = get_printer_ip()  # Get the printer IP from the text file
    # ZPL code. 
    # ^CI0,26,48 maps the dotted zero to a clean zero.
    # ^FBwidth,lines,spaces,align,indent creates a text box to wrap long names.
    zpl_code = f"""^XA
    ^CI0,26,48
    ^FO30,30^BY3
    ^BCN,80,Y,N,N
    ^FD{fnsku}^FS
    ^FO30,140
    ^A0N,25,25
    ^FB500,2,0,L,0
    ^FD{product_name}^FS
    ^FO30,200
    ^A0N,25,25
    ^FDNew^FS
    ^PQ{quantity}
    ^XZ"""

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0) # Wait up to 3 seconds to connect
        
        # Connect to IP and Port
        sock.connect((printer_ip, port))
        sock.send(zpl_code.encode('utf-8'))
        sock.close()
        
        print(f"🖨️ Success: Order sent. The Zebra printer will print {quantity} labels of '{fnsku}'.")
        return True
        
    except socket.timeout:
        print(f"❌ Error: Printer at IP {printer_ip} is not responding. Check if it is turned on and on the same network.")
        return False
    except Exception as e:
        print(f"❌ Error attempting to print: {e}")
        return False