from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
import os

# 1. INITIALISATION DE L'APPLICATION
app = FastAPI(title="API IA Inclusive - Hackathon")

# Configuration CORS (autorise l'interface HTML à contacter le serveur sans blocage)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. PROMPT SYSTÈME FALC (Facile À Lire et à Comprendre)
PROMPT_SYSTEME_FALC = """Tu es un expert en simplification de texte selon les règles du FALC (Facile À Lire et à Comprendre).
Ta mission est de réécrire le texte donné pour qu'il soit très simple, clair, accessible aux personnes en situation de handicap mental, dyslexiques, ou ayant des difficultés de compréhension.
Consignes :
1. Utilise des mots simples et des phrases courtes.
2. Évite le jargon, les métaphores et le langage abstrait.
3. Conserve l'information essentielle sans déformer le sens original.
4. Présente le résultat de façon aérée et bien structurée.
"""


# 3. ROUTE PRINCIPALE UNIVERSELLE (TEXTE)
@app.post("/api/analyse-texte")
@app.post("/api/simplify")
async def simplify_text(request: Request):
    input_text = ""
    
    # Étape A : Extraire le texte quel que soit le format envoyé par le JavaScript
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
        # Si ce n'est pas du JSON (ex: FormData)
        try:
            form_data = await request.form()
            input_text = (
                form_data.get("text") or 
                form_data.get("texte") or 
                form_data.get("prompt") or 
                form_data.get("content") or ""
            )
        except Exception:
            pass

    if not input_text:
        raise HTTPException(status_code=400, detail="Aucun texte n'a été fourni.")

    full_prompt = f"{PROMPT_SYSTEME_FALC}\n\nTexte à simplifier :\n{input_text}"
    
    # --- TENTATIVE 1 : OLLAMA (100% LOCAL / HORS-LIGNE) ---
    try:
        ollama_response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2",
                "prompt": full_prompt,
                "stream": False
            },
            timeout=60
        )
        if ollama_response.status_code == 200:
            result = ollama_response.json().get("response", "")
            return {
                "simplified_text": result,
                "texte_simplifie": result,
                "resultat": result,
                "response": result,
                "source": "Ollama (Local)"
            }
    except Exception as e:
        print(f"Ollama local non disponible ou éteint : {e}")

    # --- TENTATIVE 2 : GROQ (CLOUD / EN LIGNE) ---
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key and os.path.exists("cle_groq.txt"):
        with open("cle_groq.txt", "r", encoding="utf-8") as f:
            api_key = f.read().strip()
            
    if api_key:
        try:
            groq_response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "llama-3.2-11b-vision-preview",
                    "messages": [
                        {"role": "system", "content": PROMPT_SYSTEME_FALC},
                        {"role": "user", "content": input_text}
                    ]
                },
                timeout=10
            )
            if groq_response.status_code == 200:
                result = groq_response.json()['choices']['message']['content']
                return {
                    "simplified_text": result,
                    "texte_simplifie": result,
                    "resultat": result,
                    "response": result,
                    "source": "Groq (Cloud)"
                }
        except Exception as e:
            print(f"Erreur Groq : {e}")

    raise HTTPException(status_code=500, detail="Aucun service d'IA (ni Ollama local, ni Groq) n'est disponible.")


# 4. ROUTE MULTIMÉDIA (Squelette Réception Fichiers / Images / Audio)
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "status": "Fichier reçu avec succès",
        "message": "Squelette prêt pour le traitement multimédia."
    }


# 5. SERVICE DES FICHIERS STATIQUES (Interface Web index.html)
app.mount("/", StaticFiles(directory=".", html=True), name="static")