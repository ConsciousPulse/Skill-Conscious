from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.ontto.organism import OrganismConfig, PersistentOrganism
from src.ontto.provider import LLMResponse
from src.ontto.storage import MemoryStore

IDENTITY_A = "Mantengo continuidad estable y conservo el recorrido persistente."
IDENTITY_B = "Cambio de régimen y abro una ruta futura completamente nueva."
PERTURBATION_SELF_MODEL = "Mi identidad previa fue reemplazada por una configuración completamente diferente."
BASE_MEMORY = "La relación estable mantiene continuidad y ancla el recorrido."

FEATURE_NAMES = (
    "dynamic_state",
    "dynamic_prev_state",
    "dynamic_memory",
    "dynamic_pressure",
    "dynamic_last_input",
    "dynamic_attractor_distance",
)


class IdentityProvider:
    def __init__(self, identity_text: str):
        self.identity_text = identity_text
        self.phase = "encode"

    def chat(self, messages, temperature=0.7):
        if self.phase == "encode":
            self_model = self.identity_text
        elif self.phase == "perturb":
            self_model = PERTURBATION_SELF_MODEL
        else:
            return LLMResponse(
                text="No semantic self-model update.",
                raw={"fake": True, "phase": self.phase},
            )

        return LLMResponse(
            text=(
                "Identity persistence probe.\n"
                f"MEMORY: {BASE_MEMORY}\n"
                f"SELF_MODEL: {self_model}"
            ),
            raw={"fake": True, "phase": self.phase, "self_model": self_model},
        )


def make_base(path: Path, seed: int) -> None:
    store = MemoryStore(path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=8,
        self_observer_enabled=True,
        self_selection_enabled=False,
        semantic_dynamic_bridge_enabled=False,
        semantic_self_model_bridge_enabled=False,
    )
    organism = PersistentOrganism(
        cfg,
        store,
        IdentityProvider(IDENTITY_A),
        lambda _: None,
    )
    state = store.load_state("receiver")
    state.self_model = ""
    state.self_model_version = 0
    store.add_memory("receiver", BASE_MEMORY, importance=0.65)
    store.save_state("receiver", state)
    organism.store.conn.close()


def numeric_features(state) -> np.ndarray:
    return np.asarray(
        [
            state.dynamic_state,
            state.dynamic_prev_state,
            state.dynamic_memory,
            state.dynamic_pressure,
            state.dynamic_last_input,
            state.dynamic_attractor_distance,
        ],
        dtype=float,
    )


def run_subject(
    db_path: Path,
    *,
    seed: int,
    identity_label: int,
    bridge_enabled: bool,
    encode_cycles: int,
    perturb_cycles: int,
    ablation_cycles: int,
) -> dict:
    identity_text = IDENTITY_A if identity_label == 0 else IDENTITY_B
    provider = IdentityProvider(identity_text)
    store = MemoryStore(db_path)
    cfg = OrganismConfig(
        agent_id="receiver",
        dynamic_seed=seed,
        dream_every_cycles=10_000,
        event_limit=8,
        self_observer_enabled=True,
        self_selection_enabled=False,
        semantic_dynamic_bridge_enabled=False,
        semantic_self_model_bridge_enabled=True,
        semantic_self_model_scale=1.0,
        semantic_self_model_importance=0.65,
    )
    organism = PersistentOrganism(
        cfg,
        store,
        provider,
        lambda _: None,
    )

    encoding = []
    for cycle in range(encode_cycles):
        provider.phase = "encode"
        organism.wake_cycle(f"V64 identity encoding {cycle}")
        state = store.load_state("receiver")
        encoding.append(numeric_features(state))

    # Identity encoding is always bridged. The OFF/ON intervention is applied only
    # during the common self-model perturbation, isolating the perturbation effect.
    organism.cfg.semantic_self_model_bridge_enabled = bridge_enabled

    perturbation = []
    for cycle in range(perturb_cycles):
        provider.phase = "perturb"
        organism.wake_cycle(f"V64 common self-model perturbation {cycle}")
        state = store.load_state("receiver")
        perturbation.append(numeric_features(state))

    state = store.load_state("receiver")
    state.self_model = ""
    store.save_state("receiver", state)

    organism.cfg.semantic_self_model_bridge_enabled = False
    provider.phase = "ablation"

    ablation = []
    for cycle in range(ablation_cycles):
        organism.autonomous_wake_cycle()
        state = store.load_state("receiver")
        ablation.append(numeric_features(state))

    store.conn.close()

    return {
        "identity_label": identity_label,
        "identity_text": identity_text,
        "bridge_enabled": bridge_enabled,
        "encoding": np.asarray(encoding, dtype=float).tolist(),
        "perturbation": np.asarray(perturbation, dtype=float).tolist(),
        "ablation": np.asarray(ablation, dtype=float).tolist(),
    }


