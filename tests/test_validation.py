import pytest


def test_missing_feature_rejected():
    import compute
    with pytest.raises(ValueError):
        compute.predict([{}])
