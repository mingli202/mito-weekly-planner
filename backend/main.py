import pandas as pd
import numpy as np

data = pd.read_csv("./stores_location.csv")
addresses = data["Adresse Mag."]

addresses[0:10]
