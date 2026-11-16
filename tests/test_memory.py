import json

from langchain_core.messages import AIMessage

from research_agent.memory import BufferMemory, EntityMemory, SummaryMemory, load_memory, save_memory


class DummyModel:
    def __init__(self, answer):
        self.answer = answer

    def invoke(self, messages):
        return AIMessage(content=self.answer, usage_metadata={"input_tokens": 12, "output_tokens": 5,
                                                              "total_tokens": 17})


def test_buffer_persists_all_turns(tmp_path):
    memory = BufferMemory()
    memory.record("My codename is Orion", "Noted")
    memory.record("What was it?", "Orion")
    path = tmp_path / "session.json"
    save_memory(memory, path)
    loaded = load_memory("buffer", None, path)
    assert "My codename" in loaded.context("anything")
    assert "What was it?" in loaded.context("anything")
    assert len(loaded.turns) == 2


def test_summary_updates_and_counts_tokens():
    memory = SummaryMemory(DummyModel("Orion project has a budget of 4500 rupees."))
    memory.record("Orion budget is 4500", "Okay")
    assert "4500" in memory.context("What is the budget?")
    assert memory.memory_tokens["input_tokens"] == 12


def test_entity_extraction_and_retrieval():
    model = DummyModel(json.dumps({"Orion": "Project budget 4500 rupees", "Sirius": "Other project"}))
    memory = EntityMemory(model)
    memory.record("Orion project budget is 4500", "Okay")
    assert "4500" in memory.context("What is Orion's budget?")
    assert "Sirius" not in memory.context("What is Orion's budget?")
    assert memory.snapshot()["entities"]["Orion"].startswith("Project")

