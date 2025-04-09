from pydantic_ai.models import Model
from pydantic_ai.models import infer_model as legacy_infer_model
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.azure import AzureProvider

from lightblue_ai.models.anthropic import AnthropicModel as PatchedAnthropicModel
from lightblue_ai.models.bedrock import (
    BedrockConverseModel as PatchedBedrockConverseModel,
)


def infer_model(model: str | Model):
    if not isinstance(model, str):
        return legacy_infer_model(model)

    if model.startswith("bedrock:"):
        return PatchedBedrockConverseModel(model.lstrip("bedrock:"))

    if model.startswith("anthropic:"):
        return PatchedAnthropicModel(model.lstrip("anthropic:"))

    if model.startswith("azure:"):
        # https://github.com/pydantic/pydantic-ai/pull/1422
        return OpenAIModel(model.lstrip("azure:"), provider=AzureProvider())

    return legacy_infer_model(model)
