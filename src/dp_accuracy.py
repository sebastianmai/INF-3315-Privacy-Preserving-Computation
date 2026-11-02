"""Task 2: accuracy of the DP queries in code1.py compared with the plain ones.

Run from src/:  python dp_accuracy.py
For each query, on a large and a small group, prints the true value and the
mean absolute error of the DP version over RUNS runs at each epsilon, and
writes the same table to ../report/dp_accuracy_table.tex.
"""

from pathlib import Path

import numpy as np
import pandas as pd

import code1

REPORT = Path(__file__).parent.parent / 'report'

EPSILONS = [0.1, 1, 10]
RUNS = 100

survey = code1.survey
diabetics = survey[survey['Diabetic'] == 1]


def groups(by: list[str]) -> dict[str, tuple]:
    """The group with the most diabetics and one with the fewest (at least one)."""
    sizes = diabetics.groupby(by).size().sort_values(kind='stable')
    key = lambda k: k if isinstance(k, tuple) else (k,)
    return {'large': (key(sizes.index[-1]), sizes.iloc[-1]),
            'small': (key(sizes.index[0]), sizes.iloc[0])}

QUERIES = [
    ('getDiabeticsByZip', ['Zipcode']),
    ('getDiabeticsByCounty', ['County']),
    ('getDiabeticsByAge', ['Age']),
    ('getDiabeticsByCountyAge', ['County', 'Age']),
    ('getAverageAge', []),
    ('getAvgAgeByCounty', ['County']),
    ('getAvgAgeByZip', ['Zipcode']),
]

def accuracy_table() -> pd.DataFrame:
    rows = []
    for name, by in QUERIES:
        plain, dp = getattr(code1, name), getattr(code1, name + 'DP')
        cases = groups(by) if by else {'all': ((), len(diabetics))}
        for group, (args, n) in cases.items():
            true = float(plain(*args))
            row = {'Query': name, 'Group': group, 'Arguments': ', '.join(map(str, args)) or '-',
                   'Diabetics': n, 'True value': round(true, 2)}
            for eps in EPSILONS:
                errors = [abs(dp(*args, epsilon=eps) - true) for _ in range(RUNS)]
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
    table = accuracy_table()
    print(f'Mean absolute error of the DP queries over {RUNS} runs '
          f'(n = number of diabetics in the group)\n')
    print(table.to_string(index=False))
    REPORT.mkdir(exist_ok=True)
    (REPORT / 'dp_accuracy_table.tex').write_text(to_latex(table))
    print(f'\nLaTeX table written to {REPORT / "dp_accuracy_table.tex"}')
