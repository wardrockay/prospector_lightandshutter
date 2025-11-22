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

# Charger les instructions depuis un fichier externe
with open("instructions_prospector.txt", "r", encoding="utf-8") as f:
    INSTRUCTIONS = f.read()


PROMPT = "{'first_name': 'Morgane', 'last_name': 'Hennebel', 'website': 'https://www.antenia.com', 'partner_name': 'Antenia', 'function': 'Responsable communication et marketing', 'description': 'Développement de logiciels'}"

class MyAgentSchema(BaseModel):
  subject: str
  body: str


my_agent = Agent(
  name="My agent",
  instructions=INSTRUCTIONS,
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
    texte_demande = PROMPT

    wf_input = WorkflowInput(input_as_text=texte_demande)
    result = asyncio.run(run_workflow(wf_input))

    print("=== OBJET ===")
    print(result["subject"])
    print("\n=== CORPS ===")
    print(result["body"])
