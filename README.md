# PriceBot Pièces Auto

Bot qui compare le prix d'une référence pièce auto sur plusieurs sites
(DGJAUTO, DistriAuto et Pieceauto-Discount) et retourne le moins cher.

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Interface web

```bash
python web.py
```

Ouvre ensuite [http://127.0.0.1:5000](http://127.0.0.1:5000) dans ton navigateur.

## Publication gratuite avec une URL publique

Le fichier `render.yaml` prépare le déploiement sur Render :

1. Mets le projet sur GitHub.
2. Va sur [render.com](https://render.com) et connecte ton dépôt GitHub.
3. Choisis **New > Blueprint** et sélectionne le dépôt.
4. Render détecte `render.yaml`, puis crée le service `pricebot`.
5. Après le déploiement, Render fournit une URL publique du type
  `https://pricebot.onrender.com`.

Le plan gratuit Render peut mettre le service en veille après une période sans
visite. Le premier accès peut donc prendre quelques secondes. Un hébergement
gratuit réellement garanti 24 h/24 et 7 j/7 est rarement proposé ; Oracle
Cloud Free Tier est une alternative plus persistante, mais sa configuration
est plus complexe et peut demander une carte bancaire.

## Utilisation

```bash
python main.py "0986424815"
python main.py "WK6037"
python main.py "filtre à air Audi"
python main.py "06J 115 403 Q"
python main.py "59925" "NGK"
```

La recherche accepte une référence fabricant, un numéro OE ou le nom d'une
pièce avec une marque. Pour un nom composé de plusieurs mots, entoure la
recherche de guillemets afin qu'elle soit envoyée comme une seule requête.
Le deuxième argument est optionnel et filtre les résultats sur la marque :
`python main.py "59925" "NGK"` ne conserve que les produits de marque NGK.

## ⚠️ Étape indispensable avant le premier lancement : vérifier les sélecteurs

Les sélecteurs CSS dans `sites.yaml` sont des **points de départ
plausibles**, pas une garantie — chaque site change régulièrement sa
structure HTML, et le bot doit être calibré dessus. Sans cette étape, le
scraping risque de ne rien trouver ou de choper le mauvais prix. Voici
comment corriger un site :

1. Ouvre le site dans un navigateur, fais une recherche par référence.
2. Clic droit sur **une carte produit** dans la liste de résultats →
   **Inspecter**. Repère la classe ou l'attribut `data-*` commun à toutes
   les cartes → colle-le dans `selecteur_resultat`.
3. Ouvre **une fiche produit**, clic droit sur **le prix affiché** →
   Inspecter → note le sélecteur → `selecteur_prix_fiche`.
4. Fais pareil pour l'endroit où la référence est affichée sur la fiche
   → `selecteur_ref_fiche` (sert à vérifier qu'on n'a pas pris la
   mauvaise pièce).
5. Relance `python main.py "ta_ref"` et regarde la colonne `Détail` du
   tableau de sortie : elle affiche l'erreur exacte si un site échoue,
   ça guide directement vers quel sélecteur corriger.

## Ajouter un nouveau site

Ajoute un bloc dans `sites.yaml`, aucun code à toucher :

```yaml
  - nom: "nouveau_site"
    url_recherche: "https://nouveau-site.fr/recherche?q={ref}"
    selecteur_resultat: "..."
    selecteur_lien: "a"
    attendre_selecteur: "..."
    selecteur_prix_fiche: "..."
    selecteur_ref_fiche: "..."
    actif: true
```

## Points d'attention légaux / techniques

- **CGU** : vérifie que le scraping automatisé n'est pas explicitement
  interdit par les CGU du site avant de l'utiliser à grande fréquence.
- **`robots.txt`** : à consulter (`site.fr/robots.txt`) pour connaître
  les zones que le site demande de ne pas crawler.
- **Fréquence** : évite les requêtes en boucle serrée ; un usage
  ponctuel pour comparer un prix est très différent d'un crawl massif.
- **API officielle** : si un site en propose une, elle est presque
  toujours préférable au scraping (plus stable, pas de risque de
  blocage).

## Prochaines étapes possibles

- Historique des prix (SQLite) pour suivre l'évolution dans le temps.
- Alerte email/notification si le prix passe sous un seuil.
- Résolution multi-référence (OEM ↔ équipementier) pour un même produit.
