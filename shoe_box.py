from flask import Flask, request, render_template, jsonify, redirect, url_for
import os
import pandas as pd
from zebra_print import zebra_printer


def print_label(FNSKU, quantity):
    #codigo que recibe el FNSKU y la cantidad, busca en el pdf el barcode y lo manda a imprimir a la zebra
    #aca ya encontre en el pdf que imprimir
    zebra_printer() #aca le paso lo que necesito para imprimir, por ejemplo el FNSKU y la cantidad, o el nombre del pdf, o lo que nescesite.