"""
Connecteur générique : un seul bout de code sait parler à N'IMPORTE QUEL
site du moment que sa config (sites.yaml) est correcte.

Ajouter un site = ajouter une entrée YAML, pas modifier ce fichier.
"""
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

from playwright.async_api import Page


@dataclass
class ResultatPrix:
    site: str
    ref_demandee: str
    prix: Optional[float]
    devise: str
    url_produit: str
    ref_confirmee: bool
    erreur: Optional[str] = None


def extraire_prix(texte: str) -> Optional[float]:
    """Extrait un nombre décimal d'un texte de prix genre '129,90 €' ou '$129.90'."""
    if not texte:
        return None
    texte = texte.replace("\xa0", " ").strip()
    match = re.search(r"(\d[\d\s]*[.,]\d{2})", texte)
    if not match:
        match = re.search(r"(\d+)", texte)
        if not match:
            return None
        return float(match.group(1))
    valeur = match.group(1).replace(" ", "").replace(",", ".")
    return float(valeur)


async def chercher_prix(
    page: Page, site_config: dict, recherche: str, marque: str = None
) -> ResultatPrix:
    """
    1. Va sur la page de recherche du site pour la référence ou le nom donné
    2. Prend le premier résultat pertinent
    3. Ouvre la fiche produit
    4. Vérifie que la référence affichée correspond
    5. Extrait le prix
    """
    from normalizer import normaliser_texte, recherche_par_nom_correspond, ref_correspond

    nom = site_config["nom"]
    valeur_url = quote_plus(recherche.strip())
    url_recherche = site_config["url_recherche"].format(ref=valeur_url)
    recherche_descriptive = any(c.isspace() for c in recherche.strip()) or len(recherche.split()) > 1

    try:
        await page.goto(url_recherche, timeout=20000, wait_until="domcontentloaded")

        champ_recherche = site_config.get("selecteur_champ_recherche")
        if champ_recherche:
            champ = page.locator(champ_recherche)
            await champ.fill("")
            await champ.press_sequentially(recherche, delay=30)
            await page.wait_for_timeout(1500)

        # attendre que les résultats apparaissent (site en JS lourd sinon la
        # page est encore vide au moment du scraping)
        attendre = site_config.get("attendre_selecteur")
        if attendre:
            try:
                await page.wait_for_selector(attendre, timeout=10000)
            except Exception:
                return ResultatPrix(
                    site=nom, ref_demandee=recherche, prix=None, devise="EUR",
                    url_produit=url_recherche, ref_confirmee=False,
                    erreur="Aucun résultat trouvé (timeout sélecteur résultats)",
                )

        resultats = page.locator(site_config["selecteur_resultat"])
        nb = await resultats.count()
        if nb == 0:
            return ResultatPrix(
                site=nom, ref_demandee=recherche, prix=None, devise="EUR",
                url_produit=url_recherche, ref_confirmee=False,
                erreur="Aucun résultat sur la page de recherche",
            )

        # Avec une marque, choisir le premier résultat dont la carte la contient.
        premier = resultats.first
        if marque:
            marque_norm = normaliser_texte(marque)
            premier = None
            for index in range(nb):
                candidat = resultats.nth(index)
                texte_carte = normaliser_texte(await candidat.inner_text())
                if marque_norm in texte_carte:
                    premier = candidat
                    break
            if premier is None:
                return ResultatPrix(
                    site=nom, ref_demandee=recherche, prix=None, devise="EUR",
                    url_produit=url_recherche, ref_confirmee=False,
                    erreur=f"Aucun résultat pour la marque : {marque}",
                )

        lien = premier.locator(site_config["selecteur_lien"]).first
        href = await lien.get_attribute("href")
        if not href:
            href = await lien.get_attribute("data-url")
        if not href:
            return ResultatPrix(
                site=nom, ref_demandee=recherche, prix=None, devise="EUR",
                url_produit=url_recherche, ref_confirmee=False,
                erreur="Lien produit introuvable dans le résultat",
            )
        if href.startswith("/"):
            base = re.match(r"https?://[^/]+", url_recherche).group(0)
            href = base + href

        await page.goto(href, timeout=20000, wait_until="domcontentloaded")

        # Vérifier la référence/OE ou les mots du nom demandé sur la fiche.
        ref_confirmee = True
        sel_ref = site_config.get("selecteur_ref_fiche")
        if sel_ref:
            try:
                texte_ref = await page.locator(sel_ref).first.inner_text(timeout=5000)
                if recherche_descriptive:
                    texte_fiche = await page.locator("body").inner_text(timeout=5000)
                    ref_confirmee = recherche_par_nom_correspond(recherche, texte_fiche)
                else:
                    ref_confirmee = ref_correspond(recherche, texte_ref)
            except Exception:
                ref_confirmee = False  # pas trouvé -> on ne peut pas garantir

        # extraire le prix
        texte_prix = await page.locator(site_config["selecteur_prix_fiche"]).first.inner_text(timeout=8000)
        prix = extraire_prix(texte_prix)

        return ResultatPrix(
            site=nom, ref_demandee=recherche, prix=prix, devise="EUR",
            url_produit=href, ref_confirmee=ref_confirmee,
            erreur=None if prix is not None else "Prix non extrait",
        )

    except Exception as e:
        return ResultatPrix(
            site=nom, ref_demandee=recherche, prix=None, devise="EUR",
            url_produit=url_recherche, ref_confirmee=False,
            erreur=f"{type(e).__name__}: {e}",
        )
