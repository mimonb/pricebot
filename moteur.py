"""
Moteur : lance la recherche sur tous les sites actifs, en parallèle,
et retourne le classement du moins cher au plus cher.
"""
import asyncio
from pathlib import Path
from typing import List

import yaml
from playwright.async_api import async_playwright

from connecteur import chercher_prix, ResultatPrix


def charger_sites(config_path: str) -> list[dict]:
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [s for s in data["sites"] if s.get("actif", True)]


async def comparer_prix(
    recherche: str, marque: str = None, config_path: str = None
) -> List[ResultatPrix]:
    if config_path is None:
        config_path = str(Path(__file__).parent / "sites.yaml")

    sites = charger_sites(config_path)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        async def traiter(site_config):
            page = await browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                )
            )
            try:
                await page.route("**/*", filtrer_ressource)
                return await chercher_prix(page, site_config, recherche, marque)
            finally:
                await page.close()

        resultats = await asyncio.gather(*[traiter(s) for s in sites])
        await browser.close()

    # tri : résultats valides et confirmés d'abord, par prix croissant,
    # puis les erreurs/non-confirmés à la fin
    def cle_tri(r: ResultatPrix):
        valide = r.prix is not None and r.ref_confirmee
        return (0 if valide else 1, r.prix if r.prix is not None else float("inf"))

    return sorted(resultats, key=cle_tri)


async def filtrer_ressource(route):
    """Ignore les ressources visuelles et trackers inutiles au scraping."""
    requete = route.request
    if requete.resource_type in {"image", "font", "media"}:
        await route.abort()
        return
    if any(domaine in requete.url for domaine in (
        "google-analytics.com",
        "googletagmanager.com",
        "doubleclick.net",
        "facebook.net",
    )):
        await route.abort()
        return
    await route.continue_()


def afficher_resultats(resultats: List[ResultatPrix]):
    print(f"\n{'Site':<15}{'Prix':<12}{'Ref OK':<10}{'Détail'}")
    print("-" * 70)
    for r in resultats:
        prix_str = f"{r.prix:.2f} €" if r.prix is not None else "N/A"
        ref_str = "oui" if r.ref_confirmee else "non"
        detail = r.erreur or r.url_produit
        print(f"{r.site:<15}{prix_str:<12}{ref_str:<10}{detail}")

    valides = [r for r in resultats if r.prix is not None and r.ref_confirmee]
    if valides:
        moins_cher = valides[0]
        print(f"\n>> Moins cher : {moins_cher.site} à {moins_cher.prix:.2f} €")
        print(f"   {moins_cher.url_produit}")
    else:
        print("\n>> Aucun résultat fiable trouvé sur les sites configurés.")
