import socket

# En zebra_print.py
def zebra_printer(fnsku, product_name, quantity, ip_impresora="192.168.1.100", puerto=9100):    
    """
    Se encarga exclusivamente de enviar comandos ZPL a una impresora Zebra en red.
    Garantiza calidad perfecta y tamaño exacto.
    """
    
    # El código ZPL. Los números como 50,50 son las coordenadas (X, Y).
    # Si sale muy arriba o muy a la izquierda en tu etiqueta, solo cambias esos números.
    codigo_zpl = f"""^XA
        ^FO50,50^BY3
        ^BCN,100,Y,N,N
        ^FD{fnsku}^FS
        ^FO50,180
        ^A0N,25,25
        ^FD{product_name[:40]}^FS
        ^FO50,210
        ^A0N,25,25
        ^FDNEW^FS
        ^PQ{quantity}
        ^XZ"""

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0) # Espera máximo 3 segundos para conectar
        
        # Conectamos a la IP y Puerto
        sock.connect((ip_impresora, puerto))
        sock.send(codigo_zpl.encode('utf-8'))
        sock.close()
        
        print(f"🖨️ Éxito: Orden enviada. La Zebra imprimirá {quantity} etiquetas de '{fnsku}'.")
        return True
        
    except socket.timeout:
        print(f"❌ Error: La impresora en la IP {ip_impresora} no responde. Revisa que esté encendida y en la misma red.")
        return False
    except Exception as e:
        print(f"❌ Error al intentar imprimir: {e}")
        return False