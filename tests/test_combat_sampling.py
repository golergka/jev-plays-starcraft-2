import random
import pytest
from player import sample_concrete_answer


def test_samples_only_model_mass_and_keeps_input():
    answer={'choice':'a','probabilities':{'a':0,'b':1}}
    assert sample_concrete_answer(answer,{'a':'A','b':'B'},random.Random(1))['choice']=='b'
    assert answer['choice']=='a'


@pytest.mark.parametrize('weights',[{}, {'bad':1}, {'a':-1}, {'a':float('nan')}, {'a':float('inf')}, {'a':0}])
def test_invalid_distribution_fails_loudly(weights):
    with pytest.raises(ValueError):
        sample_concrete_answer({'probabilities':weights},{'a':'A'},random.Random(1))


def test_fixed_seed_and_canonical_keys_ignore_dict_order():
    def draws(weights):
        rng=random.Random(20260920)
        return [sample_concrete_answer({'probabilities':weights},{'a':'A','b':'B'},rng)['choice'] for _ in range(30)]
    assert draws({'a':.4,'b':.6})==draws({'b':.6,'a':.4})
