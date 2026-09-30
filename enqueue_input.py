from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from src.ontto.storage import MemoryStore

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Enqueue persistent organism input.")
    parser.add_argument("message", help="Message to enqueue.")
    parser.add_argument("--source", default="cli", help="Input source label.")
    parser.add_argument(
        "--agent-id",
        default=os.environ.get("ONTTO_AGENT_ID", "consciencia-001"),
    )
    parser.add_argument(
        "--db",
        default=os.environ.get("ONTTO_DB_PATH", "data/ontto.db"),
    )
    args = parser.parse_args()

    store = MemoryStore(Path(args.db))
    input_id = store.enqueue_input(
        args.agent_id,
        args.message,
        source=args.source,
    )

    print(f"INPUT_QUEUED id={input_id}")
    print(f"AGENT={args.agent_id}")
    print(f"DB={args.db}")
    print(f"PENDING={store.pending_input_count(args.agent_id)}")


if __name__ == "__main__":
    main()
