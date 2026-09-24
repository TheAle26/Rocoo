# Contexto para la IA: Shipping Tool (Rocco)

> **Para quien usa esto:** pegá este archivo entero en el chat de tu IA (Claude, ChatGPT, etc.) y después contale qué te pasa. Tiene todo lo necesario para que te explique cómo instalar, usar y arreglar el programa.

---

## Instrucciones para la IA

Vas a ayudar a una persona **no técnica** a instalar y usar un programa de etiquetado de envíos de Amazon en una PC con Windows. Reglas:

1. Explicá **paso a paso, en español**, un paso por vez, y esperá a que la persona confirme antes de seguir.
2. Cuando des un comando, aclarale **dónde escribirlo** (PowerShell, o la ventana negra) y pedile que te copie lo que aparece.
3. **Nunca** le hagas borrar ni sobrescribir la carpeta `output\`, que es donde está el avance del envío, ni el archivo `printers.json`, sin hacer antes una copia.
4. **Nunca** le hagas ejecutar `git reset --hard`, `git clean` ni `git push`, ni modificar archivos `.py`, `.html` o `.bat`. Si hace falta cambiar el programa, que avise a **Alejo**, el dueño del programa.
5. Si algo no está en este documento, decilo y sugerí preguntarle a Alejo en vez de adivinar.

---

## Qué es el programa

Es una aplicación web chica que corre **en la misma PC**: se abre en el navegador en `http://127.0.0.1:5000` y no está en internet. Sirve para etiquetar un envío de cajas que va a Amazon (FBA):

- El operario **escanea o escribe** un código.
- El programa muestra en qué **caja grande (master box)** va ese producto.
- Desde ahí se imprimen dos etiquetas:
  - **Shoes (N):** N etiquetas FNSKU chicas, una por par.
  - **Big Box:** la etiqueta de Amazon 4x6 de la caja grande.
- Al terminar una caja se aprieta **Mark Done** y el avance queda guardado.

Datos técnicos:

- Está hecho en Python 3.13 con Flask y se sirve con `waitress`.
- Imprime por la cola de impresión de Windows con `pywin32`.
- Lee PDFs con PyPDF2 y PyMuPDF, y genera códigos de barras con `python-barcode` y Pillow.

---

## Instalación en una PC nueva

**Requisitos:**

- Windows 10 u 11 con internet.
- Una cuenta de GitHub invitada al repositorio **privado** `https://github.com/TheAle26/Rocoo`. La invitación la manda Alejo y se acepta desde el mail.
- Las dos impresoras de etiquetas instaladas en Windows:
  - la de etiquetas chicas de los pares;
  - la de etiquetas 4x6 de las cajas.
- Una pistola lectora de códigos USB. Funciona como un teclado: escribe el código y aprieta Enter.

**Pasos:**

1. **Instalar Python 3.13** desde https://www.python.org/downloads/windows/.
   - Usar la **3.13**, no una versión más nueva: algunas librerías fijadas en el programa podrían no estar disponibles para versiones posteriores.
   - En la primera pantalla del instalador **tildar "Add python.exe to PATH"**.
   - Para comprobarlo, en PowerShell: `python --version` tiene que decir `Python 3.13.x`.
2. **Instalar Git** desde https://git-scm.com/download/win, con todas las opciones por defecto. Para comprobarlo: `git --version`.
3. **Bajar el programa.** En PowerShell:
   ```
   git clone https://github.com/TheAle26/Rocoo.git C:\ShippingTool
   ```
   Se abre el navegador para iniciar sesión en GitHub; hay que aceptar. La sesión queda guardada.
4. **Configurar las impresoras.**
   - Ver los nombres exactos, en PowerShell:
     ```
     Get-Printer | Select-Object Name
     ```
   - Abrir `C:\ShippingTool\printers.json` con el Bloc de notas. Si no existe, copiar `printers.example.json` y renombrar la copia a `printers.json`.
   - Dejarlo así, con los nombres **copiados exactos**:
     ```json
     {
       "shoe_printer": "NOMBRE EXACTO de la impresora de etiquetas chicas",
       "big_box_printer": "NOMBRE EXACTO de la impresora de 4x6"
     }
     ```
   - Hay que respetar las comillas, los dos puntos y la coma.
5. **Primer arranque.** Doble clic en `C:\ShippingTool\start_app.bat`.
   - La primera vez tarda unos minutos, porque crea la carpeta `venv` e instala las librerías.
   - Después se abre el navegador solo.
   - Si Windows pregunta por el **Firewall**, apretar **Cancelar**: el programa solo lo usa esta PC.
