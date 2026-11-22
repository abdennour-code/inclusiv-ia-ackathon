import os
import requests
from fastapi import FastAPI, Request, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from groq import Groq

# Initialisation de l'application FastAPI
app = FastAPI(title="Inclusiv'IA - API de Simplification FALC")

# Initialisation du client Groq (clé API dans les variables d'environnement)
client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

# ==============================================================================
# 1. PROMPTS DÉCOUPLÉS ET SPÉCIFIQUES À CHAQUE MOTEUR D'IA
# ==============================================================================

# Prompt 1 : Ultra-cadré pour Ollama (Modèle local Llama 3.2 3B)
PROMPT_OLLAMA = """Tu es un expert FALC (Facile À Lire et à Comprendre).

RÈGLES IMPÉRATIVES DE RESTITUTION :
1. Ne mets AUCUNE phrase d'introduction ni de politesse (Ne dis JAMAIS "Voici le texte..."). Donne DIRECTEMENT le résultat.
2. Découpe le texte sous forme de liste à puces claires (utilise des puces •).
3. Chaque puce doit contenir une seule idée très courte et simple.
4. Conserve uniquement les informations essentielles (dates, montants, démarches).
"""

# Prompt 2 : Fluidité naturelle pour Groq (Modèle Cloud Llama 3.3 70B)
PROMPT_GROQ = """Tu me sers d'expert en simplification de texte selon les règles du FALC (Facile À Lire et à Comprendre).
Ta mission est de réécrire le texte fourni pour qu'il soit extrêmement simple, clair, aéré et accessible à tous.
Consignes :
1. Utilise des mots simples et des phrases courtes.
2. Évite le jargon administratif et technique.
3. Conserve l'information essentielle sans déformer le sens.
"""

# ==============================================================================
# 2. ROUTES API (LOGIQUE ET TRAITEMENT)
# ==============================================================================

# Route principale universelle (Texte) - Accepte /api/analyse-texte et /api/simplify
@app.post("/api/analyse-texte")
@app.post("/api/simplify")
async def simplify_text(request: Request):
    input_text = ""
    
    # Extraire le texte quel que soit le format envoyé par le JavaScript
    try:
        data = await request.json()
        if isinstance(data, dict):
            input_text = (
                data.get("text") or 
                data.get("texte") or 
                data.get("prompt") or 
                data.get("content") or 
                data.get("message") or 
                data.get("input") or ""
            )
        elif isinstance(data, str):
            input_text = data
    except Exception:
        try:
            form_data = await request.form()
            input_text = (
                form_data.get("text") or 
                form_data.get("texte") or 
                form_data.get("prompt") or 
                form_data.get("content") or ""
            )
        except Exception:
            input_text = ""

    input_text = input_text.strip()

    if not input_text:
        raise HTTPException(status_code=400, detail="Aucun texte valide n'a été fourni.")

    # TENTATIVE 1 : Moteur Principal — Ollama (Local sur GPU)
    try:
        prompt_ollama = f"{PROMPT_OLLAMA}\n\nTexte à simplifier :\n{input_text}"

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt_ollama,
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            resultat = response.json().get("response", "").strip()
            if resultat:
                return {
                    "simplified_text": resultat,
                    "source": "Ollama (Local GPU)"
                }

    except Exception as e:
        print(f"⚠️ Ollama local indisponible ({e}). Bascule automatique sur Groq (Cloud)...")

    # TENTATIVE 2 : Moteur de Secours — Groq API (Cloud)
    try:
        prompt_groq = f"{PROMPT_GROQ}\n\nTexte à simplifier :\n{input_text}"

        chat_completion = client_groq.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt_groq}
            ],
            model="llama-3.3-70b-versatile",
        )

        resultat = chat_completion.choices.message.content.strip()
        return {
            "simplified_text": resultat,
            "source": "Groq (Cloud)"
        }

    except Exception as e:
        print(f"❌ Erreur critique Groq Cloud : {e}")
        raise HTTPException(
            status_code=500,
            detail="Aucun moteur d'IA (ni local, ni cloud) n'a pu répondre."
        )


# ROUTE MULTIMÉDIA (Squelette Réception Fichiers / Images / Audio)
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Route préparée pour recevoir des fichiers (documents, images, extraits audio)"""
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "status": "Fichier reçu avec succès",
        "message": "Squelette prêt pour le traitement multimédia."
    }

# ==============================================================================
# 3. SERVICE DES FICHIERS STATIQUES (SERVEUR WEB HTML/CSS/JS)
# ==============================================================================
# Servir les fichiers du dossier courant (y compris index.html à la racine /)
app.mount("/", StaticFiles(directory=".", html=True), name="static")