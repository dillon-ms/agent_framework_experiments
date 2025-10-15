
import asyncio
from datetime import datetime
import json
import random
from agent_framework import ChatMessage
import aiohttp
from anyio import Path
from bs4 import BeautifulSoup
from pydantic import BaseModel
from jinja2 import Environment, Template
from agent_framework_demo.shared.client import get_completions_client
from agent_framework_demo.decision_tree_builder.examples.mermaid import generate_mermaid_diagram_from_file, generate_mermaid_diagram_from_string
from agent_framework_demo.decision_tree_builder.tree_executor import execute_tree


decision_tree_builder_prompt = "build_decision_tree_2.jinja2"

class GuidelinesDocument(BaseModel):
    name: str
    title: str
    url: str
    sections_html: list[str]

async def pull_guidelines():

    url_to_name = {
        "https://www.unboundmedicine.com/ucentral/view/Guidelines%20for%20Antibiotic%20Use/1308079/all/Pneumonia%2C%20CAP": "Pneumonia_CAP",
        # "https://www.unboundmedicine.com/ucentral/view/Guidelines%20for%20Antibiotic%20Use/1308089/all/Pneumonia%2C%20HAP": "Pneumonia_HAP",
        # "https://www.unboundmedicine.com/ucentral/view/Guidelines%20for%20Antibiotic%20Use/1308071/all/Aspiration%20and%20aspiration%20pneumonia": "Aspiration_Pneumonia",
        # "https://www.unboundmedicine.com/ucentral/view/Guidelines%20for%20Antibiotic%20Use/1308189/all/Pneumocystis_Jirovecii_Pneumonia__PCP_?q=Jirovecii+PCP+Pneumocystis+Pneumonia": "PCP_Pneumonia",
        # "https://www.unboundmedicine.com/ucentral/view/Guidelines%20for%20Antibiotic%20Use/1308072/all/Bacterial_Urinary_Tract_Infection__UTI%C2%AE_?q=Bacterial+Infection+Tract+UTI+Urinary": "Bacterial_UTI",
        # "https://www.unboundmedicine.com/ucentral/view/Guidelines%20for%20Antibiotic%20Use/1308156/all/Catheter_Associated_Urinary_Tract_Infection__CA_UTI%C2%AE_?q=Bacterial+Infection+Tract+UTI+Urinary": "CA_UTI",
    }
    async def get_guidelines_document(url, name) -> GuidelinesDocument:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                title = soup.select_one("#document-title").text.strip()
                sections = soup.select("section")
                sections_raw_html = (str(section) for section in sections)
                filtered_sections = [
                    section
                    for section in sections_raw_html
                    if '<div>References</div>' not in section
                    and '<div>Important Notes</div>' not in section
                ]
                return GuidelinesDocument(
                    name=name,
                    title=title,
                    url=url,
                    sections_html=filtered_sections
                )



    documents = await asyncio.gather(*(get_guidelines_document(url, name) for url, name in url_to_name.items()))
    print(f"Pulled {len(documents)} documents")
    return documents

def generate_mock_patient_indicators(llm_response_dict: dict) -> dict:
    """Generate a mock patient indicators dictionary based on the decision tree structure."""
    indicator_names = [indicator["name"] for indicator in llm_response_dict["indicators"]]
    indicators = {name: bool(random.randint(0, 1)) for name in indicator_names}
    return indicators



async def main():
    output_dir = Path(__file__).parent / "output" / datetime.now().strftime("%Y%m%d-%H%M%S")
    await output_dir.mkdir(exist_ok=True, parents=True)
    documents = await pull_guidelines()
    template_path = Path(__file__).parent / "prompts" / decision_tree_builder_prompt
    with open(template_path, 'r') as f:
        template: Template = Template(f.read())
    client = get_completions_client()
    for document in documents:
        rendered_template = template.render(document=document.model_dump(mode="json"))
        response = await client.get_response(messages=[ChatMessage(role="system", text=rendered_template)])
        print(response)
        decision_tree_dict = json.loads(response.text)
        mermaid_str = generate_mermaid_diagram_from_string(response.text, include_conditions=True)
        output_path = output_dir / f"{document.name}_decision_tree.md"
        decision = execute_tree(
            decision_tree_dict["decision_tree"],
            generate_mock_patient_indicators(decision_tree_dict)
        )
        with open(output_path, 'w') as f:
            f.write(f"# {document.title}\n")
            f.write(f"Source: {document.url}\n\n")
            f.write(f"The final decision is\n\n```json\n{json.dumps(decision.model_dump(mode="json"), indent=4)}\n```\n")
            f.write("```mermaid\n")
            f.write(mermaid_str)
            f.write("\n```\n")
            f.write(f"\n\nRaw decision tree json:\n```json\n{response.text}\n```\n\n")
            f.write(f"\n\nDecision tree generated from the following prompt:\n\n```\n{rendered_template}\n```\n")
        print(f"Wrote {output_path}")

    print("Decision Tree Builder Main")

if __name__ == "__main__":
    asyncio.run(main())