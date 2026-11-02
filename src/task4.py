"""Task 4: Gaussian noise with an RDP accountant, compared with Laplace noise.

Run from src/:  python task4.py
Runs repeated queries on the Gaussian API until its budget runs out, showing
the privacy loss (epsilon', delta), and compares the total epsilon' of Laplace
and Gaussian noise at the same standard deviation per call as the number of
calls grows. Writes the comparison plot to ../report/epsilon_vs_calls.pdf.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from task1 import load_survey
from task2 import COUNT_SENSITIVITY
from task3 import BIN_WIDTH, BUDGET, BudgetedDiabetesAPI, PrivacyBudget, PrivacyBudgetExceeded

REPORT = Path(__file__).parent.parent / 'report'

# Fixed for the whole API.
DELTA = 1e-6

# Epsilon per Gaussian call; the mechanism below is only valid for epsilon < 1.
GAUSSIAN_EPSILON = 0.5


def gaussian_sigma(epsilon, delta, sensitivity):
    return sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon

def gaussian_mechanism(value, epsilon, delta, sensitivity):
    sigma = gaussian_sigma(epsilon, delta, sensitivity)
    noise = np.random.normal(0, sigma)
    return value + noise


# RDP accountant

def rdp_to_epsilon(rdp: float, delta: float) -> float:
    """epsilon' = min over alpha > 1 of (alpha * rdp + ln(1/delta) / (alpha - 1)).

    `rdp` is the sum of sensitivity^2 / (2 sigma^2) over all Gaussian releases,
    so the RDP of order alpha is alpha * rdp. With beta = alpha - 1 the term is
    rdp + beta * rdp + ln(1/delta) / beta, smallest at beta = sqrt(ln(1/delta) / rdp),
    which gives rdp + 2 sqrt(rdp * ln(1/delta)).
    """
    if rdp == 0:
        return 0.0
    return rdp + 2 * np.sqrt(rdp * np.log(1 / delta))


class RDPPrivacyBudget(PrivacyBudget):
    """A budget on epsilon' at a fixed delta, tracked with the RDP accountant.

    `used` is the accountant's epsilon' for all calls so far, not a sum of
    per-call epsilons.
    """

    def __init__(self, budget, delta):
        super().__init__(budget)
        self.delta = delta
        self.rdp = 0.0

    def use_rdp(self, rdp):
        epsilon = rdp_to_epsilon(self.rdp + rdp, self.delta)
        if epsilon > self.budget:
            return False
        self.rdp += rdp
        self.used = epsilon
        return True


class GaussianDiabetesAPI(BudgetedDiabetesAPI):
    """The Task 3 API with Gaussian instead of Laplace noise: (epsilon, delta)-DP per call."""

    def __init__(self, survey: pd.DataFrame, epsilon: float = GAUSSIAN_EPSILON, delta: float = DELTA,
                 budget: float | None = BUDGET, bin_width: int = BIN_WIDTH):
        if not 0 < epsilon < 1:
            raise ValueError('the Gaussian mechanism needs 0 < epsilon < 1')
        super().__init__(survey, epsilon, budget, bin_width)
        self.delta = delta
        self.budget = RDPPrivacyBudget(np.inf if budget is None else budget, delta)

    def _noise(self, value: float, sensitivity: float, epsilon: float) -> float:
        return gaussian_mechanism(value, epsilon, self.delta, sensitivity)

    def _spend(self, *releases: tuple[float, float]) -> None:
        rdp = sum(s**2 / (2 * gaussian_sigma(e, self.delta, s)**2) for s, e in releases)
        if not self.budget.use_rdp(rdp):
            needed = rdp_to_epsilon(self.budget.rdp + rdp, self.delta)
            raise PrivacyBudgetExceeded(
                f'Privacy budget exceeded - try again later. '
                f"(epsilon' = {self.budget.used:.3g} of {self.budget.budget:g} at delta = {self.delta:g}; "
                f"this call would bring it to {needed:.3g})")


# Laplace or Gaussian: total epsilon' at the same standard deviation per call

def laplace_total_epsilon(k: int, noise_std: float, sensitivity: float = COUNT_SENSITIVITY) -> float:
    # Laplace with scale b has std sqrt(2) b, and costs sensitivity / b per call.
    # Pure DP composes sequentially: the epsilons add up.
    return k * sensitivity * np.sqrt(2) / noise_std

def gaussian_total_epsilon(k: int, noise_std: float, delta: float = DELTA,
                           sensitivity: float = COUNT_SENSITIVITY) -> float:
    return rdp_to_epsilon(k * sensitivity**2 / (2 * noise_std**2), delta)

def last_laplace_win(noise_std: float, delta: float = DELTA) -> int:
    """The largest number of calls for which Laplace still has the lower total epsilon'."""
    k = 1
    while laplace_total_epsilon(k + 1, noise_std) <= gaussian_total_epsilon(k + 1, noise_std, delta):
        k += 1
    return k if laplace_total_epsilon(1, noise_std) <= gaussian_total_epsilon(1, noise_std, delta) else 0

