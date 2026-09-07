"""
Normalisation de référence pièce auto.

Le but : comparer "1 234-567 A" et "1234567a" comme identiques,
pour éviter de rater un match juste à cause du formatage du site.
"""
import re
import unicodedata


def normaliser_ref(ref: str) -> str:
    """Retire espaces, tirets, points et met en majuscules."""
    if not ref:
        return ""
    ref = ref.upper()
    ref = re.sub(r"[\s\-\._/]", "", ref)
    return ref


def normaliser_texte(texte: str) -> str:
    """Normalise un texte pour comparer une recherche descriptive."""
    texte = unicodedata.normalize("NFKD", texte or "")
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", texte.lower()).strip()


def recherche_par_nom_correspond(recherche: str, texte_page: str) -> bool:
    """Vérifie que les mots significatifs d'un nom apparaissent sur la fiche."""
    mots = [mot for mot in normaliser_texte(recherche).split() if len(mot) >= 3]
    texte = normaliser_texte(texte_page)
    return bool(mots) and all(mot in texte for mot in mots)


def ref_correspond(ref_demandee: str, texte_page: str) -> bool:
    """
    Vérifie que la référence demandée apparaît bien dans le texte
    extrait de la fiche produit (après normalisation des deux côtés).
    C'est le garde-fou anti faux-positif.
    """
    ref_norm = normaliser_ref(ref_demandee)
    texte_norm = normaliser_ref(texte_page)
    if not ref_norm:
        return False
    return ref_norm in texte_norm
