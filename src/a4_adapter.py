"""Connect your A4 code to test_a4.py.

Fill in each function so that it calls your own code. Do not change the
names or signatures: the tests call these and nothing else. You may keep
your own design; this file only translates between it and the tests.

Every API object must read its data from the `survey` DataFrame passed in,
not from survey.csv, so the tests can run it on modified data.
"""

import pandas as pd

import task2
import task3
import task4

# Task 2: the fixed bounds [L, U] you clamp ages to (chosen without looking at the data).
AGE_BOUNDS = (0, task2.AGE_MAX)


def make_api(survey: pd.DataFrame, epsilon: float, budget: float | None = None):
    """Task 2 and 3: return your Laplace DP API built on `survey`.

    The object must have the seven methods from Task 1, with the same names
    and arguments: getDiabeticsByZip(zip), getDiabeticsByCounty(county),
    getDiabeticsByAge(age), getDiabeticsByCountyAge(county, age),
    getAverageAge(), getAvgAgeByCounty(county), getAvgAgeByZip(zip).
    Each call spends `epsilon` and returns only the noisy, post-processed value.

    budget=None means no budget (Task 2). With a budget (Task 3), a call that
    would exceed it must raise an exception with a clear message.
    """
    return task3.BudgetedDiabetesAPI(survey, epsilon, budget)


def age_histogram(api, county: str) -> list:
    """Task 3: your getAgeHistogram for `county`, using only `api`."""
    return task3.getAgeHistogram(county, api)


def budget_used(api) -> float:
    """Task 3: the total epsilon spent so far by `api`."""
    return api.privacy_loss


def make_gaussian_api(survey: pd.DataFrame, epsilon: float, delta: float, budget: float | None = None):
    """Task 4: as make_api, but with Gaussian noise and (epsilon, delta) accounting."""
    return task4.GaussianDiabetesAPI(survey, epsilon, delta, budget)


def privacy_loss(api) -> tuple:
    """Task 4: the total (epsilon', delta) that `api` reports to the user."""
    return api.privacy_loss, api.delta


def laplace_total_epsilon(k: int, noise_std: float) -> float:
    """Task 4: total epsilon of k Laplace count queries (sensitivity 1) whose noise has this standard deviation."""
    return task4.laplace_total_epsilon(k, noise_std)


def gaussian_total_epsilon(k: int, noise_std: float, delta: float) -> float:
    """Task 4: total epsilon from your accountant for k Gaussian count queries (sensitivity 1) with this standard deviation."""
    return task4.gaussian_total_epsilon(k, noise_std, delta)
