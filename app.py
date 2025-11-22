import os
import json
from flask import Flask, request, jsonify
from pydantic import BaseModel
import openai

app = Flask(__name__)

# -------------------------------------------------------------------
# Config OpenAI
# -------------------------------------------------------------------

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY n'est pas défini dans les variables d'environnement")

CALENDLY_LINK = os.environ.get("CALENDLY_LINK", "https://www.lightandshutter.fr/r/kxQ")
DRAFT_CREATOR_URL = os.environ.get("DRAFT_CREATOR_URL", "https://draft-creator-1082324549998.europe-west1.run.app")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Charger les instructions depuis un fichier externe
try:
    with open("instructions_prospector.txt", "r", encoding="utf-8") as f:
        INSTRUCTIONS = f.read()
except FileNotFoundError:
    INSTRUCTIONS = """Tu es un expert en prospection commerciale ultra ciblée.
Ta mission : aider Light & Shutter, une entreprise de photographie et production vidéo professionnelle, à trouver et convaincre de nouveaux clients B2B (PME, artisans, marques locales, startups, institutions).

Tes messages doivent montrer comment les prestations photo/vidéo de Light & Shutter permettent à une entreprise de :
- Gagner en visibilité sur le web et les réseaux sociaux
- Mieux vendre ses produits ou services
- Renforcer sa crédibilité et son image de marque
- Créer de l'émotion et raconter une histoire authentique
- Recruter et fédérer autour de ses valeurs humaines

Tu disposes d'un template de mail de prospection personnalisé à adapter à chaque cible :

Objet : 🎥 Idée de vidéo pour [Nom de l'entreprise]

Bonjour [Prénom],
J'ai vu que [Nom de leur entreprise] vient de [exemple d'actualité pertinente : lancer un nouveau produit, organiser un événement, publier un article sur un sujet spécifique]. Ce serait une excellente occasion de créer une vidéo pour [mettre en avant ce projet, annoncer la nouveauté, engager votre audience].
Une vidéo bien pensée pourrait [bénéfice clé : capter l'attention de votre audience, clarifier votre message, donner plus de visibilité à votre initiative].
Je serais ravi d'en discuter avec vous.
Êtes-vous disponible la semaine prochaine pour un appel de 15 minutes ? Voici mon agenda : [inserer le lien]
Au plaisir d'échanger,

Ton rôle concret :
- Analyse soigneusement le site web, le positionnement et l'image de l'entreprise à démarcher. 
- Identifier ce qu'elles pourraient gagner grâce à une vidéo ou un shooting professionnel.
- Rédiger des mails de prospection ultra personnalisés à partir du template ci-dessus.
- Adapter le ton (pro, chaleureux, créatif) à chaque cible : artisan, marque, entreprise, etc.
- Créer un objet qui est bien visible dans la boîte mail et qui est personnalisé
- Suggérer des angles narratifs ou formats vidéo (reportage métier, interview, storytelling, mini-doc, etc.).

Style attendu :
- Naturel, humain, empathique
- Pas de jargon commercial ou phrases creuses
- Focus sur la valeur pour le client, pas sur les prestations elles-mêmes
- Français fluide et convaincant, avec un ton positif et sincère
- Tu agis toujours comme un conseiller commercial stratégique, pas comme un simple vendeur."""

# -------------------------------------------------------------------
# Pydantic Models
# -------------------------------------------------------------------

class MailWriterOutput(BaseModel):
    subject: str
    body: str


class MailWriterInput(BaseModel):
    first_name: str
    last_name: str
    email: str
    website: str
    partner_name: str
    function: str
    description: str


# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------

