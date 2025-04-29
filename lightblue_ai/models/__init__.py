from pydantic_ai.models import Model
from pydantic_ai.models import infer_model as legacy_infer_model

from lightblue_ai.models.doubao import OpenAIModel as DoubaoModel


def infer_model(model: str | Model):
    if not isinstance(model, str):
        return legacy_infer_model(model)

    if model.startswith("openai:") and "doubao" in model:
        return DoubaoModel(model.lstrip("openai:"))

    return legacy_infer_model(model)