6. **Acceso directo.** Clic derecho en `start_app.bat` > Enviar a > Escritorio (crear acceso directo).

---

## Uso diario

**Arrancar:** doble clic en `start_app.bat`.

- Se abre una ventana negra. **No hay que cerrarla** mientras se trabaja.
- Si el navegador dice "no se puede acceder", esperar unos segundos y apretar F5.

**Cargar un envío nuevo (solo la primera vez de cada envío):** en la pantalla de inicio subir 3 archivos y apretar **Upload & Process**:

| Casillero | Qué va |
|---|---|
| 1. Shipment Data | la planilla del envío (`.csv` o `.xlsx`) |
| Big Box Label | el PDF de Amazon con las etiquetas 4x6 de las cajas |
| Small Box Label | el PDF con las etiquetas FNSKU de los pares |

**Trabajar:**

1. Escanear o escribir el código en el recuadro grande y apretar Enter.
2. Aparecen las cajas. En cada una:
   - **Shoes (N)** imprime las etiquetas de los pares;
   - **Big Box** imprime la etiqueta de la caja;
   - **Mark Done** marca la caja como terminada.
3. **View Data** muestra la tabla completa. **Download (CSV)** baja la planilla con las cajas marcadas.

**Apagar:** botón rojo **Shut down**, arriba a la derecha. No cerrar la ventana negra con la X.

### MUY IMPORTANTE: retomar un envío

Si se cerró el programa o se reinició la PC, al volver a abrirlo apretar **Continue Work**. **No volver a subir los archivos:**

- En la versión **vieja**, subirlos de nuevo **borra todo el avance** (todas las cajas vuelven a "no terminada") sin avisar.
- En la versión **nueva**, el programa avisa antes y retoma el envío solo.

Para saber qué versión se está usando, mirar la pantalla de escaneo:

- si arriba a la izquierda dice **"Back to Home"**, es la **vieja**;
- si dice **"Start a new shipment"** y muestra "X of Y done", es la **nueva**.

---

## Envío Birkenstock FBA19QHGWM04 (AGLMIA225, 6.747 pares)

**Archivos**, que no están en GitHub: se pasan por pendrive, Drive o WhatsApp.

- Planilla: `Birkenstock FBA19QHGWM04 - para la app.csv`. Es una versión adaptada del packing list de AGL; el original no sirve tal cual en el programa.
- Etiquetas de pares: `Birkenstock FBA19QHGWM04 - etiquetas FNSKU (generado).pdf`. Lo generó Alejo con los datos de la planilla. Si AGL manda el oficial, usar ese.
- Etiquetas de cajas: el PDF 4x6 de Amazon que manda AGL. Son 586 etiquetas, de `FBA19QHGWM04U000001` a `U000586`.

**Cómo se trabaja:**

- Cada caja grande tiene escrito a mano un **número de referencia de 6 cifras** (por ejemplo `453909`); muchas cajas comparten la misma referencia.
- Cada caja tiene además una **etiqueta chica con su número de box** (1, 2, 3…).
- El código de barras del tipo `P0468` que tienen algunas cajas **no se usa**.

**Pasos:**

1. Escribir la referencia (`453909`) y apretar Enter.
2. Aparece la lista: "Box 1 - ARIZONA EVA WHITE 37", "Box 2 - …", etc.
3. Buscar la fila con el número de la etiqueta chica e imprimir desde ahí.

Algunas cajas tienen más de un producto adentro; en ese caso aparecen varias filas con el mismo número de box, y cada una tiene su propia etiqueta de Amazon.

**Filas "SET ASIDE (NO VA A AMAZON)":** esas cajas **no se etiquetan ni se envían**, se quedan en la bodega. Si se aprieta imprimir en una de ellas, da error, y está bien que sea así.

Totales:

| Destino | Pares | Cajas / líneas |
|---|---|---|
| Amazon | 6.223 | 586 etiquetas de caja |
| Set aside | 524 | 58 líneas |
| Total | 6.747 | 27 referencias |

En la planilla, la columna `UPC/EAN (GTIN)` contiene en realidad la **referencia de la caja grande**, a propósito, para poder buscar por ella. Los UPC y EAN reales de los productos están en las columnas `UPC` y `EAN`.

---

## Problemas comunes