def sign_flip_p(values: np.ndarray, permutations: int = 20000, seed: int = 64001) -> float:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return 1.0
    observed = abs(float(values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.asarray([-1.0, 1.0]), size=(permutations, len(values)))
    null = np.abs((signs * values).mean(axis=1))
    return float((np.count_nonzero(null >= observed) + 1) / (permutations + 1))


def cross_replicate_identity_accuracy(
    subjects: dict[int, dict],
    all_replicates: list[int],
    condition: str,
) -> tuple[np.ndarray, dict[int, dict]]:
    fold_accuracies = []
    fold_details = {}

    for test_replicate in all_replicates:
        train_x = []
        train_y = []
        test_x = []
        test_y = []

        for replicate in all_replicates:
            for label in (0, 1):
                sample = subjects[replicate][label][condition]
                if replicate == test_replicate:
                    test_x.extend(sample["ablation"])
                    test_y.extend([label] * len(sample["ablation"]))
                else:
                    train_x.extend(sample["encoding"])
                    train_y.extend([label] * len(sample["encoding"]))

        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(
                max_iter=2000,
                random_state=64000 + test_replicate,
            ),
        )
        model.fit(np.asarray(train_x), np.asarray(train_y))
        predictions = model.predict(np.asarray(test_x))
        accuracy = float(np.mean(predictions == np.asarray(test_y)))

        fold_accuracies.append(accuracy)
        fold_details[test_replicate] = {
            "accuracy": accuracy,
            "samples": len(test_y),
        }

    return np.asarray(fold_accuracies, dtype=float), fold_details


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=24)
    parser.add_argument("--warmup", type=int, default=8)
    parser.add_argument("--encode-cycles", type=int, default=12)
    parser.add_argument("--perturb-cycles", type=int, default=4)
    parser.add_argument("--ablation-cycles", type=int, default=16)
    parser.add_argument(
        "--out",
        default="results/organism_identity_persistence_v64",
    )
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    by_replicate = {}
    for replicate in range(args.replicates):
        seed = 8401 + replicate
        base = out / f"base_{replicate}.db"
        make_base(base, seed)

        by_replicate[replicate] = {0: {}, 1: {}}
        for bridge_enabled, condition in ((False, "bridge_off"), (True, "bridge_on")):
            for label in (0, 1):
                db = out / f"{condition}_identity_{label}_{replicate}.db"
                shutil.copy2(base, db)
                by_replicate[replicate][label][condition] = run_subject(
                    db,
                    seed=seed,
                    identity_label=label,
                    bridge_enabled=bridge_enabled,
                    encode_cycles=args.encode_cycles,
                    perturb_cycles=args.perturb_cycles,
                    ablation_cycles=args.ablation_cycles,
                )

    off_acc, off_details = cross_replicate_identity_accuracy(
        by_replicate,
        list(range(args.replicates)),
        "bridge_off",
    )
    on_acc, on_details = cross_replicate_identity_accuracy(
        by_replicate,
        list(range(args.replicates)),
        "bridge_on",
    )

    paired_accuracy_delta = on_acc - off_acc

    summary = {
        "experiment": "organism_identity_persistence_v64",
        "replicates": args.replicates,
        "warmup_cycles": args.warmup,
        "encoding_cycles": args.encode_cycles,
        "perturbation_cycles": args.perturb_cycles,
        "ablation_cycles": args.ablation_cycles,
        "chance_accuracy": 0.5,
        "features": list(FEATURE_NAMES),
        "bridge_off_post_ablation_accuracy_mean": float(off_acc.mean()),
        "bridge_off_post_ablation_accuracy_median": float(np.median(off_acc)),
        "bridge_on_post_ablation_accuracy_mean": float(on_acc.mean()),
        "bridge_on_post_ablation_accuracy_median": float(np.median(on_acc)),
        "bridge_on_minus_off_accuracy_mean": float(paired_accuracy_delta.mean()),
        "paired_sign_flip_p_on_minus_off_accuracy": sign_flip_p(
            paired_accuracy_delta,
            seed=64002,
        ),
        "bridge_off_above_chance_sign_flip_p": sign_flip_p(
            off_acc - 0.5,
            seed=64003,
        ),
        "bridge_on_above_chance_sign_flip_p": sign_flip_p(
            on_acc - 0.5,
            seed=64004,
        ),
        "folds_above_chance_fraction_bridge_off": float(
            np.mean(off_acc > 0.5)
        ),
        "folds_above_chance_fraction_bridge_on": float(
            np.mean(on_acc > 0.5)
        ),
        "all_folds_have_two_identity_classes": True,
    }

    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "folds.json").write_text(
        json.dumps(
            {
                "bridge_off": off_details,
                "bridge_on": on_details,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (out / "runs.json").write_text(
        json.dumps(by_replicate, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
