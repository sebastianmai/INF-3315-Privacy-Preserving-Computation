"""Task 1: re-identification risk of the survey API, using the public tax registry (pii.csv).

Run from src/:  python reidentify.py
Prints the k-anonymity figures and an example attack, and writes the heatmap
to ../report/heatmap_county_age.pdf.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

import code1

HERE = Path(__file__).parent
REPORT = HERE.parent / 'report'

# Attributes survey.csv and pii.csv share (the quasi-identifier).
QI = ['Zipcode', 'County', 'Age']

# Cells with fewer respondents than this are flagged as sparse.
SPARSE = 5

survey = code1.survey
registry = pd.read_csv(HERE / 'pii.csv', dtype={'Zipcode': str, 'PNR': str})
registry['Name'] = registry['Name'].str.strip()


# k-anonymity of the link

def link(survey: pd.DataFrame, registry: pd.DataFrame) -> pd.DataFrame:
    """Each respondent with k = the number of registry entries sharing their quasi-identifier."""
    k = registry.groupby(QI).size().rename('k')
    linked = survey.join(k, on=QI)
    linked['k'] = linked['k'].fillna(0).astype(int)
    return linked

def k_table(linked: pd.DataFrame) -> pd.DataFrame:
    labels = ['0 (no match)', '1 (unique)', '2', '3-4', '5-9', '10+']
    groups = pd.cut(linked['k'], bins=[-0.5, 0.5, 1.5, 2.5, 4.5, 9.5, np.inf], labels=labels)
    counts = groups.value_counts().reindex(labels)
    return pd.DataFrame({'respondents': counts, 'share': (counts / len(linked)).round(4)})


# What the API reveals about a named person

def reveal_by_zip(registry: pd.DataFrame) -> pd.DataFrame:
    """Named people whose diabetes status follows from two API calls on their zip code.

    getDiabeticsByZip(zip) == 0  -> nobody in the zip is diabetic.
    getDiabeticsByZip(zip) == 1  -> getAvgAgeByZip(zip) is the age of the one
    diabetic; if only one registry entry in the zip has that age, that is them.
    """
    rows = []
    for zip in registry['Zipcode'].unique():
        n = code1.getDiabeticsByZip(zip)
        people = registry[registry['Zipcode'] == zip]
        if n == 0:
            rows.append(people.assign(Diabetic=0, Calls=f'getDiabeticsByZip({zip}) = 0'))
        elif n == 1:
            age = code1.getAvgAgeByZip(zip)
            match = people[people['Age'] == age]
            if len(match) == 1:
                rows.append(match.assign(Diabetic=1, Calls=f'getDiabeticsByZip({zip}) = 1, '
                                                           f'getAvgAgeByZip({zip}) = {age:g}'))
    return pd.concat(rows, ignore_index=True)


# Heatmap of respondents per {County, Age}

COUNT_BOUNDS = [0, 1, SPARSE, 10, 25, 50, np.inf]
COUNT_LABELS = ['0', f'1-{SPARSE - 1} (sparse)', f'{SPARSE}-9', '10-24', '25-49', '50+']
COUNT_COLORS = ['#fcfcfb', '#d03b3b', '#cde2fb', '#86b6ef', '#3987e5', '#1c5cab']

def plot_heatmap(table: pd.DataFrame, title: str, path: Path) -> None:
    cmap = ListedColormap(COUNT_COLORS)
    norm = BoundaryNorm([b - 0.5 if b != np.inf else 1e9 for b in COUNT_BOUNDS], cmap.N)
    fig, ax = plt.subplots(figsize=(10, 13), layout='constrained')
    ax.pcolormesh(table.values, cmap=cmap, norm=norm)
    ax.invert_yaxis()

    step = max(1, len(table.columns) // 15)
    ax.set_xticks(np.arange(0, len(table.columns), step) + 0.5, table.columns[::step])
    ax.set_yticks(np.arange(0, len(table.index), 20) + 0.5, table.index[::20], fontsize=7)
    ax.set_xlabel(table.columns.name)
    ax.set_ylabel('County (sorted by number of respondents, every 20th labelled)')
    ax.set_title(title, loc='left')
    for side in ax.spines.values():
        side.set_visible(False)
    ax.tick_params(length=0, colors='#52514e')

    handles = [Patch(facecolor=c, edgecolor='#52514e', linewidth=0.5, label=l)
               for c, l in zip(COUNT_COLORS, COUNT_LABELS)]
    ax.legend(handles=handles, title='Respondents in cell', loc='upper left',
              bbox_to_anchor=(1.01, 1), frameon=False)
    fig.savefig(path)
    plt.close(fig)

def county_table(survey: pd.DataFrame, column: str) -> pd.DataFrame:
    table = survey.pivot_table(index='County', columns=column, values='PatientID',
                               aggfunc='size', fill_value=0, observed=False)
    return table.loc[table.sum(axis=1).sort_values(ascending=False).index]

def sparse_share(table: pd.DataFrame) -> tuple[int, int, int]:
    """(non-empty cells, sparse cells, respondents in sparse cells)."""
    cells = table.values[table.values > 0]
    sparse = cells[cells < SPARSE]
    return len(cells), len(sparse), int(sparse.sum())


if __name__ == '__main__':
    linked = link(survey, registry)
    print(f'Linking {len(survey)} survey respondents to {len(registry)} registry entries on {QI}\n')
    print(k_table(linked).to_string(), '\n')

    # Equivalence classes inside the survey itself, for comparison.
    k_survey = survey.groupby(QI)['PatientID'].transform('size')
    print(f'Unique within the survey on {QI}: {(k_survey == 1).sum()}')
    k_zip_age = registry.groupby(['Zipcode', 'Age'])['Name'].transform('size')
    print(f'Unique in the registry on Zipcode+Age alone: {(k_zip_age == 1).sum()} '
          f'(County adds nothing: every zip code lies in one county)')
    k_county_age = registry.groupby(['County', 'Age'])['Name'].transform('size')
    print(f'Unique in the registry on County+Age (if the zip code were dropped): {(k_county_age == 1).sum()}\n')

    unique = linked[linked['k'] == 1].merge(registry, on=QI)
    print(f'Uniquely re-identified respondents (k = 1): {len(unique)}; '
          f'of them diabetic: {unique["Diabetic"].sum()}\n')

    revealed = reveal_by_zip(registry)
    print(f'Named people whose diabetes status two zip-code API calls reveal: {len(revealed)} '
          f'({revealed["Diabetic"].sum()} diabetic, {(revealed["Diabetic"] == 0).sum()} not diabetic)')
    example = revealed[revealed['Diabetic'] == 1].sort_values('Name').iloc[0]
    print(f'Example: {example["Name"]} (PNR {example["PNR"]}), age {example["Age"]}, '
          f'{example["Zipcode"]} {example["County"]}')
    print(f'  {example["Calls"]}')
    print(f'  -> the only diabetic in {example["Zipcode"]} is {example["Age"]}, and {example["Name"]} is the only '
          f'person of that age there: diabetic')
    print(f'  getDiabeticsByCountyAge({example["County"]!r}, {example["Age"]}) = '
          f'{code1.getDiabeticsByCountyAge(example["County"], example["Age"])}\n')

    by_age = county_table(survey, 'Age')
    cells, sparse, people = sparse_share(by_age)
    print(f'County x Age: {cells} non-empty cells, {sparse} sparse (< {SPARSE}) = {sparse / cells:.0%}, '
          f'holding {people} respondents = {people / len(survey):.0%}')

    REPORT.mkdir(exist_ok=True)
    plot_heatmap(by_age, 'Survey respondents per {County, Age}', REPORT / 'heatmap_county_age.pdf')
    print(f'\nHeatmap written to {REPORT / "heatmap_county_age.pdf"}')
