from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import OpenAICompatibleProvider
from src.ontto.storage import MemoryStore

load_dotenv()


def main() -> None:
    api_key = os.environ.get("ONTTO_API_KEY", "")
    if not api_key:
        raise SystemExit("Falta ONTTO_API_KEY")

    agent_id = os.environ.get("ONTTO_AGENT_ID", "consciencia-001")
    poll_seconds = int(os.environ.get("ONTTO_POLL_SECONDS", "10"))
    autonomous_when_idle = os.environ.get(
        "ONTTO_AUTONOMOUS_WHEN_IDLE", "true"
    ).lower() in {"1", "true", "yes", "on"}

    store = MemoryStore(
        Path(os.environ.get("ONTTO_DB_PATH", "data/ontto.db"))
    )

    recovered = store.requeue_processing_inputs(agent_id)
    if recovered:
        store.add_event(
            agent_id,
            "SYSTEM",
            "input_recovery",
            {"requeued_inputs": recovered},
        )

    provider = OpenAICompatibleProvider(
        base_url=os.environ.get(
            "ONTTO_API_BASE_URL",
            "https://api.openai.com/v1",
        ),
        api_key=api_key,
        model=os.environ.get("ONTTO_MODEL", ""),
    )

    cfg = OrganismConfig(
        agent_id=agent_id,
        wake_seconds=poll_seconds,
        dream_seconds=int(os.environ.get("ONTTO_DREAM_SECONDS", "300")),
        dream_every_cycles=int(
            os.environ.get("ONTTO_DREAM_EVERY_CYCLES", "40")
        ),
        memory_limit=int(os.environ.get("ONTTO_MEMORY_LIMIT", "12")),
        event_limit=int(os.environ.get("ONTTO_EVENT_LIMIT", "20")),
    )

    organism = PersistentOrganism(cfg, store, provider, time.sleep)

    while True:
        organism.cycles += 1
        item = store.claim_next_input(agent_id)

        try:
            if item is not None:
                organism.wake_cycle(item["content"])
                store.add_event(
                    agent_id,
                    "SYSTEM",
                    "input_processed",
                    {
                        "input_id": item["id"],
                        "source": item["source"],
                    },
                )
                store.complete_input(item["id"])
            elif autonomous_when_idle:
                organism.autonomous_wake_cycle()

            if organism.cycles % cfg.dream_every_cycles == 0:
                organism.dream_cycle()
                time.sleep(cfg.dream_seconds)
            else:
                time.sleep(cfg.wake_seconds)

        except Exception:
            if item is not None:
                store.fail_input(item["id"])
            raise


if __name__ == "__main__":
    main()
