"""Task 2: differentially private versions of the Task 1 queries, and their accuracy.

Run from src/:  python task2.py
For each query, on a large and a small group, prints the true value and the
mean absolute error of the DP version over RUNS runs at each epsilon, and
writes the same table to ../report/dp_accuracy_table.tex.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from task1 import SurveyAPI, load_survey

REPORT = Path(__file__).parent.parent / 'report'


def laplace_mechanism(value, epsilon, sensitivity):
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)
    return value + noise

# Diabetic is 0/1, so one person changes a count by at most 1.
COUNT_SENSITIVITY = 1

# Default privacy parameter.
EPSILON = 1.0

# Public upper bound on age. Must not be derived from the data.
AGE_MAX = 100

class DiabetesAPI(SurveyAPI):
    """The seven Task 1 queries, each answered with epsilon-DP Laplace noise."""

    def __init__(self, survey: pd.DataFrame, epsilon: float = EPSILON):
        super().__init__(survey)
        self.epsilon = epsilon

    def _noise(self, value: float, sensitivity: float, epsilon: float) -> float:
        return laplace_mechanism(value, epsilon, sensitivity)

    def _noisyCount(self, value: int) -> int:
        # Post-processing: round to a non-negative integer.
        return max(0, round(self._noise(value, COUNT_SENSITIVITY, self.epsilon)))

    def _noisyMeanAge(self, ages: pd.Series) -> float:
        # A mean has no fixed sensitivity, so release a noisy sum of clipped ages
        # (sensitivity AGE_MAX) and a noisy count (sensitivity 1), each with
        # epsilon/2. By sequential composition the result is epsilon-DP.
        ages = ages.clip(0, AGE_MAX)
        noisy_sum = self._noise(ages.sum(), AGE_MAX, self.epsilon / 2)
        noisy_count = self._noise(len(ages), COUNT_SENSITIVITY, self.epsilon / 2)
        return float(np.clip(noisy_sum / max(noisy_count, 1), 0, AGE_MAX))

    def _count(self, condition: str, **params) -> int:
        return self._noisyCount(super()._count(condition, **params))

    def _meanAge(self, condition: str, **params) -> float:
        return self._noisyMeanAge(self._rows('Diabetic == 1 and ' + condition, **params)['Age'])


# Accuracy of the DP queries compared with the plain ones

EPSILONS = [0.1, 1, 10]
RUNS = 100

QUERIES = [
    ('getDiabeticsByZip', ['Zipcode']),
    ('getDiabeticsByCounty', ['County']),
    ('getDiabeticsByAge', ['Age']),
    ('getDiabeticsByCountyAge', ['County', 'Age']),
    ('getAverageAge', []),
    ('getAvgAgeByCounty', ['County']),
    ('getAvgAgeByZip', ['Zipcode']),
]

def groups(diabetics: pd.DataFrame, by: list[str]) -> dict[str, tuple]:
    """The group with the most diabetics and one with the fewest (at least one)."""
    sizes = diabetics.groupby(by).size().sort_values(kind='stable')
    key = lambda k: k if isinstance(k, tuple) else (k,)
    return {'large': (key(sizes.index[-1]), sizes.iloc[-1]),
            'small': (key(sizes.index[0]), sizes.iloc[0])}

def accuracy_table(survey: pd.DataFrame) -> pd.DataFrame:
    diabetics = survey[survey['Diabetic'] == 1]
    plain = SurveyAPI(survey)
    private = {eps: DiabetesAPI(survey, eps) for eps in EPSILONS}
    rows = []
    for name, by in QUERIES:
        cases = groups(diabetics, by) if by else {'all': ((), len(diabetics))}
        for group, (args, n) in cases.items():
            true = float(getattr(plain, name)(*args))
            row = {'Query': name, 'Group': group, 'Arguments': ', '.join(map(str, args)) or '-',
                   'Diabetics': n, 'True value': round(true, 2)}
            for eps, api in private.items():
                errors = [abs(getattr(api, name)(*args) - true) for _ in range(RUNS)]
                row[f'MAE eps={eps:g}'] = round(float(np.mean(errors)), 2)
            rows.append(row)
    return pd.DataFrame(rows)

def to_latex(table: pd.DataFrame) -> str:
    header = ' & '.join(['Query', 'Group', 'Arguments', '$n$', 'True']
                        + [f'$\\varepsilon={e:g}$' for e in EPSILONS])
    lines = [r'\begin{tabular}{lllrr' + 'r' * len(EPSILONS) + '}', r'\hline',
             header + r' \\', r'\hline']
    for _, r in table.iterrows():
        cells = [f'\\texttt{{{r["Query"]}}}', r['Group'], r['Arguments'], str(r['Diabetics']),
                 f'{r["True value"]:g}'] + [f'{r[f"MAE eps={e:g}"]:g}' for e in EPSILONS]
        lines.append(' & '.join(cells) + r' \\')
    lines += [r'\hline', r'\end{tabular}']
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    np.random.seed(0)  # only so the table in the report is reproducible
    table = accuracy_table(load_survey())
    print(f'Mean absolute error of the DP queries over {RUNS} runs '
          f'(n = number of diabetics in the group)\n')
    print(table.to_string(index=False))
    REPORT.mkdir(exist_ok=True)
    (REPORT / 'dp_accuracy_table.tex').write_text(to_latex(table))
    print(f'\nLaTeX table written to {REPORT / "dp_accuracy_table.tex"}')
