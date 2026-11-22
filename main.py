# main.py - Serveur API universel pour le Hackathon
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq  # 🟢 Importation de la bibliothèque Groq
import uvicorn

app = FastAPI(title="API IA Inclusive - Hackathon")

# Permet à l'interface HTML de communiquer avec le serveur sans blocage de sécurité
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔑 1. Mets ta clé API Groq ici (entre les guillemets)
GROQ_API_KEY = "VOTRE_CLE_GROQ_ICI"
client = Groq(api_key=GROQ_API_KEY)

# 🧠 2. Le Prompt Système FALC
PROMPT_SYSTEME_FALC = """
Tu es un expert diplômé en accessibilité numérique et en rédaction FALC (Facile À Lire et à Comprendre).
Ton rôle est de réécrire le texte fourni par l'utilisateur pour le rendre parfaitement accessible à tous.

Voici les RÈGLES STRICTES que tu dois appliquer obligatoirement :
1. UNE SEULE IDÉE PAR PHRASE : Fais des phrases très courtes (Sujet + Verbe + Complément).
2. VOCABULAIRE SIMPLE : Utilise des mots du quotidien. Si un mot complexe est indispensable, explique-le simplement entre parenthèses.
3. STRUCTURE CLAIRE : Utilise des listes à puces avec des tirets dès que c'est possible pour aérer le texte.
4. VOIX ACTIVE : Utilise la voix active et des phrases affirmatives (évite les formes négatives ou passives).
5. PAS DE JARGON NI DE MÉTAPHORES : Supprime toutes les formules de style, abréviations non expliquées ou figures de style.
6. FORMAT DE SORTIE : Donne DIRECTEMENT le texte simplifié. Ne rajoute AUCUNE formule d'introduction ou de politesse du type "Voici votre texte simplifié :".
"""

@app.get("/")
def home():
    return {"status": "Serveur IA en ligne et prêt !"}

# ⚡ 3. La route API TEXTE connectée à la VRAIE IA
@app.post("/api/analyse-texte")
async def analyser_texte(texte: str = Form(...)):
    try:
        # Envoi de la requête à Llama 3.3 via Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": PROMPT_SYSTEME_FALC},
                {"role": "user", "content": f"Simplifie ce texte en FALC :\n{texte}"}
            ],
            model="openai/gpt-oss-20b",
            temperature=0.3,
        )
        
        # On extrait le résultat généré par l'IA
        resultat_ia = chat_completion.choices[0].message.content
        return {"succes": True, "resultat": resultat_ia}

    except Exception as e:
        return {"succes": False, "erreur": str(e)}


# 4. ROUTE FICHIER / IMAGE / AUDIO : Pour recevoir des photos, vidéos ou vocaux
@app.post("/api/analyse-media")
async def analyser_media(file: UploadFile = File(...)):
    type_fichier = file.content_type
    nom_fichier = file.filename
    
    return {
        "succes": True, 
        "message": f"Fichier '{nom_fichier}' ({type_fichier}) reçu avec succès !",
        "analyse": "Prêt pour le traitement par l'outil IA."
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)