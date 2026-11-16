from research_agent.tools import calculator, python_execute, wikipedia_search
import research_agent.tools as tools


def test_calculator_arithmetic():
    assert calculator("(50 + 20) * 3") == "210"
    assert calculator("sqrt(81) + 2**3") == "17.0"


def test_calculator_rejects_code():
    assert calculator("__import__('os').system('whoami')").startswith("ERROR")
    assert calculator("2**1000000").startswith("ERROR")


def test_python_numeric_script():
    result = python_execute("values = [10,20,30]\nprint(sum(values)/len(values))")
    assert result == "20.0"


def test_python_rejects_unsafe_operations():
    assert python_execute("import os\nprint(os.getcwd())").startswith("ERROR")
    assert python_execute("print(open('/etc/passwd').read())").startswith("ERROR")


def test_wikipedia_search_mocked(monkeypatch):
    def fake_api(params):
        if "list" in params:
            return {"query": {"search": [{"title": "Ada Lovelace"}]}}
        return {"query": {"pages": {"1": {"title": "Ada Lovelace", "extract": "A mathematician."}}}}

    monkeypatch.setattr(tools, "_wiki_json", fake_api)
    response = wikipedia_search("Ada Lovelace")
    assert "Ada Lovelace" in response
    assert "A mathematician" in response
    assert "https://en.wikipedia.org/wiki/Ada_Lovelace" in response


def test_wikipedia_search_prefers_relevant_title(monkeypatch):
    def fake_api(params):
        if "list" in params:
            return {"query": {"search": [
                {"title": "Outlook.com", "snippet": "A Microsoft email service"},
                {"title": "Microsoft", "snippet": "Founded in 1975 by Bill Gates and Paul Allen"},
            ]}}
        return {"query": {"pages": {
            "1": {"title": "Microsoft", "extract": "Microsoft was founded by Bill Gates and Paul Allen."},
            "2": {"title": "Outlook.com", "extract": "An email service."},
        }}}

    monkeypatch.setattr(tools, "_wiki_json", fake_api)
    response = wikipedia_search("Microsoft founders")
    assert response.startswith("TITLE: Microsoft\n")

