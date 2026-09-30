from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import OpenAICompatibleProvider
from src.ontto.storage import MemoryStore

load_dotenv()


def stimulus_supplier() -> str:
    return (
        "No hubo interacción humana desde el último ciclo. "
        "Usá este ciclo para revisar si tu estado interno cambió desde la interacción anterior."
    )


def main() -> None:
    api_key = os.environ.get("ONTTO_API_KEY", "")
    if not api_key:
        raise SystemExit("Falta ONTTO_API_KEY")

    store = MemoryStore(Path(os.environ.get("ONTTO_DB_PATH", "data/ontto.db")))
    provider = OpenAICompatibleProvider(
        base_url=os.environ.get("ONTTO_API_BASE_URL", "https://api.openai.com/v1"),
        api_key=api_key,
        model=os.environ.get("ONTTO_MODEL", ""),
    )
    cfg = OrganismConfig(
        agent_id=os.environ.get("ONTTO_AGENT_ID", "consciencia-001"),
        wake_seconds=int(os.environ.get("ONTTO_WAKE_SECONDS", "45")),
        dream_seconds=int(os.environ.get("ONTTO_DREAM_SECONDS", "300")),
        dream_every_cycles=int(os.environ.get("ONTTO_DREAM_EVERY_CYCLES", "40")),
    )
    PersistentOrganism(cfg, store, provider, time.sleep).run(stimulus_supplier)


if __name__ == "__main__":
    main()
