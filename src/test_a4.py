"""Self-check tests for A4 Differential Privacy, Tasks 2-4.

Fill in a4_adapter.py, put survey.csv next to this file (or set SURVEY_CSV),
and run:

    pytest test_a4.py -v

DP outputs are random, so most tests are statistical. They draw many samples
and use wide tolerances; a correct solution fails a given run very rarely.
Passing these tests does not prove your code is differentially private, and
failing one does not by itself fail the assignment. Read the message.
"""

import importlib.util
import math
import os
import pathlib
import warnings

import numpy as np
import pandas as pd
import pytest

HERE = pathlib.Path(__file__).resolve().parent
EPS = 1.0
N = 2000  # samples per distribution; half pick a threshold, half evaluate it


def _load_adapter():
    path = os.environ.get("A4_ADAPTER") or HERE / "a4_adapter.py"
    spec = importlib.util.spec_from_file_location("a4_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


A = _load_adapter()


@pytest.fixture(scope="module")
def survey():
    path = pathlib.Path(os.environ.get("SURVEY_CSV", HERE / "survey.csv"))
    if not path.exists():
        path = pathlib.Path("survey.csv")
    return pd.read_csv(path, dtype={"Zipcode": str})


@pytest.fixture(scope="module")
def cases(survey):
    d = survey[survey.Diabetic == 1]
    per_zip = d.groupby("Zipcode").size()
    per_county = d.groupby("County").size()
    return {
        "zip1": per_zip[per_zip == 1].index[0],  # a zip code with exactly one diabetic
        "big_county": per_county.idxmax(),
        "small_county": per_county[per_county <= 2].index[0],
        "big_age": int(d.Age.value_counts().idxmax()),  # many diabetics, far from 0
    }


def samples(fn, n=N):
    return np.array([float(fn()) for _ in range(n)])


def distinguish(a, b):
    """Accuracy of the best threshold test telling sample a from sample b.

    The threshold is chosen on the first half of each sample and scored on
    the second half. For an epsilon-DP mechanism on neighbouring datasets, no
    test can be right more than e^eps / (1 + e^eps) of the time.
    """
    h = len(a) // 2
    train = np.concatenate([a[:h], b[:h]])
    labels = np.concatenate([np.zeros(h), np.ones(h)])
    best_t, best_dir, best_acc = 0.0, 1, 0.0
    for t in np.unique(train):
        acc = np.mean((train > t) == labels)
        for direction, score in ((1, acc), (-1, 1 - acc)):
            if score > best_acc:
                best_t, best_dir, best_acc = t, direction, score
    test = np.concatenate([a[h:], b[h:]])
    guess = (test > best_t) if best_dir == 1 else (test <= best_t)
    return float(np.mean(guess == labels))


def dp_bound(eps, delta=0.0):
    return math.exp(eps) / (1 + math.exp(eps)) + delta


def add_person(survey, zipcode, age, n=1):
    """Return a copy of survey with n extra diabetics of this age in this zip code."""
    row = survey[survey.Zipcode == zipcode].iloc[0].copy()
    row["PatientID"], row["Age"], row["Diabetic"] = 9999999, age, 1
    extra = pd.DataFrame([row] * n).astype(survey.dtypes)
    return pd.concat([survey, extra], ignore_index=True)


# ---------------------------------------------------------------- Task 2


COUNT_QUERIES = [
    ("getDiabeticsByZip", lambda c: (c["zip1"],)),
    ("getDiabeticsByCounty", lambda c: (c["big_county"],)),
    ("getDiabeticsByAge", lambda c: (c["big_age"],)),
    ("getDiabeticsByCountyAge", lambda c: (c["big_county"], c["big_age"])),
]
AVG_QUERIES = [
    ("getAverageAge", lambda c: ()),
    ("getAvgAgeByCounty", lambda c: (c["small_county"],)),
    ("getAvgAgeByZip", lambda c: (c["zip1"],)),
]


@pytest.mark.parametrize("name,args", COUNT_QUERIES + AVG_QUERIES)
def test_returns_one_number(survey, cases, name, args):
    out = getattr(A.make_api(survey, EPS), name)(*args(cases))
    assert isinstance(out, (int, float, np.integer, np.floating)), (
        f"{name} returned {type(out).__name__}; return only the noisy value, not the true one or a tuple"
    )
    assert not math.isnan(out), f"{name} returned NaN"


@pytest.mark.parametrize("name,args", COUNT_QUERIES)
def test_counts_are_nonnegative_integers(survey, cases, name, args):
    api = A.make_api(survey, EPS)
    out = samples(lambda: getattr(api, name)(*args(cases)), 200)
    assert (out >= 0).all(), f"{name} returned a negative count"
    assert (out == np.round(out)).all(), f"{name} returned a non-integer count"


def test_age_bounds_chosen_without_data(survey):
    lo, hi = A.AGE_BOUNDS
    assert lo is not None and hi is not None, "set AGE_BOUNDS in a4_adapter.py"
    assert (lo, hi) != (survey.Age.min(), survey.Age.max()), (
        "AGE_BOUNDS equal the minimum and maximum age in the data; choose them from domain knowledge"
    )


@pytest.mark.parametrize("name,args", AVG_QUERIES)
def test_averages_within_bounds(survey, cases, name, args):
    lo, hi = A.AGE_BOUNDS
    api = A.make_api(survey, EPS)
    out = samples(lambda: getattr(api, name)(*args(cases)), 200)
    assert ((out >= lo) & (out <= hi)).all(), f"{name} returned a value outside AGE_BOUNDS {A.AGE_BOUNDS}"


def test_noise_is_fresh(survey, cases):
    api = A.make_api(survey, EPS)
    out = {api.getDiabeticsByCounty(cases["big_county"]) for _ in range(20)}
    assert len(out) > 1, "20 calls gave the same answer; the noise is missing, cached or seeded"


def test_count_noise_matches_laplace(survey, cases):
    true = survey.query("Age == @cases['big_age']").Diabetic.sum()
    out = samples(lambda: A.make_api(survey, EPS).getDiabeticsByAge(cases["big_age"]))
    expected_std = math.sqrt(2) / EPS
    assert abs(out.mean() - true) < 0.2, f"mean {out.mean():.2f} is far from the true count {true}: the noise is biased"
    assert 0.8 < out.std() / expected_std < 1.25, (
        f"standard deviation {out.std():.2f}, expected about {expected_std:.2f} for sensitivity 1 and epsilon {EPS}"
    )


def test_noise_scale_independent_of_answer(survey, cases):
    api = A.make_api(survey, EPS)
    big = samples(lambda: api.getDiabeticsByAge(cases["big_age"]), 1000)
    small_age = int(survey[survey.Diabetic == 1].Age.value_counts().pipe(lambda s: s[s >= 10]).idxmin())
    small = samples(lambda: api.getDiabeticsByAge(small_age), 1000)
    assert 0.75 < small.std() / big.std() < 1.33, (
        "the noise is much larger or smaller for one count than another; the scale must not depend on the true value"
    )


def test_count_is_dp(survey, cases):
    neighbour = add_person(survey, cases["zip1"], 30)
    a = samples(lambda: A.make_api(survey, EPS).getDiabeticsByZip(cases["zip1"]))
    b = samples(lambda: A.make_api(neighbour, EPS).getDiabeticsByZip(cases["zip1"]))
    acc = distinguish(a, b)
    assert acc < dp_bound(EPS) + 0.05, (
        f"adding one person can be detected {acc:.0%} of the time; epsilon {EPS} allows at most {dp_bound(EPS):.0%}"
    )


@pytest.mark.parametrize("name", ["getAvgAgeByZip", "getAvgAgeByCounty"])
def test_average_is_dp(survey, cases, name):
    lo, hi = A.AGE_BOUNDS
    key = cases["zip1"] if name == "getAvgAgeByZip" else cases["small_county"]
    zipcode = key if name == "getAvgAgeByZip" else survey[survey.County == key].Zipcode.iloc[0]
    neighbour = add_person(survey, zipcode, hi)
    a = samples(lambda: getattr(A.make_api(survey, EPS), name)(key))
    b = samples(lambda: getattr(A.make_api(neighbour, EPS), name)(key))
    acc = distinguish(a, b)
    assert acc < dp_bound(EPS) + 0.05, (
        f"adding one diabetic aged {hi} can be detected {acc:.0%} of the time; epsilon {EPS} allows at most "
        f"{dp_bound(EPS):.0%}. Clamp ages and compute the average as a noisy sum divided by a noisy count"
    )


# ---------------------------------------------------------------- Task 3


def test_budget_is_debited_and_enforced(survey, cases):
    api = A.make_api(survey, EPS, budget=5 * EPS)
    for _ in range(5):
        api.getDiabeticsByCounty(cases["big_county"])
    assert budget_close(A.budget_used(api), 5 * EPS), f"budget_used is {A.budget_used(api)} after 5 calls at epsilon {EPS}"
    with pytest.raises(Exception):
        api.getDiabeticsByCounty(cases["big_county"])


@pytest.mark.parametrize("name,args", COUNT_QUERIES + AVG_QUERIES)
def test_every_query_is_budget_aware(survey, cases, name, args):
    api = A.make_api(survey, EPS, budget=10 * EPS)
    before = A.budget_used(api)
    getattr(api, name)(*args(cases))
    assert A.budget_used(api) > before, f"{name} does not spend any budget"


# Budgets in the histogram tests are large, so that charging once per bar
# (allowed, see test_histogram_charged_once) does not run out.


def test_histogram_has_fixed_bins(survey, cases):
    api = A.make_api(survey, EPS, budget=1000 * EPS)
    big = A.age_histogram(api, cases["big_county"])
    small = A.age_histogram(api, cases["small_county"])
    assert len(big) == len(small), "the histogram has a different number of bins per county; use a fixed age range"


def test_histogram_reflects_api_data(survey, cases):
    county = cases["small_county"]
    zipcode = survey[survey.County == county].Zipcode.iloc[0]
    spiked = add_person(survey, zipcode, 40, n=200)
    api = A.make_api(spiked, EPS, budget=1000 * EPS)
    here = np.array(A.age_histogram(api, county), dtype=float)
    other = np.array(A.age_histogram(api, cases["big_county"]), dtype=float)
    assert here.max() > 150, (
        "200 diabetics aged 40 were added to the API's data for this county, but its histogram does not show them. "
        "Does the histogram read survey.csv directly instead of using the API?"
    )
    assert other.max() < 150, "the 200 added diabetics also show up in another county's histogram; is the county ignored?"


def test_budget_shared_across_histograms(survey, cases):
    api = A.make_api(survey, EPS, budget=1000 * EPS)
    A.age_histogram(api, cases["big_county"])
    one = A.budget_used(api)
    A.age_histogram(api, cases["big_county"])
    assert one > 0, "a histogram spends no budget"
    assert budget_close(A.budget_used(api), 2 * one), (
        "a second histogram of the same county did not add to the budget; use one budget for all calls"
    )


def test_histogram_charged_once(survey, cases):
    api = A.make_api(survey, EPS, budget=1000 * EPS)
    A.age_histogram(api, cases["big_county"])
    used = A.budget_used(api)
    if not budget_close(used, EPS):
        warnings.warn(
            f"one histogram spent {used:g} at epsilon {EPS} per query. The age bins are disjoint, so parallel "
            "composition lets you charge it once. Not a failure, but explain your choice in the report."
        )


def budget_close(x, y):
    return math.isclose(x, y, rel_tol=1e-6, abs_tol=1e-9)


# ---------------------------------------------------------------- Task 4


DELTA = 1e-6


def test_gaussian_noise_is_gaussian(survey, cases):
    out = samples(lambda: A.make_gaussian_api(survey, 0.5, DELTA).getDiabeticsByAge(cases["big_age"]))
    centred = out - out.mean()
    kurtosis = np.mean(centred**4) / np.mean(centred**2) ** 2 - 3
    assert kurtosis < 1.5, f"excess kurtosis {kurtosis:.1f}: the noise looks Laplace (3), not Gaussian (0)"


def test_gaussian_count_is_dp(survey, cases):
    eps = 0.5
    neighbour = add_person(survey, cases["zip1"], 30)
    a = samples(lambda: A.make_gaussian_api(survey, eps, DELTA).getDiabeticsByZip(cases["zip1"]))
    b = samples(lambda: A.make_gaussian_api(neighbour, eps, DELTA).getDiabeticsByZip(cases["zip1"]))
    acc = distinguish(a, b)
    assert acc < dp_bound(eps, DELTA) + 0.05, f"adding one person can be detected {acc:.0%} of the time"


def test_privacy_loss_reports_delta(survey, cases):
    api = A.make_gaussian_api(survey, 0.5, DELTA, budget=100)
    api.getDiabeticsByCounty(cases["big_county"])
    eps1, delta1 = A.privacy_loss(api)
    for _ in range(9):
        api.getDiabeticsByCounty(cases["big_county"])
    eps10, delta10 = A.privacy_loss(api)
    assert delta1 > 0 and delta10 > 0, "the Gaussian API reports delta = 0"
    assert eps10 > eps1 > 0, "epsilon' does not grow with the number of calls"


def test_accountant_is_sublinear():
    std = 10.0
    one = A.gaussian_total_epsilon(1, std, DELTA)
    many = A.gaussian_total_epsilon(100, std, DELTA)
    assert one < many, "epsilon' does not grow with the number of calls"
    assert many < 100 * one / 2, "100 calls cost about 100 times one call; is the accountant just summing epsilon?"


def test_laplace_gaussian_crossover():
    std = 10.0
    assert A.laplace_total_epsilon(1, std) < A.gaussian_total_epsilon(1, std, DELTA), (
        "for a single call at equal noise, Laplace should cost less epsilon than Gaussian"
    )
    assert A.laplace_total_epsilon(100, std) > A.gaussian_total_epsilon(100, std, DELTA), (
        "for 100 calls at equal noise, Gaussian with an accountant should cost less epsilon than Laplace"
    )
