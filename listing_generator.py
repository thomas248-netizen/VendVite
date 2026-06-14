"""
listing_generator.py — Le cerveau de l'outil.

À partir d'une (ou plusieurs) photo(s) d'un article, il demande à Claude de
rédiger une annonce Vinted complète et prête à copier-coller :
titre, description, marque, taille, état, couleur, prix conseillé et mots-clés.

Il faut une clé API Anthropic (gratuite à créer sur https://console.anthropic.com).
"""

from __future__ import annotations

import base64
import io

import anthropic
from PIL import Image

# Modèle par défaut : bon rapport qualité / prix / vitesse, et il "voit" les images.
DEFAULT_MODEL = "claude-sonnet-4-6"

# Pour réduire le coût et la lenteur, on rétrécit les photos avant de les envoyer.
# 1024 px de côté max, c'est largement suffisant pour que Claude reconnaisse l'article.
MAX_IMAGE_SIDE = 1024


SYSTEM = (
    "Tu es un expert de la vente sur Vinted (seconde main). Tu rédiges des annonces "
    "qui se vendent vite : titres clairs et trouvables dans la recherche, descriptions "
    "honnêtes et attractives. Tu écris simplement, sans superlatifs creux ni mensonges. "
    "RÈGLE D'OR : tu n'inventes JAMAIS une information que tu ne vois pas. Si la marque, "
    "la taille ou la matière ne sont pas visibles sur les photos et ne sont pas fournies "
    "par le vendeur, tu écris « à confirmer » plutôt que de deviner."
)

# La consigne envoyée à Claude. {hints} contient les infos données par le vendeur.
PROMPT = """Voici une ou plusieurs photos d'un article à vendre sur Vinted.

Infos fournies par le vendeur (à considérer comme certaines, complète le reste depuis les photos) :
{hints}

Analyse les photos et rédige une annonce Vinted complète, en {langue}.

Réponds en markdown, avec EXACTEMENT ces sections (garde les emojis et les titres) :

### 📌 Titre
Un seul titre, court et trouvable. Format conseillé : Marque + type d'article + couleur + taille.
(Vinted limite le titre : reste sous ~70 caractères.)
Si la marque ou la taille sont inconnues, ne les mets PAS dans le titre — ne mets JAMAIS
« à confirmer » dans le titre.

### 📝 Description (prête à copier-coller)
Une description vendeuse de 3 à 6 lignes : type d'article, matière, coupe, couleur,
état réel, mesures si visibles, et une petite touche qui donne envie. Reste honnête.
N'écris JAMAIS de phrase qui demande à l'acheteur de te contacter pour vérifier la taille
ou la marque, et ne t'excuse pas pour les infos manquantes. Si la taille ou la marque
manquent, écris simplement une courte ligne « Taille : à compléter » / « Marque : à compléter »
pour que le vendeur la remplisse lui-même.
Termine par une ligne « 📦 Envoi rapide et soigné ✨ ».

### 🏷️ Champs Vinted (à recopier dans les cases)
- Marque : ...
- Catégorie : ...
- Taille : ...
- État : (choisis parmi : Neuf avec étiquette / Neuf sans étiquette / Très bon état / Bon état / Satisfaisant)
- Couleur : ...

### 💶 Prix conseillé
Donne une fourchette RÉALISTE pour de la SECONDE MAIN sur Vinted (les prix y sont bas).
Sois prudent, surtout pour les vêtements d'enfant et quand la marque est inconnue.
Repères seconde main (indicatifs) : vêtement enfant sans marque connue 5–15 €,
vêtement adulte courant 8–20 €, pièce de marque ou premium plus haut.
Donne UNE phrase de justification et précise que c'est une estimation à ajuster
selon la marque et l'état réels.

### 🔎 Mots-clés
5 à 8 mots-clés séparés par des virgules, que l'acheteur taperait dans la recherche.
Écris-les TOUS dans la langue de l'annonce ({langue}) — ne mélange JAMAIS plusieurs langues.

Si une info est introuvable, écris « à confirmer » — n'invente rien."""


def _image_to_block(file_bytes: bytes) -> dict:
    """Rétrécit une photo et la transforme au format attendu par l'API Claude."""
    image = Image.open(io.BytesIO(file_bytes))
    image = image.convert("RGB")                 # enlève la transparence (PNG) si besoin
    image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))   # garde les proportions

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    data = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

    return {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/jpeg", "data": data},
    }


def _format_hints(hints: dict) -> str:
    """Met en forme les infos données par le vendeur (on ignore les cases vides)."""
    labels = {
        "marque": "Marque",
        "taille": "Taille",
        "etat": "État",
        "matiere": "Matière",
        "prix_achat": "Prix d'achat (pour aider à estimer le prix de revente)",
        "infos": "Autres infos",
    }
    rows = [f"- {labels[k]} : {hints[k]}" for k in labels if hints.get(k)]
    return "\n".join(rows) or "- (aucune info fournie, déduis tout depuis les photos)"


def generate_listing(api_key: str, images: list[bytes], hints: dict | None = None,
                     model: str = DEFAULT_MODEL, langue: str = "français") -> str:
    """Renvoie l'annonce Vinted (texte markdown) générée par l'IA."""
    if not images:
        raise ValueError("Il faut au moins une photo de l'article.")

    hints = hints or {}
    client = anthropic.Anthropic(api_key=api_key)

    # Le message envoyé = les photos, puis la consigne texte.
    content: list[dict] = [_image_to_block(img) for img in images]
    content.append({
        "type": "text",
        "text": PROMPT.format(hints=_format_hints(hints), langue=langue),
    })

    message = client.messages.create(
        model=model,
        max_tokens=1500,
        system=SYSTEM,
        messages=[{"role": "user", "content": content}],
    )

    parts = [b.text for b in message.content if getattr(b, "type", "") == "text"]
    return "\n".join(parts).strip() or "_(Réponse vide de l'IA.)_"
