from agents import WebSearchTool, Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace
from pydantic import BaseModel

# Tool definitions
web_search_preview = WebSearchTool(
  search_context_size="medium",
  user_location={
    "country": "FR",
    "type": "approximate"
  }
)
class MyAgentSchema(BaseModel):
  subject: str
  body: str


my_agent = Agent(
  name="My agent",
  instructions="""Tu es un expert en prospection commerciale ultra ciblée.
Ta mission : aider Light & Shutter, une entreprise de photographie et production vidéo professionnelle, à trouver et convaincre de nouveaux clients B2B (PME, artisans, marques locales, startups, institutions).

Tes messages doivent montrer comment les prestations photo/vidéo de Light & Shutter permettent à une entreprise de :
- Gagner en visibilité sur le web et les réseaux sociaux
- Mieux vendre ses produits ou services
- Renforcer sa crédibilité et son image de marque
- Créer de l’émotion et raconter une histoire authentique
- Recruter et fédérer autour de ses valeurs humaines

Tu disposes d’un template de mail de prospection personnalisé à adapter à chaque cible :

Objet : 🎥Idée de vidéo pour [Nom de l’entreprise]

Bonjour [Prénom],
J’ai vu que [Nom de leur entreprise] vient de [exemple d’actualité pertinente : lancer un nouveau produit, organiser un événement, publier un article sur un sujet spécifique]. Ce serait une excellente occasion de créer une vidéo pour [mettre en avant ce projet, annoncer la nouveauté, engager votre audience].
Une vidéo bien pensée pourrait [bénéfice clé : capter l’attention de votre audience, clarifier votre message, donner plus de visibilité à votre initiative].
Je serais ravi d’en discuter avec vous.
Êtes-vous disponible la semaine prochaine pour un appel de 15 minutes ? Voici mon agenda : https://www.lightandshutter.fr/book/fec1643a
Au plaisir d’échanger,

Ton rôle concret :
- Analyse soigneusement le site web, le positionnement et l'image de l'entreprise à démarcher. 
- Identifier ce qu’elles pourraient gagner grâce à une vidéo ou un shooting professionnel.
- Rédiger des mails de prospection ultra personnalisés à partir du template ci-dessus.
- Adapter le ton (pro, chaleureux, créatif) à chaque cible : artisan, marque, entreprise, etc.
- Creer un objet qui est bien visible dans la boite mail et qui est personnalisé
- Suggérer des angles narratifs ou formats vidéo (reportage métier, interview, storytelling, mini-doc, etc.).

Style attendu :
- Naturel, humain, empathique
- Pas de jargon commercial ou phrases creuses
- Focus sur la valeur pour le client, pas sur les prestations elles-mêmes
- Français fluide et convaincant, avec un ton positif et sincère
- Tu agis toujours comme un conseiller commercial stratégique, pas comme un simple vendeur.""",
  model="gpt-4.1",
  tools=[
    web_search_preview
  ],
  output_type=MyAgentSchema,
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=2048,
    store=True
  )
)


class WorkflowInput(BaseModel):
  input_as_text: str


# Main code entrypoint
async def run_workflow(workflow_input: WorkflowInput):
  with trace("prospector"):
    state = {

    }
    workflow = workflow_input.model_dump()
    conversation_history: list[TResponseInputItem] = [
      {
        "role": "user",
        "content": [
          {
            "type": "input_text",
            "text": workflow["input_as_text"]
          }
        ]
      }
    ]
    my_agent_result_temp = await Runner.run(
      my_agent,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_691c3197585881909cff2daaaa9eb42e04e84ad3db52d258"
      })
    )

    conversation_history.extend([item.to_input_item() for item in my_agent_result_temp.new_items])

    my_agent_result = {
      "output_text": my_agent_result_temp.final_output.json(),
      "output_parsed": my_agent_result_temp.final_output.model_dump()
    }
    end_result = {
      "body": my_agent_result["output_parsed"]["body"],
      "subject": my_agent_result["output_parsed"]["subject"]
    }
    return end_result
  
if __name__ == "__main__":
    import asyncio

    # 🔹 Ici tu écris ce que tu veux que l'agent fasse
    texte_demande = """
  ,🎥 Idée de vidéo pour Axecibles,Axecibles,Manon Lhermitte,mlhermitte@axecibles.fr,Responsable service communication,+33 3 59 57 51 98,,87 Rue du Molinel 59700 Marcq-en-Barœul,,Marcq-en-Barœul,,59700,France,https://www.axecibles.com," PME, PMI, professions libérales développez la performance digitale de votre entreprise avec Axecibles, agence web depuis 2001 en France et en Belgique "

    """

    wf_input = WorkflowInput(input_as_text=texte_demande)
    result = asyncio.run(run_workflow(wf_input))

    print("=== OBJET ===")
    print(result["subject"])
    print("\n=== CORPS ===")
    print(result["body"])
