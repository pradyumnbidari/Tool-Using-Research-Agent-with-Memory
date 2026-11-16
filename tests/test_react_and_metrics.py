import json

from langchain_core.messages import AIMessage

from research_agent.metrics import answer_em, answer_f1, normalize_answer
from research_agent.evaluation import _aggregate
from research_agent.evaluation import cot_baseline
from research_agent.react_agent import ReActResearchAgent


class ScriptedModel:
    def __init__(self, decisions):
        self.decisions = list(decisions)
        self.calls = 0

    def invoke(self, messages):
        answer = self.decisions[self.calls]
        self.calls += 1
        return AIMessage(content=json.dumps(answer), usage_metadata={
            "input_tokens": 25, "output_tokens": 15, "total_tokens": 40,
        })


def action(name, action_input="", final=""):
    return {"thought_summary": f"I should use {name}", "action": name,
            "action_input": action_input, "final_answer": final}


def test_react_two_tools_and_full_trace(tmp_path):
    model = ScriptedModel([
        action("wikipedia_search", "founding date of Microsoft"),
        action("calculator", "1975 - 1955"),
        action("final", final="20"),
    ])
    agent = ReActResearchAgent(model, tools={
        "wikipedia_search": lambda query: "Microsoft was founded in 1975. Its founder was born in 1955.",
        "calculator": lambda query: "20", "python_execute": lambda query: "unused",
    })
    file = tmp_path / "trace.jsonl"
    result = agent.run("How old was the founder?", trace_path=file)
    assert result["answer"] == "20"
    assert result["tool_calls"] == 2
    assert len(result["trace"]) == 3
    assert result["total_tokens"] == 120
    logs = [json.loads(line) for line in file.read_text().splitlines()]
    assert logs[0]["action"] == "wikipedia_search"
    assert logs[0]["observation"] == "Microsoft was founded in 1975. Its founder was born in 1955."
    assert logs[1]["action_input"] == "1975 - 1955"
    assert logs[2]["action"] == "final"


def test_limit_of_tool_calls(tmp_path):
    model = ScriptedModel([action("calculator", "1 + 1"), action("calculator", "1 + 1")])
    result = ReActResearchAgent(model, max_steps=1,
                                 tools={"calculator": lambda q: "2"}).run("Calculate", trace_path=tmp_path / "x.jsonl")
    assert result["status"] == "step_limit"
    assert result["tool_calls"] == 1


def test_can_answer_after_last_permitted_tool(tmp_path):
    model = ScriptedModel([action("calculator", "2 + 2"), action("final", final="4")])
    result = ReActResearchAgent(model, max_steps=1, tools={
        "calculator": lambda q: "4",
    }).run("What is 2 + 2?", trace_path=tmp_path / "done.jsonl")
    assert result["status"] == "completed"
    assert result["answer"] == "4"


def test_direct_arithmetic_finishes_without_repeated_model_call(tmp_path):
    model = ScriptedModel([action("calculator", "1975 - 1955 - 1")])
    agent = ReActResearchAgent(model, tools={"calculator": lambda q: "19"})
    result = agent.run("What is 1975 - 1955 - 1? Use the calculator tool.",
                       trace_path=tmp_path / "numeric.jsonl")
    assert result["status"] == "completed"
    assert result["answer"] == "19"
    assert result["tool_calls"] == 1
    assert model.calls == 1
    assert result["trace"][-1]["action"] == "final"


def test_repeating_same_calculator_is_blocked(tmp_path):
    model = ScriptedModel([
        action("calculator", "1975 - 1955"),
        action("calculator", "1975 - 1955"),
    ])
    result = ReActResearchAgent(model, tools={
        "calculator": lambda q: "20",
    }).run("Given 1975 and 1955, calculate the year difference.",
           trace_path=tmp_path / "repeated.jsonl")
    assert result["status"] == "step_limit"
    assert result["tool_calls"] == 1
    assert "same tool action was repeated" in result["answer"]


def test_rejects_invented_numeric_facts(tmp_path):
    model = ScriptedModel([
        action("wikipedia_search", "Bill Gates birth year"),
        action("calculator", "1952"),
        action("final", final="1952"),
    ])
    agent = ReActResearchAgent(model, tools={
        "wikipedia_search": lambda q: "ERROR: Wikipedia request timed out",
        "calculator": lambda q: "1952",
    })
    result = agent.run("In what year was he born?", trace_path=tmp_path / "guard.jsonl")
    assert result["status"] == "unverified"
    assert "could not verify" in result["answer"]
    assert result["trace"][1]["observation"].startswith("ERROR: Unsupported factual numbers 1952")


def test_evaluation_counts_abstention_as_evaluated_query():
    rows = [{"status": "unverified", "em": 0, "f1": 0, "tool_calls": 2,
             "total_tokens": 100, "input_tokens": 80, "output_tokens": 20}]
    summary = _aggregate(rows, n_requested=1)
    assert summary["completed"] == 1
    assert summary["abstained"] == 1
    assert summary["exact_match_accuracy_pct"] == 0.0


def test_invalid_local_model_decisions_end_safely(tmp_path):
    class InvalidModel:
        def __init__(self):
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            return AIMessage(content="This is not valid JSON")

    model = InvalidModel()
    result = ReActResearchAgent(model).run("Who was born in 1955?",
                                            trace_path=tmp_path / "invalid.jsonl")
    assert result["status"] == "unverified"
    assert result["tool_calls"] == 0
    assert model.calls == 2
    assert result["trace"][-1]["action"] == "final"


def test_empty_cot_response_does_not_crash():
    class EmptyModel:
        def invoke(self, messages):
            return AIMessage(content="")

    assert cot_baseline(EmptyModel(), "Question?")["answer"] == "I could not answer."


def test_hotpot_normalization_and_f1():
    assert normalize_answer("The United States!") == "united states"
    assert answer_em("The United States", "United States") == 1.0
    assert answer_em("London", "Paris") == 0.0
    assert answer_f1("first and second", "first second") == 0.8

