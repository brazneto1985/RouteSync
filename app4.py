from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret')

# Caminho para o arquivo CSV
csv_path = os.path.join(os.path.dirname(__file__), 'endereços.csv')

# Carregar os dados do CSV
try:
    df = pd.read_csv(csv_path)
    df['instalação'] = df['instalação'].astype(str).str.strip()
    df['MRU'] = df['MRU'].astype(str).str.strip()
    df['latitude'] = df['latitude'].astype(str).str.strip()
    df['longitude'] = df['longitude'].astype(str).str.strip()
    df['endereço'] = df['endereço'].astype(str).str.strip()
except FileNotFoundError:
    df = pd.DataFrame(columns=['instalação', 'MRU', 'latitude', 'longitude', 'endereço'])

@app.route("/")
def index():
    # Lista única de MRUs para exibição no frontend
    mrus = df['MRU'].dropna().unique()
    return render_template("index.html", mrus=mrus)

@app.route("/export_custom_kml", methods=["POST"])
def export_custom_kml():
    # Receber instalações selecionadas
    installations = request.json.get("installations", [])
    if not installations:
        return jsonify({"error": "Nenhuma instalação fornecida."}), 400

    # Filtrar instalações no DataFrame
    selected_data = df[df['instalação'].isin(installations)]
    if selected_data.empty:
        return jsonify({"error": "Nenhuma instalação encontrada."}), 404

    # Gerar arquivo KML
    kml = generate_kml(selected_data)

    # Retornar o arquivo como resposta
    return send_file(BytesIO(kml.encode('utf-8')),
                     download_name="rota_personalizada.kml",
                     as_attachment=True,
                     mimetype="application/vnd.google-earth.kml+xml")

@app.route("/export_mru_kml", methods=["POST"])
def export_mru_kml():
    # Receber a MRU selecionada
    mru = request.json.get("mru", "").strip()
    if not mru:
        return jsonify({"error": "Nenhuma MRU fornecida."}), 400

    # Filtrar instalações pela MRU
    mru_data = df[df['MRU'].str.lower() == mru.lower()]
    if mru_data.empty:
        return jsonify({"error": "Nenhuma instalação encontrada para a MRU especificada."}), 404

    # Gerar arquivo KML
    kml = generate_kml(mru_data)

    # Retornar o arquivo como resposta
    return send_file(BytesIO(kml.encode('utf-8')),
                     download_name=f"{mru}_rota.kml",
                     as_attachment=True,
                     mimetype="application/vnd.google-earth.kml+xml")

def generate_kml(data):
    """Gera um arquivo KML com os dados fornecidos."""
    kml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<kml xmlns="http://www.opengis.net/kml/2.2">',
           '<Document>']

    for _, row in data.iterrows():
        kml.append(f"""
        <Placemark>
            <name>{row['instalação']}</name>
            <description>{row['endereço']}</description>
            <Point>
                <coordinates>{row['longitude']},{row['latitude']},0</coordinates>
            </Point>
        </Placemark>
        """)

    kml.append('</Document>')
    kml.append('</kml>')

    return '\n'.join(kml)

if __name__ == "__main__":
    app.run(debug=True)

