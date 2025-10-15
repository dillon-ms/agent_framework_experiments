
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Generator
from agent_framework import AgentRunResponse, ChatResponseUpdate, HostedCodeInterpreterTool
from agent_framework.azure import AzureAIAgentClient, AzureOpenAIChatClient
from azure.ai.agents.models import (
    RunStepDeltaCodeInterpreterDetailItemObject,
)
from azure.identity.aio import AzureCliCredential

@asynccontextmanager
async def get_agent_client():
    async with (
        AzureCliCredential() as credential,
        AzureAIAgentClient(async_credential=credential) as chat_client,
    ):
        yield chat_client

def get_completions_client(**kwargs: Any):
    credential = AzureCliCredential()
    client = AzureOpenAIChatClient(async_credential=credential, **kwargs)
    return client