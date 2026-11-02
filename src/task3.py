"""Task 3: a privacy budget for the DP API, and a DP age histogram.

Run from src/:  python task3.py
Calls getAgeHistogram for a few counties on an API with a budget, showing the
privacy loss epsilon' after each call until the budget runs out, compares the
true and the DP histogram, and compares bin widths. Writes the comparison plot
to ../report/histogram_dp.pdf.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from task1 import load_survey
from task2 import AGE_MAX, COUNT_SENSITIVITY, EPSILON, DiabetesAPI

REPORT = Path(__file__).parent.parent / 'report'

# Total epsilon the API may spend.
BUDGET = 5.0

# Fixed age bins 0-9, 10-19, ..., 90-99, chosen without looking at the data.
# Older ages fall in the last bin.
AGE_RANGE = 100
BIN_WIDTH = 10


class PrivacyBudget:
    def __init__(self, budget):
        self.budget = budget
        self.used = 0

    def use_budget(self, epsilon):
        if self.used + epsilon > self.budget:
            return False
        self.used += epsilon
        return True


class PrivacyBudgetExceeded(Exception):
    pass


class BudgetedDiabetesAPI(DiabetesAPI):
    """The Task 2 API with a privacy budget and a histogram query.

    Every call spends epsilon from one budget shared by all queries
    (sequential composition), so the privacy loss epsilon' is budget.used.
    budget=None means no limit, but the loss is still tracked.
    """

    def __init__(self, survey: pd.DataFrame, epsilon: float = EPSILON, budget: float | None = BUDGET,
                 bin_width: int = BIN_WIDTH):
        super().__init__(survey, epsilon)
        self.budget = PrivacyBudget(np.inf if budget is None else budget)
        self.bin_width = bin_width

    @property
    def privacy_loss(self) -> float:
        return self.budget.used

    def _spend(self, *releases: tuple[float, float]) -> None:
        """Charge one call made of noisy releases (sensitivity, epsilon), or reject it before any noise is drawn."""
        cost = sum(epsilon for _, epsilon in releases)
        if not self.budget.use_budget(cost):
            raise PrivacyBudgetExceeded(
                f'Privacy budget exceeded - try again later. '
                f'(used epsilon = {self.budget.used:g} of {self.budget.budget:g}, this call needs {cost:g})')

    def _count(self, condition: str, **params) -> int:
        self._spend((COUNT_SENSITIVITY, self.epsilon))
        return super()._count(condition, **params)

    def _meanAge(self, condition: str, **params) -> float:
        # Sum and count each get epsilon/2, so together they cost epsilon.
        self._spend((AGE_MAX, self.epsilon / 2), (COUNT_SENSITIVITY, self.epsilon / 2))
        return super()._meanAge(condition, **params)

    def getDiabeticsByAgeHistogram(self, county: str) -> list[int]:
        """Noisy count of diabetics in `county` per age bin, in one call.

        The bins are disjoint, so each person changes at most one bar by at
        most 1. By parallel composition the whole histogram is epsilon-DP and
        is charged once, not once per bin.
        """
        self._spend((COUNT_SENSITIVITY, self.epsilon))
        ages = self._rows('Diabetic == 1 and County == @county', county=county)['Age']
        return [self._noisyCount(count) for count in age_bins(ages, self.bin_width)]


def age_bins(ages: pd.Series, bin_width: int = BIN_WIDTH) -> np.ndarray:
    """Number of ages in each fixed bin of width `bin_width` over 0..AGE_RANGE-1."""
    n_bins = -(-AGE_RANGE // bin_width)
    index = ages.clip(0, AGE_RANGE - 1) // bin_width
    return np.bincount(index, minlength=n_bins)

def bin_labels(bin_width: int = BIN_WIDTH) -> list[str]:
    return [f'{lo}-{min(lo + bin_width, AGE_RANGE) - 1}' for lo in range(0, AGE_RANGE, bin_width)]


# Front end: no access to the database, only to the API.

def getAgeHistogram(county: str, api: BudgetedDiabetesAPI) -> list[int]:
    return api.getDiabeticsByAgeHistogram(county)


# Comparison of the true and the DP histogram

def true_histogram(survey: pd.DataFrame, county: str, bin_width: int = BIN_WIDTH) -> np.ndarray:
    ages = survey.query('Diabetic == 1 and County == @county')['Age']
    return age_bins(ages, bin_width)

def plot_comparison(true: np.ndarray, noisy: list[int], county: str, path: Path) -> None:
    x = np.arange(len(true))
    fig, ax = plt.subplots(figsize=(8, 4), layout='constrained')
    ax.bar(x - 0.2, true, width=0.38, color='#2a78d6', label='True')
    ax.bar(x + 0.2, noisy, width=0.38, color='#eb6834', label=f'DP (epsilon = {EPSILON:g})')
    ax.set_xticks(x, bin_labels())
    ax.set_xlabel('Age')
    ax.set_ylabel('Diabetics')
    ax.set_title(f'Diabetics by age in {county}: true and DP histogram', loc='left')
    ax.grid(axis='y', color='#e4e3df', linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ['top', 'right', 'left']:
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0, colors='#52514e')
    ax.legend(frameon=False)
    fig.savefig(path)
    plt.close(fig)

def bin_width_errors(survey: pd.DataFrame, county: str, widths: list[int], runs: int = 100) -> pd.DataFrame:
    """Mean absolute error per bar, and relative to the mean non-empty bar, for each bin width."""
    rows = []
    for width in widths:
        api = BudgetedDiabetesAPI(survey, budget=None, bin_width=width)
        true = true_histogram(survey, county, width)
        errors = np.array([np.abs(np.array(api.getDiabeticsByAgeHistogram(county)) - true) for _ in range(runs)])
        rows.append({'Bin width': width, 'Bins': len(true), 'Mean bar (non-empty)': true[true > 0].mean().round(1),
                     'MAE per bar': errors.mean().round(2),
                     'Relative error': (errors[:, true > 0].mean() / true[true > 0].mean()).round(3)})
    return pd.DataFrame(rows)


if __name__ == '__main__':
    np.random.seed(0)  # only so the output in the report is reproducible
    survey = load_survey()
    api = BudgetedDiabetesAPI(survey)
    print(f'API with epsilon = {api.epsilon:g} per call and a budget of {BUDGET:g}\n')

    for county in ['OSLO', 'BERGEN', 'OSLO', 'TROMSØ', 'AREMARK', 'OSLO']:
        try:
            bars = getAgeHistogram(county, api)
            print(f'getAgeHistogram({county!r}) = {bars}')
        except PrivacyBudgetExceeded as error:
            print(f'getAgeHistogram({county!r}) rejected: {error}')
        print(f"  privacy loss so far: epsilon' = {api.privacy_loss:g} of {BUDGET:g}")

    county = 'OSLO'
    comparison = BudgetedDiabetesAPI(survey, budget=None)
    true = true_histogram(survey, county)
    noisy = getAgeHistogram(county, comparison)
    print(f'\n{county}, true vs. DP (epsilon = {EPSILON:g}):')
    print(pd.DataFrame({'Age': bin_labels(), 'True': true, 'DP': noisy}).to_string(index=False))

    small = 'AREMARK'
    print(f'\n{small}, true vs. DP: {true_histogram(survey, small).tolist()} vs. '
          f'{getAgeHistogram(small, comparison)}')

    print(f'\nError per bar in {county} by bin width (100 runs each, epsilon = {EPSILON:g}):')
    print(bin_width_errors(survey, county, [5, 10, 20]).to_string(index=False))

    REPORT.mkdir(exist_ok=True)
    plot_comparison(true, noisy, county, REPORT / 'histogram_dp.pdf')
    print(f'\nPlot written to {REPORT / "histogram_dp.pdf"}')
