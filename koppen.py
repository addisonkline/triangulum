import numpy as np
import pandas as pd

# Return the Koppen classification of a given climate normal df
def koppen(df):
    classification = ""

    if (df.iloc[1][0:12].max() <= 50): # polar climates
        classification += "E"

        if (df.iloc[1][0:12].max() > 32):
            classification += "T"
        else:
            classification += "F"
        
    else:
        precip_threshold = 20*(5/9)*(df.loc["Daily Mean Temp (F)", "Year"] - 32)
        if (df.iloc[3][3:8].sum()/df.iloc[3][0:12].sum() >= 0.7):
            precip_threshold += 280
        elif (df.iloc[3][3:8].sum()/df.iloc[3][0:12].sum() >= 0.3):
            precip_threshold += 140
        
        if ((25.4 * df.loc["Precip (in)", "Year"])/precip_threshold < 0.5): # arid climates
            classification += "BW"

            if(df.loc["Daily Mean Temp (F)", "Year"] > 64.4):
                classification += "h"
            else:
                classification += "k"

        elif ((25.4 * df.loc["Precip (in)", "Year"])/precip_threshold < 1): # semiarid climates
            classification += "BS"
            
            if(df.loc["Daily Mean Temp (F)", "Year"] >= 64.4):
                classification += "h"
            else:
                classification += "k"

        else:
            if (df.iloc[1][0:12].min() >= 64.4): # non-arid tropical climates
                classification += "A"

                if (df.iloc[3][0:12].min() >= 2.4):
                    classification += "f"
                elif (df.iloc[3][0:12].min() >= 100 - ((25.4 * df.loc["Precip (in)", "Year"])/25)):
                    classification += "m"
                else:
                    classification += "w"

            elif (df.iloc[1][0:12].min() > 26.6): # temperate climates
                classification += "C"

                if (df.iloc[3][0:12].max()/df.iloc[3][0:12].min() >= 10 and df.iloc[3][0:12].idxmax() > 3 and df.iloc[3][0:12].idxmac() < 10):
                    classification += "w"
                elif (df.iloc[3][0:12].max()/df.iloc[3][0:12].min() >= 3 and (df.iloc[3][0:12].idxmax() <= 3 or df.iloc[3][0:12].idxmac() >= 10) and df.iloc[3][0:12].min() < 1.6):
                    classification += "s"
                else:
                    classification += "f"

                if ((df.iloc[1][0:12] >= 50).sum() >= 4 and df.iloc[1][0:12].max() >= 71.6):
                    classification += "a"
                elif (df[df.iloc[1][0:12] >= 50].shape[1] >= 4):
                    classification += "b"
                else:
                    classification += "c"
            
            else: # continental climates
                classification += "D"

                if (df.iloc[3][0:12].max()/df.iloc[3][0:12].min() >= 10 and df.iloc[3][0:12].idxmax() > 3 and df.iloc[3][0:12].idxmac() < 10):
                    classification += "w"
                elif (df.iloc[3][0:12].max()/df.iloc[3][0:12].min() >= 3 and (df.iloc[3][0:12].idxmax() <= 3 or df.iloc[3][0:12].idxmac() >= 10) and df.iloc[3][0:12].max() < 1.6):
                    classification += "s"
                else:
                    classification += "f"

                if ((df.iloc[1][0:12] >= 50).sum() >= 4 and df.iloc[1][0:12].max() >= 71.6):
                    classification += "a"
                elif (df[df.iloc[1][0:12] >= 50].shape[1] >= 4):
                    classification += "b"
                elif (df.iloc[1][0:12].min() > -36.4):
                    classification += "c"
                else:
                    classification += "d"

    return classification