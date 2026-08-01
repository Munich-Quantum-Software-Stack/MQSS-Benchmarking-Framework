import pytest
from mqssbench.framework.utils import validate_benchmark_registry_key

def test_valid_key():
    validate_benchmark_registry_key("core/native/bench1")  # should not raise

@pytest.mark.parametrize("bad", [
    "core/native",             # too few parts
    "core/native/too/many",    # too many parts
    "/source/name",            # empty origin
    "core//name",              # empty source
    "core/source/",            # empty name
    "user/ /name",             # white space
])
def test_invalid_keys_raise(bad):
    with pytest.raises(ValueError):
        validate_benchmark_registry_key(bad)
