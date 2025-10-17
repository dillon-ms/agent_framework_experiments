from datetime import datetime
import os
import asyncio
from pathlib import Path

from agent_framework.azure import AzureOpenAIChatClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv
load_dotenv()

def get_client(**kwargs) -> AzureOpenAIChatClient:
    """Create an Azure OpenAI Chat Client with Azure CLI authentication."""
    return AzureOpenAIChatClient(
        # async_credential=AzureCliCredential(),
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],  # Optional if using AzureCliCredential
        **kwargs,
    )


async def call_ai() -> None:
    print("Creating agent...")
    async with (
        AzureCliCredential() as credential,
        get_client().create_agent(
            name="Performance Review Writer",
            instructions="You help employees write performance reviews based on their job description and accomplishments.",
        ) as agent,
    ):
        date = datetime.now().strftime("%B %d, %Y")
        print(date)
        quarter = "FY26 Q1"
        notes = open(Path(__file__).parent / "input" / "notes.org").read()
        query = open(Path(__file__).parent / "prompt.txt").read().format(notes=notes, date=date, quarter=quarter)
        print("Calling model...")
        result = await agent.run(query)
        print("Got result.")
        report = result.text
        date = datetime.now().strftime("%Y%m%d")
        output_path = Path(__file__).parent / "output" / f"performance_review_{date}.md"
        output_path.write_text(report, encoding="utf-8")
        print(f"Wrote report to:\n{output_path.absolute()}")


async def main() -> None:

    await call_ai()


if __name__ == "__main__":
    asyncio.run(main())

