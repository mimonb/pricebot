from __future__ import annotations

import asyncio
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from moteur import comparer_prix


app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/recherche")
def recherche():
    payload = request.get_json(silent=True) or request.form
    terme = str(payload.get("recherche", "")).strip()
    marque = str(payload.get("marque", "")).strip() or None

    if not terme:
        return jsonify({"erreur": "Saisis une référence ou un nom de pièce."}), 400

    try:
        resultats = asyncio.run(comparer_prix(terme, marque=marque))
    except Exception as erreur:
        app.logger.exception("Recherche impossible")
        return jsonify({"erreur": f"La recherche a échoué : {erreur}"}), 500

    donnees = [
        {
            "site": resultat.site,
            "prix": resultat.prix,
            "devise": resultat.devise,
            "url": resultat.url_produit,
            "confirmee": resultat.ref_confirmee,
            "erreur": resultat.erreur,
        }
        for resultat in resultats
    ]
    valides = [resultat for resultat in donnees if resultat["prix"] is not None and resultat["confirmee"]]

    return jsonify(
        {
            "recherche": terme,
            "marque": marque,
            "resultats": donnees,
            "meilleur": valides[0] if valides else None,
        }
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )