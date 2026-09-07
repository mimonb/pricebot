"""
Usage :
    python main.py "REF-PIECE"
    python main.py "filtre à air Audi"
    python main.py "59925" "NGK"

Exemple :
    python main.py "0986424815"
"""
import asyncio
import sys

from moteur import comparer_prix, afficher_resultats


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <référence, numéro OE ou nom de pièce>")
        sys.exit(1)

    recherche = sys.argv[1].strip()
    marque = " ".join(sys.argv[2:]).strip() or None
    description = recherche if not marque else f"{recherche} (marque : {marque})"
    print(f"Recherche du prix le plus bas pour : {description}")

    resultats = asyncio.run(comparer_prix(recherche, marque=marque))
    afficher_resultats(resultats)


if __name__ == "__main__":
    main()
