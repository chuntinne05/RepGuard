from itertools import combinations

import numpy as np

from repguard.audit.paired import exact_ht_total_variance, joint_inclusion, paired_sample, select_paired


def enumerate_design(n, k, budget):
    full, remainder = divmod(budget, k)
    for rows in combinations(range(n), full):
        base = [i*k+j for i in rows for j in range(k)]
        if not remainder:
            yield base
        else:
            for partial in set(range(n))-set(rows):
                for cols in combinations(range(k), remainder):
                    yield base + [partial*k+j for j in cols]


def test_exact_marginals_joint_probabilities_and_ht_variance_by_enumeration():
    n, k = 4, 3
    values = np.array([[.3,-.8,.1],[-.2,.5,.7],[.9,-.6,.4],[.2,.8,-.5]])
    for budget in range(1, n*k+1):
        samples = list(enumerate_design(n, k, budget))
        masks = np.zeros((len(samples), n*k))
        for i, indices in enumerate(samples):
            masks[i, indices] = 1
        q, same, different = joint_inclusion((n,k), budget)
        np.testing.assert_allclose(masks.mean(axis=0), q, atol=1e-12)
        np.testing.assert_allclose((masks[:,0]*masks[:,1]).mean(), same, atol=1e-12)
        np.testing.assert_allclose((masks[:,0]*masks[:,k]).mean(), different, atol=1e-12)
        totals = masks @ values.ravel()/q
        np.testing.assert_allclose(totals.mean(), values.sum(), atol=1e-12)
        np.testing.assert_allclose(totals.var(), exact_ht_total_variance(values,budget), atol=1e-12)


def test_sampler_exact_budget_unique_and_balanced_agent_counts():
    for budget in range(1, 57):
        indices = paired_sample((8,7), budget, np.random.default_rng(budget))
        assert len(indices) == len(set(indices)) == budget
        counts = np.bincount(indices % 7, minlength=7)
        assert counts.max()-counts.min() <= 1


def test_single_row_single_agent_edge_cases():
    for shape in [(1,4),(4,1),(1,1)]:
        values = np.arange(np.prod(shape),dtype=float).reshape(shape)
        assert exact_ht_total_variance(values, values.size) == 0
        assert len(paired_sample(shape,1,np.random.default_rng(0))) == 1


def test_paired_selector_never_uses_unqueried_labels():
    proxy=np.full((6,3),.5)
    routes=np.array([np.full(6,a) for a in range(3)])
    gold=(np.arange(18)%4==0).astype(float)
    queried=[]
    def audit(ix):
        queried.extend(ix.tolist())
        return gold[ix]
    first=select_paired(routes,proxy,0,7,np.random.default_rng(19),audit)
    changed=1-gold; changed[queried]=gold[queried]
    second=select_paired(routes,proxy,0,7,np.random.default_rng(19),lambda ix:changed[ix])
    assert len(queried)==len(set(queried))==7
    assert first==second
