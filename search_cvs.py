import pandas as pd

def search_barcode(UPC, df):
    
    row = df[df['UPC/EAN (GTIN)'] == UPC]
    
    if row.empty:
        print(f"Error: UPC {UPC} does not exist in file.")
        return {
            "status": "error",
            "message": f"UPC {UPC} not found."
        }
    
    FNSKU = row['FNSKU'].values[0]
    

    Quantity = row['Quantity'].values[0] 
    
    amazon_labels = row['Amazon Labels'].values[0]
    
    print(f"✔️ Encontrado: FNSKU: {FNSKU}, Cantidad: {Quantity}")
    print("---------------------------------------------------------")
    
    # Devolvemos el éxito
    return {
        "status": "success",
        "FNSKU": FNSKU,
        "Quantity": int(float(Quantity)), # Convertimos a entero seguro
        "Amazon Labels": amazon_labels,
        "row":row
    }