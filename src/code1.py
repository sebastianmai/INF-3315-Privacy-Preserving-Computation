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

# Public upper bound on age. Must not be derived from the data.
AGE_MAX = 100

def getDiabeticsByZipDP(zip: str, epsilon: float) -> float:
    return laplace_mechanism(getDiabeticsByZip(zip), epsilon, COUNT_SENSITIVITY)

def getDiabeticsByCountyDP(county: str, epsilon: float) -> float:
    return laplace_mechanism(getDiabeticsByCounty(county), epsilon, COUNT_SENSITIVITY)

def getDiabeticsByAgeDP(age: int, epsilon: float) -> float:
    return laplace_mechanism(getDiabeticsByAge(age), epsilon, COUNT_SENSITIVITY)

def getDiabeticsByCountyAgeDP(county: str, age: int, epsilon: float) -> float:
    return laplace_mechanism(getDiabeticsByCountyAge(county, age), epsilon, COUNT_SENSITIVITY)

def _noisyMeanAge(rows: pd.DataFrame, epsilon: float) -> float:
    # A mean has no fixed sensitivity, so release a noisy sum of clipped ages
    # (sensitivity AGE_MAX) and a noisy count (sensitivity 1), each with
    # epsilon/2. By sequential composition the result is epsilon-DP.
    ages = rows['Age'].clip(0, AGE_MAX)
    noisy_sum = laplace_mechanism(ages.sum(), epsilon / 2, AGE_MAX)
    noisy_count = laplace_mechanism(len(ages), epsilon / 2, COUNT_SENSITIVITY)
    return float(np.clip(noisy_sum / max(noisy_count, 1), 0, AGE_MAX))

def getAverageAgeDP(epsilon: float) -> float:
    return _noisyMeanAge(survey.query('Diabetic == 1'), epsilon)

def getAvgAgeByCountyDP(county: str, epsilon: float) -> float:
    return _noisyMeanAge(survey.query('Diabetic == 1 and County == @county'), epsilon)

def getAvgAgeByZipDP(zip: str, epsilon: float) -> float:
    return _noisyMeanAge(survey.query('Diabetic == 1 and Zipcode == @zip'), epsilon)
