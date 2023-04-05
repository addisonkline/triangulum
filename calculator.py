import pandas as pd
import numpy as np
from scipy.stats import norm

def calculate(d1, d2, d3, dfs, elev, lapse): # d1, d2, d3 distances, dfs a list of the corresponding dataframes
    # gets weighted average of the three stations
    max_temps = ((1 - (d1/(d1 + d2 + d3)))/2)*dfs[0].iloc[0].to_numpy() + ((1 - (d2/(d1 + d2 + d3)))/2)*dfs[1].iloc[0].to_numpy() + ((1 - (d3/(d1 + d2 + d3)))/2)*dfs[2].iloc[0].to_numpy()
    min_temps = ((1 - (d1/(d1 + d2 + d3)))/2)*dfs[0].iloc[1].to_numpy() + ((1 - (d2/(d1 + d2 + d3)))/2)*dfs[1].iloc[1].to_numpy() + ((1 - (d3/(d1 + d2 + d3)))/2)*dfs[2].iloc[1].to_numpy()
    precip = ((1 - (d1/(d1 + d2 + d3)))/2)*dfs[0].iloc[2].to_numpy() + ((1 - (d2/(d1 + d2 + d3)))/2)*dfs[1].iloc[2].to_numpy() + ((1 - (d3/(d1 + d2 + d3)))/2)*dfs[2].iloc[2].to_numpy()
    max_temp_std = ((1 - (d1/(d1 + d2 + d3)))/2)*dfs[0].iloc[3].to_numpy() + ((1 - (d2/(d1 + d2 + d3)))/2)*dfs[1].iloc[3].to_numpy() + ((1 - (d3/(d1 + d2 + d3)))/2)*dfs[2].iloc[3].to_numpy()
    min_temp_std = ((1 - (d1/(d1 + d2 + d3)))/2)*dfs[0].iloc[4].to_numpy() + ((1 - (d2/(d1 + d2 + d3)))/2)*dfs[1].iloc[4].to_numpy() + ((1 - (d3/(d1 + d2 + d3)))/2)*dfs[2].iloc[4].to_numpy()

    # calculates daily mean from max and min
    mean_temps = (max_temps + min_temps) / 2

    # calculates adjusts for elevation
    max_temps = max_temps - ((elev/1000)*lapse)
    min_temps = min_temps - ((elev/1000)*lapse)

    # create df from above information
    df = pd.DataFrame(data=np.array([max_temps, mean_temps, min_temps, precip, max_temp_std, min_temp_std]), index=['Monthly Mean Max Temp (F)', 'Daily Mean Temp (F)', 'Monthly Mean Min Temp (F)', 'Precip (in)', 'Monthly Max Temp StdDev (F)', 'Monthly Min Temp StdDev (F)'], columns=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])

    # add col of annual values (means for temp, total for precip)
    df['Year'] = np.array([np.mean(df.iloc[0]), np.mean(df.iloc[1]), np.mean(df.iloc[2]), np.sum(df.iloc[3]), np.mean(df.iloc[4]), np.mean(df.iloc[5])])

    # round final df accordingly: 1 decimal place for temperature, 2 for precip
    df.iloc[0:3] = df.iloc[0:3].round(1)
    df.iloc[4:6] = df.iloc[4:6].round(1)
    df.iloc[3] = df.iloc[3].round(2)

    return df

def normal_probabilities(df):
    # percentiles of monthly mean maximum
    max_temps_p95 = norm.ppf(0.95, df.iloc[0], df.iloc[4])
    max_temps_p75 = norm.ppf(0.75, df.iloc[0], df.iloc[4])
    max_temps_p25 = norm.ppf(0.25, df.iloc[0], df.iloc[4])
    max_temps_p5 = norm.ppf(0.05, df.iloc[0], df.iloc[4])
    # percentiles of monthly mean minimum
    min_temps_p95 = norm.ppf(0.95, df.iloc[2], df.iloc[5])
    min_temps_p75 = norm.ppf(0.75, df.iloc[2], df.iloc[5])
    min_temps_p25 = norm.ppf(0.25, df.iloc[2], df.iloc[5])
    min_temps_p5 = norm.ppf(0.05, df.iloc[2], df.iloc[5])

    # compile into df
    df = pd.DataFrame(data=np.array([max_temps_p95, max_temps_p75, max_temps_p25, max_temps_p5, min_temps_p95, min_temps_p75, min_temps_p25, min_temps_p5]), index=['Monthly Mean Max Temp (F) (95th)', 'Monthly Mean Max Temp (F) (75th)', 'Monthly Mean Max Temp (F) (25th)', 'Monthly Mean Max Temp (F) (5th)', 'Monthly Mean Min Temp (F) (95th)', 'Monthly Mean Min Temp (F) (75th)', 'Monthly Mean Min Temp (F) (25th)', 'Monthly Mean Min Temp (F) (5th)'], columns=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Year'])

    # round temps to 1 decimal place
    df.iloc[0:8] = df.iloc[0:8].round(1)

    return df

def occurrence_probabilities(df):
    # assume all months are 30 days long for now
    days = 30

    # estimating daily max/min stdevs: use central limit theorem but fourth root instead of square root--square root leads to stdevs being WAY too big
    daily_max_std = df.iloc[4]*(days**0.25)
    daily_min_std = df.iloc[5]*(days**0.25)

    # probabilities of occurrences: max greater than or equal to stated temp
    prob_max_geq95 = 1 - (norm.cdf(95, df.iloc[0], daily_max_std) ** 30)
    prob_max_geq86 = 1 - (norm.cdf(86, df.iloc[0], daily_max_std) ** 30)
    prob_max_geq68 = 1 - (norm.cdf(68, df.iloc[0], daily_max_std) ** 30)
    prob_max_geq50 = 1 - (norm.cdf(50, df.iloc[0], daily_max_std) ** 30)
    # probabilities of occurrences: min less than or equal to stated temp
    prob_min_leq50 = 1 - ((1 - norm.cdf(50, df.iloc[2], daily_min_std)) ** 30)
    prob_min_leq32 = 1 - ((1 - norm.cdf(32, df.iloc[2], daily_min_std)) ** 30)
    prob_min_leq14 = 1 - ((1 - norm.cdf(14, df.iloc[2], daily_min_std)) ** 30)
    prob_min_leq5 = 1 - ((1 - norm.cdf(5, df.iloc[2], daily_min_std)) ** 30)

    # compile into df
    df = pd.DataFrame(data=np.array([prob_max_geq95, prob_max_geq86, prob_max_geq68, prob_max_geq50, prob_min_leq50, prob_min_leq32, prob_min_leq14, prob_min_leq5]), index=['P(T >= 95)', 'P(T >= 86)', 'P(T >= 68)', 'P(T >= 50)', 'P(T <= 50)', 'P(T <= 32)', 'P(T <= 14)', 'P(T <= 5)'], columns=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Year'])

    # adjust "Year" column to be the min/max of the months...maybe change this later but this does for now
    df['Year'] = np.array([np.max(df.iloc[0]), np.max(df.iloc[1]), np.max(df.iloc[2]), np.max(df.iloc[3]), np.max(df.iloc[4]), np.max(df.iloc[5]), np.max(df.iloc[6]), np.max(df.iloc[7])])

    # round temps to 1 decimal place
    df.iloc[0:8] = df.iloc[0:8].round(3)

    return df