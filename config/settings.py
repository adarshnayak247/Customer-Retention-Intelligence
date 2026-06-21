import os

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from pydantic import BaseModel


load_dotenv()


class AzureConfig(BaseModel):
    """Validated Azure OpenAI connection settings."""

    endpoint: str
    chat_deployment: str
    embed_deployment: str
    api_key: str
    api_version: str

    @classmethod
    def from_env(cls) -> "AzureConfig":
        """Build config from environment variables, stripping OpenAI path suffixes."""
        raw_endpoint = os.getenv("MODEL_ENDPOINT", "")
        endpoint = (
            raw_endpoint.split("/openai/")[0]
            if raw_endpoint and "/openai/" in raw_endpoint
            else raw_endpoint
        )
        return cls(
            endpoint=endpoint,
            chat_deployment=os.getenv("CHAT_MODEL_NAME", ""),
            embed_deployment=os.getenv("EMBEDDING_MODEL_NAME", ""),
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            api_version=os.getenv("api_version", ""),
        )

    def validate_complete(self) -> None:
        """Raise ValueError if any required field is empty."""
        missing = [
            field
            for field, value in self.model_dump().items()
            if not value
        ]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")


def load_llm(config: AzureConfig) -> AzureChatOpenAI:
    """Create an Azure ChatOpenAI LLM client with deterministic output."""
    return AzureChatOpenAI(
        azure_deployment=config.chat_deployment,
        azure_endpoint=config.endpoint,
        api_key=config.api_key,
        api_version=config.api_version,
        temperature=0,
    )


def load_embeddings(config: AzureConfig) -> AzureOpenAIEmbeddings:
    """Create an Azure OpenAI Embeddings client."""
    return AzureOpenAIEmbeddings(
        azure_deployment=config.embed_deployment,
        azure_endpoint=config.endpoint,
        api_key=config.api_key,
        api_version=config.api_version,
    )
