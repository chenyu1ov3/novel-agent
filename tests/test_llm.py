from novel_agent.llm import LLMClient


class FakeOpenAIClient:
    class Chat:
        class Completions:
            def create(self, **kwargs):
                self.last_kwargs = kwargs
                return type(
                    "Response",
                    (),
                    {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "生成结果"})()})()]},
                )()

        def __init__(self):
            self.completions = self.Completions()

    def __init__(self):
        self.chat = self.Chat()


def test_llm_client_complete_returns_message_content():
    client = LLMClient(model="fake-model", client=FakeOpenAIClient())

    result = client.complete(system="你是编辑", user="写一段", temperature=0.5)

    assert result == "生成结果"