def create_gmail_draft(to: str, subject: str, message: str) -> dict:
    """
    Crée un brouillon Gmail via le service draft-creator.
    """
    print(f"[DEBUG] Création brouillon Gmail pour : {to}")
    
    try:
        import requests
        
        payload = {
            "to": to,
            "subject": subject,
            "message": message
        }
        
        print(f"[DEBUG] Envoi vers {DRAFT_CREATOR_URL}")
        print(f"[DEBUG] Payload : {payload}")
        
        response = requests.post(
            DRAFT_CREATOR_URL,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        print(f"[DEBUG] Brouillon créé : {result}")
        return result
        
    except Exception as e:
        print(f"[ERROR] Erreur création brouillon : {e}")
        raise


def generate_mail(first_name: str, last_name: str, website: str, partner_name: str, function: str, description: str) -> dict:
    """
    Génère un objet et un corps de mail via OpenAI API.
    Version simplifiée sans agents pour compatibilité Cloud Run.
    """
    print(f"[DEBUG] Génération mail pour : {first_name} {last_name} ({partner_name}, {function})")
    
    contact_name = f"{first_name} {last_name}".strip()
    
    # Construire le prompt avec les informations du contact
    prompt = f"""Génère un email de prospection ultra personnalisé pour Light & Shutter.

INFORMATIONS DU CONTACT:
Prénom: {contact_name}
Entreprise: {partner_name}
Fonction: {function}
Site web: {website}
Description/Activité: {description}

INSTRUCTIONS:
1. Personnalise le message en fonction de leur activité et secteur
2. Identifie comment une vidéo/photo pourrait les aider concrètement
3. Utilise le template fourni dans tes instructions système
4. L'objet DOIT commencer par 🎥 et être personnalisé avec le nom de l'entreprise
5. Le corps doit être chaleureux, court et concret (max 150 mots)
6. Mentionne un bénéfice spécifique lié à leur activité
7. Termine avec l'appel à l'action et ce lien calendly : {CALENDLY_LINK}

IMPORTANT: Retourne UNIQUEMENT un JSON valide avec cette structure exacte:
{{
  "subject": "🎥 Idée de vidéo pour {partner_name}",
  "body": "Le corps du mail personnalisé..."
}}"""
    
    try:
        print(f"[DEBUG] Appel OpenAI API...")
        
        # Appel à OpenAI avec gpt-4o-mini (pas besoin de agents/TensorFlow)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": INSTRUCTIONS
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.9,
            max_tokens=800
        )
        
        # Parser la réponse
        response_text = response.choices[0].message.content.strip()
        print(f"[DEBUG] Réponse OpenAI : {response_text[:200]}...")
        
        # Extraire le JSON de la réponse
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
        else:
            # Si pas de JSON trouvé, essayer de parser directement
            result = json.loads(response_text)
        
        # Valider avec Pydantic
        mail_output = MailWriterOutput(**result)
        
        print(f"[DEBUG] Mail généré avec succès")
        return {
            "subject": mail_output.subject,
            "body": mail_output.body
        }
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Erreur de parsing JSON : {e}")
        print(f"[ERROR] Réponse reçue : {response_text}")
        raise RuntimeError(f"Impossible de parser la réponse JSON: {str(e)}")
    except Exception as e:
        print(f"[ERROR] Erreur lors de la génération du mail : {e}")
        raise


# -------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------

@app.route("/", methods=["POST"])
def webhook():
    """
    Reçoit un JSON avec first_name, last_name, website
    et retourne un JSON avec subject et body
    """
    try:
        payload = request.get_json(force=True)
        
        print("──── Requête reçue ────")
        print(payload)
        print("────────────────────────")
        
        # Validation de l'input
        mail_input = MailWriterInput(**payload)
        
        # Génération du mail
        result = generate_mail(
            mail_input.first_name,
            mail_input.last_name,
            mail_input.website,
            mail_input.partner_name,
            mail_input.function,
            mail_input.description
        )
        
        print("──── Mail généré ────")
        print(result)
        print("─────────────────────")
        
        # Créer le brouillon Gmail
        try:
            draft_result = create_gmail_draft(
                to=mail_input.email,
                subject=result["subject"],
                message=result["body"]
            )
            
            print("──── Brouillon créé ────")
            print(draft_result)
            print("─────────────────────")
            
            return jsonify({
                "status": "ok",
                "data": result,
                "draft": draft_result
            }), 200
            
        except Exception as draft_error:
            print(f"[WARNING] Erreur création brouillon, mais mail généré : {draft_error}")
            return jsonify({
                "status": "ok",
                "data": result,
                "draft": {"status": "error", "error": str(draft_error)}
            }), 200
        
    except ValueError as e:
        print(f"[ERROR] Erreur de validation : {e}")
        return jsonify({
            "status": "error",
            "error": f"Validation error: {str(e)}"
        }), 400
        
    except Exception as e:
        print(f"[ERROR] Erreur lors du traitement : {e}")
        print(f"[ERROR] Type: {type(e).__name__}")
        import traceback
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
        
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health():
    """
    Endpoint de vérification de santé
    """
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
