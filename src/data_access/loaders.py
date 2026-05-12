"""
Data loaders for SB 1087 Capstone Dashboard.
Extracts raw files (VMTIndex, PeMS, EMFAC, CalEnviroScreen) into usable DataFrames.
"""
import pandas as pd
import numpy as np
import os
from pathlib import Path

# Base directory for raw data relative to this file
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"

def load_vmtindex(filepath_or_buffer=None) -> pd.DataFrame:
    """
    Read VMTIndex data and compute trend metrics.
    Calculates change in per-capita VMT since baseline year.
    """
    path = filepath_or_buffer or (DATA_DIR / "vmt_index_cbg.csv")
    df = pd.read_csv(path)
    
    # Ensure ID is zero-padded standard FIPS mapping (12 chars for CBG)
    df['cbg_id'] = df['cbg_id'].astype(str).str.zfill(12)
    
    # Pivot to get vmt_baseline and vmt_current columns
    # We will assume min year is baseline, max year is current for each CBG
    pivot_df = df.groupby('cbg_id').agg(
        vmt_baseline=('vmt_per_capita', 'first'),
        vmt_current=('vmt_per_capita', 'last')
    ).reset_index()
    
    pivot_df['vmt_trend'] = pivot_df['vmt_current'] - pivot_df['vmt_baseline']
    return pivot_df

def load_calenviro(filepath_or_buffer=None) -> pd.DataFrame:
    """
    Read CalEnviroScreen 4.0 data.
    Extract traffic-related burden indicators and overall score.
    """
    path = filepath_or_buffer or (DATA_DIR / "calenviroscreen40.csv")
    df = pd.read_csv(path)
    df['cbg_id'] = df['cbg_id'].astype(str).str.zfill(12)
    return df

def load_pems(segment_id: str = None, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Pull/clean archived PeMS data from local exports or API.
    """
    path = DATA_DIR / "pems_segment_timeseries.csv"
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    
    if segment_id:
        df = df[df['segment_id'] == segment_id]
    if start_date:
        df = df[df['date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['date'] <= pd.to_datetime(end_date)]
        
    return df.sort_values('date').reset_index(drop=True)

def load_emfac_results(scenario_name: str) -> pd.DataFrame:
    """
    Read EMFAC2021 outputs. Accepts 'scenario_a' or 'scenario_b'.
    """
    filename = f"emfac_{scenario_name.lower()}.csv"
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing EMFAC scenario file: {path}")
    return pd.read_csv(path)

def load_tdm_scenario(scenario_name: str) -> pd.DataFrame:
    """
    Wrapper mapping to EMFAC results for simplistic architecture.
    """
    return load_emfac_results(scenario_name)