def comparison_table(noise_std: float, calls: list[int]) -> pd.DataFrame:
    rows = []
    for k in calls:
        lap, gauss = laplace_total_epsilon(k, noise_std), gaussian_total_epsilon(k, noise_std)
        rows.append({'Calls': k, "Laplace epsilon'": round(lap, 3), "Gaussian epsilon'": round(gauss, 3),
                     'Lower': 'Laplace' if lap <= gauss else 'Gaussian'})
    return pd.DataFrame(rows)

def plot_comparison(noise_std: float, max_calls: int, path: Path) -> None:
    k = np.arange(1, max_calls + 1)
    lap = laplace_total_epsilon(k, noise_std)
    gauss = np.array([gaussian_total_epsilon(n, noise_std) for n in k])
    cross = last_laplace_win(noise_std)

    fig, ax = plt.subplots(figsize=(8, 4.5), layout='constrained')
    ax.plot(k, lap, color='#2a78d6', linewidth=2, label='Laplace (pure DP, sequential)')
    ax.plot(k, gauss, color='#eb6834', linewidth=2, label=f'Gaussian (RDP accountant, delta = {DELTA:g})')
    ax.axvline(cross, color='#52514e', linewidth=1, linestyle='--')
    ax.annotate(f'Laplace lower up to {cross} calls', xy=(cross, lap[cross - 1]),
                xytext=(8, -4), textcoords='offset points', ha='left', va='top', color='#0b0b0b', fontsize=9)
    ax.set_xlabel('Number of calls')
    ax.set_ylabel("Total privacy loss epsilon'")
    ax.set_title(f"Total epsilon' at the same noise per call (std = {noise_std:.3g}, sensitivity 1)", loc='left')
    ax.grid(color='#e4e3df', linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ['top', 'right']:
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0, colors='#52514e')
    ax.legend(frameon=False, loc='upper left')
    fig.savefig(path)
    plt.close(fig)


if __name__ == '__main__':
    np.random.seed(0)  # only so the output in the report is reproducible
    survey = load_survey()

    api = GaussianDiabetesAPI(survey)
    sigma = gaussian_sigma(api.epsilon, api.delta, COUNT_SENSITIVITY)
    print(f'Gaussian API: epsilon = {api.epsilon:g} per call, delta = {api.delta:g}, budget epsilon\' = {BUDGET:g}; '
          f'noise std of a count = {sigma:.2f}\n')
    calls = 0
    while True:
        try:
            api.getDiabeticsByCounty('OSLO')
        except PrivacyBudgetExceeded as error:
            print(f'call {calls + 1} rejected: {error}')
            break
        calls += 1
        if calls in (1, 2, 5, 10, 20, 50) or calls % 25 == 0:
            print(f"after {calls:3d} calls: privacy loss (epsilon', delta) = ({api.privacy_loss:.3f}, {api.delta:g})")
    print(f"accepted {calls} calls; the same budget as a sum of per-call epsilons would allow "
          f'{int(BUDGET / api.epsilon)}\n')

    for std in [np.sqrt(2), 10.0]:
        print(f'Same noise per call: std = {std:.3g} '
              f'(Laplace epsilon = {laplace_total_epsilon(1, std):.3g} per call, '
              f'Gaussian rdp = {1 / (2 * std**2):.3g} per call)')
        print(comparison_table(std, [1, 2, 5, 10, 14, 15, 20, 24, 25, 30, 50, 100, 1000]).to_string(index=False))
        print(f'Laplace has the lower total epsilon\' up to {last_laplace_win(std)} calls\n')

    REPORT.mkdir(exist_ok=True)
    plot_comparison(np.sqrt(2), 100, REPORT / 'epsilon_vs_calls.pdf')
    print(f'Plot written to {REPORT / "epsilon_vs_calls.pdf"}')
