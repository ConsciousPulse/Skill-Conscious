import numpy as np

from src.ontto.self_observer import SelfObserver


def test_self_observer_learns_transition():
    observer = SelfObserver(ridge=1e-4, max_samples=128)

    for t in range(40):
        state = np.tanh(t / 20.0)
        previous = np.tanh(max(0, t - 1) / 20.0)
        memory = state * 0.2
        pressure = state * 0.1
        signal = 1.0 if t % 2 == 0 else 0.0
        distance = abs(state)
        features = SelfObserver.features_for(
            previous_state=previous,
            state=state,
            memory=memory,
            pressure=pressure,
            last_input=signal,
            attractor_distance=distance,
            steps_delta=1,
        )
        observer.observe(features=features, actual_state=state * 0.98)

    prediction = observer.predict(
        previous_state=0.7,
        state=0.73,
        memory=0.14,
        pressure=0.07,
        last_input=1.0,
        attractor_distance=0.73,
        steps_delta=1,
    )

    assert prediction.samples == 40
    assert 0.0 <= prediction.confidence <= 1.0
    assert np.isfinite(prediction.predicted_state)
