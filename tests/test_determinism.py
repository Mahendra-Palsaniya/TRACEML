import numpy as np


def test_vae_determinism():
    import compute
    x = np.zeros((2, 77), dtype=np.float32)
    first = compute.vae.score_raw(x)['scores']
    second = compute.vae.score_raw(x)['scores']
    np.testing.assert_array_equal(first, second)
