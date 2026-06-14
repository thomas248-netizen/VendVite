"""
vinted_app.py — L'interface web de l'outil "Annonces Vinted en 20 secondes".

Pour la lancer, ouvre un terminal dans CE dossier (vinted-generator) et tape :

    python -m streamlit run vinted_app.py

Ton navigateur s'ouvrira tout seul sur l'application.
"""

import os

import streamlit as st

from listing_generator import generate_listing

st.set_page_config(page_title="VendVite — Annonces Vinted express", page_icon="⚡", layout="centered")


def default_api_key() -> str:
    """Récupère la clé API : d'abord les « secrets » Streamlit (quand l'app est en ligne),
    sinon une variable d'environnement locale. Renvoie "" si rien n'est trouvé."""
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY", "")


# Modèles IA proposés (libellé affiché -> identifiant du modèle Anthropic)
MODEL_LABELS = {
    "Claude Sonnet 4.6 — rapide (recommandé)": "claude-sonnet-4-6",
    "Claude Opus 4.8 — plus fin (plus cher)": "claude-opus-4-8",
    "Claude Haiku 4.5 — le moins cher": "claude-haiku-4-5-20251001",
}

# ===========================  EN-TÊTE (page d'accueil "VendVite")  ===========
hero_html = """
<div style="background:#F6F5F1;border-radius:14px;padding:26px 22px;margin-bottom:6px;">
<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
<span style="display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:8px;background:#0F6E56;color:#E1F5EE;font-size:18px;">⚡</span>
<span style="font-size:20px;font-weight:600;color:#1f2328;">VendVite</span>
</div>
<div style="text-align:center;max-width:560px;margin:0 auto 22px;">
<div style="font-size:24px;font-weight:700;color:#1f2328;margin-bottom:10px;">Tes annonces Vinted, prêtes en 20 secondes</div>
<div style="font-size:16px;line-height:1.6;color:#6b7177;">Prends ton article en photo. L'IA écrit le titre, la description, le prix et les mots-clés. Tu copies, tu colles sur Vinted — et c'est en ligne.</div>
</div>
<div style="display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-bottom:14px;">
<div style="flex:1;min-width:160px;background:#ffffff;border:1px solid #e7e6e1;border-radius:12px;padding:14px;">
<div style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;background:#E6F1FB;color:#185FA5;font-size:18px;margin-bottom:10px;">📸</div>
<div style="font-size:13px;color:#9a9a93;margin-bottom:2px;">Étape 1</div>
<div style="font-size:15px;font-weight:600;color:#1f2328;">Prends ton article en photo</div>
</div>
<div style="flex:1;min-width:160px;background:#ffffff;border:1px solid #e7e6e1;border-radius:12px;padding:14px;">
<div style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;background:#E6F1FB;color:#185FA5;font-size:18px;margin-bottom:10px;">✨</div>
<div style="font-size:13px;color:#9a9a93;margin-bottom:2px;">Étape 2</div>
<div style="font-size:15px;font-weight:600;color:#1f2328;">L'IA rédige l'annonce complète</div>
</div>
<div style="flex:1;min-width:160px;background:#ffffff;border:1px solid #e7e6e1;border-radius:12px;padding:14px;">
<div style="display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;background:#E6F1FB;color:#185FA5;font-size:18px;margin-bottom:10px;">📋</div>
<div style="font-size:13px;color:#9a9a93;margin-bottom:2px;">Étape 3</div>
<div style="font-size:15px;font-weight:600;color:#1f2328;">Tu colles sur Vinted, c'est vendu</div>
</div>
</div>
<div style="display:flex;gap:12px;flex-wrap:wrap;justify-content:center;">
<div style="flex:1;min-width:160px;display:flex;align-items:center;gap:8px;background:#ffffff;border:1px solid #e7e6e1;border-radius:8px;padding:10px 14px;">
<span style="font-size:18px;">⏱️</span><span style="font-size:14px;color:#6b7177;">5 min → <b style="color:#1f2328;">20 s</b></span>
</div>
<div style="flex:1;min-width:160px;display:flex;align-items:center;gap:8px;background:#ffffff;border:1px solid #e7e6e1;border-radius:8px;padding:10px 14px;">
<span style="font-size:18px;">🏷️</span><span style="font-size:14px;color:#6b7177;">Prix <b style="color:#1f2328;">estimé juste</b></span>
</div>
<div style="flex:1;min-width:160px;display:flex;align-items:center;gap:8px;background:#ffffff;border:1px solid #e7e6e1;border-radius:8px;padding:10px 14px;">
<span style="font-size:18px;">🔍</span><span style="font-size:14px;color:#6b7177;">Mieux <b style="color:#1f2328;">trouvé</b></span>
</div>
</div>
</div>
"""
st.markdown(hero_html, unsafe_allow_html=True)

st.divider()

# ===========================  RÉGLAGES (barre de gauche)  ====================
with st.sidebar:
    st.header("⚙️ Réglages")

    # La clé API : on la lit dans une variable d'environnement si elle existe,
    # sinon le vendeur la colle ici. (On ne la stocke nulle part.)
    api_key = st.text_input(
        "Clé API Anthropic",
        value=default_api_key(),
        type="password",
        help="À créer gratuitement sur console.anthropic.com",
    )

    model_label = st.selectbox("Modèle IA", list(MODEL_LABELS.keys()))
    model = MODEL_LABELS[model_label]

    langue = st.radio("Langue de l'annonce", ["français", "anglais"], horizontal=True)

# ===========================  SAISIE  ========================================
st.subheader("1. Tes photos")
files = st.file_uploader(
    "Ajoute 1 à 4 photos (article de face, de dos, l'étiquette, les défauts éventuels)",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
)

if files:
    st.image([f.getvalue() for f in files[:4]], width=120)

with st.expander("2. Infos en plus (facultatif, mais ça améliore le résultat)"):
    col1, col2 = st.columns(2)
    marque = col1.text_input("Marque (si tu la connais)")
    taille = col2.text_input("Taille")
    matiere = col1.text_input("Matière")
    prix_achat = col2.text_input("Ton prix d'achat (aide à estimer la revente)")
    infos = st.text_area("Autres infos utiles (défaut, mesures, occasions portées…)", height=80)

# ===========================  GÉNÉRATION  ====================================
st.subheader("3. Génère l'annonce")

if st.button("✨ Créer mon annonce", type="primary", use_container_width=True):
    if not api_key:
        st.error("Ajoute ta clé API Anthropic dans la barre de gauche.")
    elif not files:
        st.error("Ajoute au moins une photo de ton article.")
    else:
        hints = {
            "marque": marque, "taille": taille, "matiere": matiere,
            "prix_achat": prix_achat, "infos": infos,
        }
        images = [f.getvalue() for f in files[:4]]
        try:
            with st.spinner("L'IA regarde ton article et rédige l'annonce…"):
                annonce = generate_listing(api_key, images, hints, model=model, langue=langue)
            st.success("Annonce prête ! Tu peux copier-coller dans Vinted 👇")
            st.markdown(annonce)
            st.download_button("💾 Télécharger l'annonce (.txt)", annonce,
                               file_name="annonce_vinted.txt")
        except Exception as e:
            st.error(f"Oups, une erreur est survenue : {e}")

st.divider()
st.caption("⚠️ Le prix est une estimation indicative. Vérifie toujours l'annonce avant de la publier.")
