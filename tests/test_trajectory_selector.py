from src.ontto.self_observer import SelfObserver
from src.ontto.trajectory_selector import TrajectorySelector


def test_selector_returns_three_counterfactuals():
    observer = SelfObserver()
    selector = TrajectorySelector()

    candidates = selector.evaluate(
        observer,
        current_state=0.2,
        current_memory=0.0,
        current_pressure=0.1,
        current_input=0.0,
        current_attractor=0.0,
        steps_delta=1,
    )

    assert [c.signal for c in candidates] == [-1.0, 0.0, 1.0]
    assert len(candidates) == 3
    assert selector.choose(candidates).signal in {-1.0, 0.0, 1.0}


def test_selector_is_deterministic():
    observer = SelfObserver()
    selector = TrajectorySelector()

    a = selector.evaluate(
        observer,
        current_state=0.3,
        current_memory=0.1,
        current_pressure=0.2,
        current_input=1.0,
        current_attractor=0.0,
        steps_delta=1,
    )
    b = selector.evaluate(
        observer,
        current_state=0.3,
        current_memory=0.1,
        current_pressure=0.2,
        current_input=1.0,
        current_attractor=0.0,
        steps_delta=1,
    )

    assert a == b
