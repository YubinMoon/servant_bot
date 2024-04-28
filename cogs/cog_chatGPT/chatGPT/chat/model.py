from openai.types.chat import ChatCompletionChunk


class ChatResponse(ChatCompletionChunk):
    def __init__(self, data) -> None:
        super().__init__(**data)

    def __add__(self, other: "ChatResponse") -> "ChatResponse":
        if self.id != other.id:
            raise ValueError("cannot add different response")
        new = self.model_dump()
        new["choices"][0] = self._merge_dict(
            self.choices[0].model_dump(), other.choices[0].model_dump()
        )
        return ChatResponse(new)

    def _merge_dict(self, dict_a: dict, dict_b: dict) -> dict:
        merged_dict = dict(dict_a)
        for key in dict_b:
            if key in dict_a:
                value_a = dict_a[key]
                value_b = dict_b[key]
                if isinstance(value_a, dict) and isinstance(value_b, dict):
                    merged_dict[key] = self._merge_dict(value_a, value_b)
                elif isinstance(value_a, str) and isinstance(value_b, str):
                    merged_dict[key] = value_a + value_b
                elif isinstance(value_a, list) and isinstance(value_b, list):
                    merged_dict[key] = self._merge_list(value_a, value_b)
                elif value_a is None or value_b is None:
                    merged_dict[key] = value_a or value_b
            else:
                merged_dict[key] = dict_b[key]

        return merged_dict

    def _merge_list(self, list_a: list, list_b: list) -> list:
        list_a_index = [value["index"] for value in list_a]
        list_b_index = [value["index"] for value in list_b]
        result = []
        for value_a in list_a:
            for value_b in list_b:
                if value_a["index"] == value_b["index"]:
                    result.append(self._merge_dict(value_a, value_b))

        for value_a in list_a:
            if value_a["index"] not in list_b_index:
                result.append(value_a)

        for value_b in list_b:
            if value_b["index"] not in list_a_index:
                result.append(value_b)
        return result
