from src.ontto.provider import LLMResponse


def test_response_contract():
    r = LLMResponse(text="hello", raw={"choices": []})
    assert r.text == "hello"
    assert isinstance(r.raw, dict)
