from pathlib import Path

import numpy as np
import pandas as pd

survey = pd.read_csv(Path(__file__).with_name('survey.csv'), dtype={'Zipcode': str})


# Task 1: survey queries

def getDiabeticsByZip(zip: str) -> int:
    return survey.query('Zipcode == @zip')['Diabetic'].sum()

def getDiabeticsByCounty(county: str) -> int:
    return survey.query('County == @county')['Diabetic'].sum()

def getDiabeticsByAge(age: int) -> int:
    return survey.query('Age == @age')['Diabetic'].sum()

def getDiabeticsByCountyAge(county: str, age: int) -> int:
    return survey.query('County==@county and Age==@age')['Diabetic'].sum()

def getAverageAge() -> float:
    return survey.query('Diabetic == 1')['Age'].mean()

def getAvgAgeByCounty(county: str) -> float:
    return survey.query('Diabetic == 1 and County == @county')['Age'].mean()

def getAvgAgeByZip(zip: str) -> float:
    return survey.query('Diabetic == 1 and Zipcode == @zip')['Age'].mean()


# Task 2: differentially private versions

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

def _noisyCount(value: int, epsilon: float) -> int:
    # Post-processing: round to a non-negative integer.
    return max(0, round(laplace_mechanism(value, epsilon, COUNT_SENSITIVITY)))

def getDiabeticsByZipDP(zip: str, epsilon: float = EPSILON) -> int:
    return _noisyCount(getDiabeticsByZip(zip), epsilon)

def getDiabeticsByCountyDP(county: str, epsilon: float = EPSILON) -> int:
    return _noisyCount(getDiabeticsByCounty(county), epsilon)

def getDiabeticsByAgeDP(age: int, epsilon: float = EPSILON) -> int:
    return _noisyCount(getDiabeticsByAge(age), epsilon)

def getDiabeticsByCountyAgeDP(county: str, age: int, epsilon: float = EPSILON) -> int:
    return _noisyCount(getDiabeticsByCountyAge(county, age), epsilon)

def _noisyMeanAge(rows: pd.DataFrame, epsilon: float) -> float:
    # A mean has no fixed sensitivity, so release a noisy sum of clipped ages
    # (sensitivity AGE_MAX) and a noisy count (sensitivity 1), each with
    # epsilon/2. By sequential composition the result is epsilon-DP.
    ages = rows['Age'].clip(0, AGE_MAX)
    noisy_sum = laplace_mechanism(ages.sum(), epsilon / 2, AGE_MAX)
    noisy_count = laplace_mechanism(len(ages), epsilon / 2, COUNT_SENSITIVITY)
    return float(np.clip(noisy_sum / max(noisy_count, 1), 0, AGE_MAX))

def getAverageAgeDP(epsilon: float = EPSILON) -> float:
    return _noisyMeanAge(survey.query('Diabetic == 1'), epsilon)

def getAvgAgeByCountyDP(county: str, epsilon: float = EPSILON) -> float:
    return _noisyMeanAge(survey.query('Diabetic == 1 and County == @county'), epsilon)

def getAvgAgeByZipDP(zip: str, epsilon: float = EPSILON) -> float:
    return _noisyMeanAge(survey.query('Diabetic == 1 and Zipcode == @zip'), epsilon)


# The seven DP queries as one API object on a given survey, for a4_adapter.py.

class DiabetesAPI:
    def __init__(self, survey: pd.DataFrame, epsilon: float = EPSILON):
        self.survey = survey
        self.epsilon = epsilon

    def _count(self, condition: str, **params) -> int:
        return _noisyCount(self.survey.query(condition, local_dict=params)['Diabetic'].sum(), self.epsilon)

    def _meanAge(self, condition: str, **params) -> float:
        return _noisyMeanAge(self.survey.query('Diabetic == 1 and ' + condition, local_dict=params), self.epsilon)

    def getDiabeticsByZip(self, zip: str) -> int:
        return self._count('Zipcode == @zip', zip=zip)

    def getDiabeticsByCounty(self, county: str) -> int:
        return self._count('County == @county', county=county)

    def getDiabeticsByAge(self, age: int) -> int:
        return self._count('Age == @age', age=age)

    def getDiabeticsByCountyAge(self, county: str, age: int) -> int:
        return self._count('County == @county and Age == @age', county=county, age=age)

    def getAverageAge(self) -> float:
        return self._meanAge('True')

    def getAvgAgeByCounty(self, county: str) -> float:
        return self._meanAge('County == @county', county=county)

    def getAvgAgeByZip(self, zip: str) -> float:
        return self._meanAge('Zipcode == @zip', zip=zip)
