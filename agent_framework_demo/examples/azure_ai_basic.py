# Copyright (c) Microsoft. All rights reserved.

import os
import asyncio
from random import randint
from typing import Annotated

from agent_framework.azure import AzureAIAgentClient, AzureOpenAIChatClient
from azure.identity.aio import AzureCliCredential
from pydantic import Field
from dotenv import load_dotenv
load_dotenv()

"""
Azure AI Agent Basic Example

This sample demonstrates basic usage of AzureAIAgentClient to create agents with automatic
lifecycle management. Shows both streaming and non-streaming responses with function tools.
"""

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

def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the weather for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    result = f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."
    print(f"[Tool] get_weather({location}) -> {result}")
    return result


async def non_streaming_example() -> None:
    """Example of non-streaming response (get the complete result at once)."""
    print("=== Non-streaming Response Example ===")

    # Since no Agent ID is provided, the agent will be automatically created
    # and deleted after getting a response
    # For authentication, run `az login` command in terminal or replace AzureCliCredential with preferred
    # authentication option.
    async with (
        AzureCliCredential() as credential,
        get_client().create_agent(
            name="WeatherAgent",
            instructions="You are a helpful weather agent.",
            tools=get_weather,
        ) as agent,
    ):
        query = "What's the weather like in Seattle?"
        print(f"User: {query}")
        result = await agent.run(query)
        print(f"Agent: {result}\n")


async def streaming_example() -> None:
    """Example of streaming response (get results as they are generated)."""
    print("=== Streaming Response Example ===")

    # Since no Agent ID is provided, the agent will be automatically created
    # and deleted after getting a response
    # For authentication, run `az login` command in terminal or replace AzureCliCredential with preferred
    # authentication option.
    async with (
        AzureCliCredential() as credential,
        get_client().create_agent(
            name="WeatherAgent",
            instructions="You are a helpful weather agent.",
            tools=get_weather,
        ) as agent,
    ):
        query = "What's the weather like in Portland?"
        print(f"User: {query}")
        print("Agent: ", end="", flush=True)
        async for chunk in agent.run_stream(query):
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print("\n")


async def main() -> None:
    print("=== Basic Azure AI Chat Client Agent Example ===")

    await non_streaming_example()
    await streaming_example()


if __name__ == "__main__":
    asyncio.run(main())
