import numpy as np
import pandas as pd

# Return the Koppen classification of a given climate normal df
def trewartha(df):
    classification = ""

    if (df.iloc[1][0:12].max() <= 50): # polar climates
        classification += "F"

        if (df.iloc[1][0:12].max() > 32):
            classification += "t"
        else:
            classification += "i"
        
    else:
        precip_threshold = 10*((5/9)*(df.loc["Mean Temp (F)", "Year"] - 32) - 10) + 3*(df.iloc[3][3:8].sum()/df.iloc[3][0:12].sum())
        if ((25.4 * df.loc["Precip (in)", "Year"])/precip_threshold < 1): # arid climates
            classification += "BW"
        elif ((25.4 * df.loc["Precip (in)", "Year"])/precip_threshold < 2): # semi arid climates
            classification += "BS"

        else:
            if (df.iloc[1][0:12].min() >= 64.4): # non-arid tropical climates
                classification += "A"

                if ((df.iloc[3][0:12] < 2.4).sum() <= 2):
                    classification += "r"
                else:
                    if (df.iloc[3][0:12].idxmax() > 3 and df.iloc[3][0:12].idxmax() < 10):
                        classification += "w"
                    else:
                        classification += "s"

            elif ((df.iloc[1][0:12] > 50).sum() >= 8): # temperate climates
                classification += "C"

                if (df.iloc[3][0:12].max()/df.iloc[3][0:12].min() >= 3 and (df.iloc[3][0:12].idxmax() <= 3 or df.iloc[3][0:12].idxmac() >= 10) and df.iloc[3][0:12].min() < 1.6):
                    classification += "s"
                else:
                    classification += "f"
            
            elif ((df.iloc[1][0:12] > 50).sum() >= 4): # continental climates
                classification += "D"

                if (df.iloc[1][0:12].min() <= 32):
                    classification += "c"
                else:
                    classification += "o"
            
            else: # boreal climates
                classification += "E"

                if (df.iloc[1][0:12].min() <= 14):
                    classification += "c"
                else:
                    classification += "o"

    return classification