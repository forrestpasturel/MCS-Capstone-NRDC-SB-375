import sys, os
sys.path.append(os.path.abspath('.'))
from src.data_access.loaders import load_vmtindex, load_calenviro, load_pems, load_emfac_results
from src.analysis.metrics import join_vmt_env, compute_congestion_metrics, compute_climate_floor_score

print("Testing VMT...")
try:
    df_vmt = load_vmtindex()
    print("VMT loaded:", len(df_vmt))
except Exception as e:
    print("VMT Error:", e)

print("Testing CalEnviro...")
try:
    df_env = load_calenviro()
    print("CalEnviro loaded:", len(df_env))
except Exception as e:
    print("CalEnviro Error:", e)

print("Testing PeMS...")
try:
    df_pems = load_pems()
    print("PeMS loaded:", len(df_pems))
except Exception as e:
    print("PeMS Error:", e)

print("Testing EMFAC...")
try:
    df_emfac = load_emfac_results("some_scenario")
    print("EMFAC loaded:", len(df_emfac))
except Exception as e:
    print("EMFAC Error:", e)
