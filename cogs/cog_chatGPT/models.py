class BaseModel:
    name: str
    description: str
    provider: str
    model: str
    image: bool


class GPT3_5(BaseModel):
    name: str = "gpt-3.5"
    description: str = "빠르고 저렴한 모델"
    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    image: bool = False


class GPT4o(BaseModel):
    name: str = "gpt-4o"
    description: str = "비싸고 느리지만 더 좋은 모델"
    provider: str = "openai"
    model: str = "gpt-4o"
    image: bool = True


def get_models() -> list[BaseModel]:
    return [GPT3_5(), GPT4o()]


def get_model(name: str) -> BaseModel | None:
    for model in get_models():
        if model.name == name:
            return model
    return None