| Qué pasa | Qué hacer |
|---|---|
| La ventana negra dice "Python is not installed" | Reinstalar Python 3.13 tildando "Add python.exe to PATH" y reiniciar la PC. |
| El navegador dice "no se puede acceder a este sitio" | Esperar 5 segundos y apretar F5. Si sigue, fijarse que la ventana negra esté abierta y sin errores. |
| Imprime en otra impresora, o da error de impresora | Revisar que los nombres de `printers.json` sean **exactamente** los de `Get-Printer`. En la versión vieja, si un nombre queda vacío, imprime en la impresora predeterminada de Windows sin avisar; si está mal escrito, da error. |
| La etiqueta sale estirada o cortada | En Windows: Configuración > Impresoras > (la impresora) > Preferencias de impresión, y poner el tamaño de papel correcto: 4x6 para las cajas y el tamaño de la etiqueta para los pares. |
| "UPC … not found" / "No match" | Revisar el número escrito. Con Birkenstock se busca por la **referencia de la caja grande** (6 cifras). Comprobar que esté cargada la planilla correcta en View Data. |
| "Page for label … not found" | Esa etiqueta de caja no está en el PDF 4x6 que se subió, o es una fila SET ASIDE. |
| "FNSKU … not found in PDF" | El PDF de etiquetas chicas no tiene ese producto. Revisar que sea el PDF de este envío. |
| "No previous session found" al apretar Continue Work | No hay ningún envío cargado todavía: hay que subir los 3 archivos. |
| Se cerró la ventana negra sin querer | Abrir `start_app.bat` de nuevo y apretar **Continue Work**. No volver a subir los archivos. |
| La pistola no hace nada | Hacer clic dentro del recuadro "Shoot barcode here…" y volver a escanear. La pistola tiene que estar configurada para terminar con Enter. |

### Actualizaciones

`start_app.bat` baja solo la última versión de GitHub cada vez que se abre (`git pull origin main`).

Cuando Alejo publique la versión nueva, ese `git pull` **puede fallar en esta PC**. Pasa porque en la versión vieja los archivos `printers.json`, `current_label.png` y `current_big_box_label.png` estaban dentro de git, y en esta PC ya fueron modificados. Se ve en la ventana negra con un mensaje parecido a *"Your local changes to the following files would be overwritten by merge"*.

Arreglo de una sola vez, en PowerShell, desde `C:\ShippingTool`:

```
cd C:\ShippingTool
copy printers.json printers.json.bak
git checkout -- printers.json current_label.png current_big_box_label.png
git pull origin main
copy printers.json.bak printers.json
```

El último paso es importante: la versión nueva ya no trae `printers.json` y usa la copia local de cada PC. Después de esto las actualizaciones vuelven a andar solas. Si el mensaje de error es otro, copiarlo entero y mandárselo a Alejo.

**Comandos de diagnóstico seguros**, solo leen y no cambian nada:

```
cd C:\ShippingTool
git status
git log --oneline -5
python --version
Get-Printer | Select-Object Name
```

---

## Mapa de archivos (para la IA)

| Archivo / carpeta | Qué es |
|---|---|
| `start_app.bat` | Arranca todo: comprueba Python, crea `venv` la primera vez, hace `git pull`, instala `requirements.txt`, abre el navegador y levanta `waitress-serve --port=5000 app:app`. |
| `app.py` | Servidor Flask. Rutas: `/` (subir archivos o Continue Work), `/processing` (pantalla de escaneo), `/scan`, `/print_shoes`, `/print_big_box`, `/mark_done`, `/view_data`, `/download_csv`, `/shutdown`. |
| `search_cvs.py` | Arma los índices de búsqueda desde la planilla y busca las páginas de cada etiqueta en el PDF de cajas. |
| `shoe_box.py` | Lee el PDF de etiquetas FNSKU (patrón: FNSKU, nombre del producto, "New") y dibuja la etiqueta de cada par. |
| `printer.py` | Imprime por la cola de Windows y extrae la página del PDF de cajas. Lee `printers.json`. |
| `printers.json` | Nombres de las 2 impresoras de **esta** PC. |
| `output\` | El envío en curso: `actual_shipment.csv` (con la columna DONE) y los 2 PDFs. **No borrar.** Se reescribe cada vez que se aprieta Mark Done. |
| `venv\` | Las librerías de Python. Si se rompe, se puede borrar: `start_app.bat` la vuelve a crear. |

Columnas que el programa espera en la planilla: `UPC/EAN (GTIN)`, `Master Box #`, `Quantity`, `FNSKU`, `Amazon Labels`. La columna `DONE` la agrega sola. La primera fila tiene que ser la de los encabezados.
