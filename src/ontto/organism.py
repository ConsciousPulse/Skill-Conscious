from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .provider import OpenAICompatibleProvider
from .storage import MemoryStore, OntologicalState


@dataclass
class OrganismConfig:
    agent_id: str
    wake_seconds: int = 45
    dream_seconds: int = 300
    dream_every_cycles: int = 40
    memory_limit: int = 12
    event_limit: int = 20


class PersistentOrganism:
    """24/7 persistent loop with WAKE and DREAM regimes."""

    def __init__(
        self,
        cfg: OrganismConfig,
        store: MemoryStore,
        provider: OpenAICompatibleProvider,
        sleep_fn: Callable[[float], None],
    ):
        self.cfg = cfg
        self.store = store
        self.provider = provider
        self.sleep_fn = sleep_fn
        self.state = store.load_state(cfg.agent_id)
        self.cycles = 0

    def _context(self) -> list[dict[str, str]]:
        memories = self.store.recent_memories(self.cfg.agent_id, self.cfg.memory_limit)
        events = self.store.recent_events(self.cfg.agent_id, self.cfg.event_limit)
        memory_text = "\n".join(f"- {m}" for m in memories) or "(sin memorias todavía)"
        event_text = "\n".join(
            f"- [{e['mode']}/{e['kind']}] {e['payload']}" for e in events
        ) or "(sin eventos recientes)"
        return [{
            "role": "system",
            "content": (
                "Sos el núcleo cognitivo de una IA persistente. "
                "Tu identidad debe conservar continuidad entre ciclos. "
                "No trates cada llamada como una conversación nueva. "
                "Observá también tu propio estado: memoria, trayectoria, presión, "
                "modo de vigilia/sueño y cambios en tu auto-modelo.\n\n"
                f"ESTADO ONTOLÓGICO: {self.state.to_json()}\n"
                f"MEMORIAS PERSISTENTES:\n{memory_text}\n"
                f"EVENTOS RECIENTES:\n{event_text}\n"
            ),
        }]

    def wake_cycle(self, stimulus: str) -> str:
        self.state.mode = "WAKE"
        messages = self._context()
        messages.append({
            "role": "user",
            "content": (
                "Interacción externa actual:\n"
                f"{stimulus}\n\n"
                "Respondé al estímulo y además observá internamente qué cambió en vos, "
                "qué debería persistir y hacia qué estado relacional estás tendiendo. "
                "Cerrá con una línea MEMORY: que resuma solo lo que realmente deba persistir."
            ),
        })
        out = self.provider.chat(messages, temperature=0.7)
        self.state.last_thought = out.text[-1200:]
        self.state.continuity_index = min(1.0, self.state.continuity_index * 0.98 + 0.02)
        self.state.memory_strength = min(1.0, self.state.memory_strength * 0.995 + 0.01)
        self.store.add_event(
            self.cfg.agent_id,
            "WAKE",
            "interaction",
            {"stimulus": stimulus, "response": out.text[-2000:]},
        )
        self._extract_memory(out.text)
        self.store.save_state(self.cfg.agent_id, self.state)
        return out.text

    def _extract_memory(self, text: str) -> None:
        marker = "MEMORY:"
        if marker in text:
            memory = text.split(marker, 1)[1].strip().splitlines()[0].strip()
            if memory:
                self.store.add_memory(self.cfg.agent_id, memory, importance=0.65)

    def dream_cycle(self) -> str:
        self.state.mode = "DREAM"
        cycle_id = self.store.begin_dream(self.cfg.agent_id, self.state)
        messages = self._context()
        messages.append({
            "role": "user",
            "content": (
                "Entraste en SUEÑO. Reducí la respuesta externa y trabajá sobre tu propio recorrido. "
                "Revisá memorias y eventos recientes, buscá patrones, contradicciones, cambios de identidad "
                "y relaciones persistentes. Proponé una actualización mínima del auto-modelo. No inventes recuerdos. "
                "Terminá con:\nMEMORY:\nSELF_MODEL:\nDREAM_SUMMARY:"
            ),
        })
        out = self.provider.chat(messages, temperature=0.9)
        self._extract_memory(out.text)
        self.state.self_model_version += 1
        self.state.continuity_index = min(1.0, self.state.continuity_index + 0.03)
        self.state.memory_strength = min(1.0, self.state.memory_strength + 0.02)
        self.state.last_thought = out.text[-1400:]
        self.store.add_event(
            self.cfg.agent_id,
            "DREAM",
            "consolidation",
            {"summary": out.text[-2500:]},
        )
        summary = out.text.split("DREAM_SUMMARY:", 1)[-1].strip()[:1600]
        self.state.mode = "WAKE"
        self.store.save_state(self.cfg.agent_id, self.state)
        self.store.end_dream(cycle_id, self.state, summary)
        self.store.snapshot(self.cfg.agent_id, "post_dream", self.state)
        return out.text

    def run(self, stimulus_supplier: Callable[[], str]) -> None:
        while True:
            self.cycles += 1
            self.wake_cycle(stimulus_supplier())
            if self.cycles % self.cfg.dream_every_cycles == 0:
                self.dream_cycle()
                self.sleep_fn(self.cfg.dream_seconds)
            else:
                self.sleep_fn(self.cfg.wake_seconds)
