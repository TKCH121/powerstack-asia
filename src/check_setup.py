import sys
import pandas as pd
import geopandas as gpd
import duckdb
import sklearn
import streamlit

print("Python:", sys.version)
print("pandas:", pd.__version__)
print("geopandas:", gpd.__version__)
print("duckdb:", duckdb.__version__)
print("scikit-learn:", sklearn.__version__)
print("streamlit:", streamlit.__version__)
print("Setup looks OK.")
