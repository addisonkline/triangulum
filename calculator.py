import pandas as pd
import numpy as np

def calculate(d1, d2, d3, dfs, elev, lapse): # d1, d2, d3 distances, dfs a list of the corresponding dataframes
    # gets weighted average of the three stations
    max_temps = ((1 - (d1/(d1 + d2 + d3)))/2)*dfs[0].iloc[0].to_numpy() + ((1 - (d2/(d1 + d2 + d3)))/2)*dfs[1].iloc[0].to_numpy() + ((1 - (d3/(d1 + d2 + d3)))/2)*dfs[2].iloc[0].to_numpy()
    min_temps = ((1 - (d1/(d1 + d2 + d3)))/2)*dfs[0].iloc[1].to_numpy() + ((1 - (d2/(d1 + d2 + d3)))/2)*dfs[1].iloc[1].to_numpy() + ((1 - (d3/(d1 + d2 + d3)))/2)*dfs[2].iloc[1].to_numpy()
    precip = ((1 - (d1/(d1 + d2 + d3)))/2)*dfs[0].iloc[2].to_numpy() + ((1 - (d2/(d1 + d2 + d3)))/2)*dfs[1].iloc[2].to_numpy() + ((1 - (d3/(d1 + d2 + d3)))/2)*dfs[2].iloc[2].to_numpy()
    
    # calculates daily mean from max and min
    mean_temps = (max_temps + min_temps) / 2

    # calculates adjusts for elevation
    max_temps = max_temps - ((elev/1000)*lapse)
    min_temps = min_temps - ((elev/1000)*lapse)

    # create df from above information
    df = pd.DataFrame(data=np.array([max_temps, mean_temps, min_temps, precip]), index=['Max Temp (F)', 'Mean Temp (F)', 'Min Temp (F)', 'Precip (in)'], columns=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])

    # add col of annual values (means for temp, total for precip)
    df['Year'] = np.array([np.mean(df.iloc[0]), np.mean(df.iloc[1]), np.mean(df.iloc[2]), np.sum(df.iloc[3])])

    # round final df accordingly: 1 decimal place for temperature, 2 for precip
    df.iloc[0:3] = df.iloc[0:3].round(1)
    df.iloc[3] = df.iloc[3].round(2)

    return df