"""
Core business logic and metric calculation for the three Policy Pillars.
"""
import pandas as pd
import numpy as np

def join_vmt_env(df_vmt: pd.DataFrame, df_env: pd.DataFrame, corridor_def: str = None) -> pd.DataFrame:
    """
    Spatially or nominally join VMT trends and pollution burden using the `cbg_id`.
    Returns a dataframe merged on CBG holding diagnostic metrics for Pillar 1.
    """
    merged = pd.merge(df_vmt, df_env, on='cbg_id', how='inner')
    
    # Filter by corridor if specified (placeholder simple string match string logic)
    if corridor_def:
        # Assuming we might add a region flag later, default passthrough for now
        pass
        
    return merged

def compute_congestion_metrics(df_pems: pd.DataFrame) -> dict:
    """
    Compare average speeds, travel time index, and reliability pre/post expansion.
    """
    if df_pems.empty: return {}
    
    # Grouping by explicit phase
    phase_speeds = df_pems.groupby('phase')['avg_speed_mph'].mean().to_dict()
    
    pre_speed = phase_speeds.get('pre', 0)
    post_speed = phase_speeds.get('post', 0)
    year3_speed = phase_speeds.get('year_3', 0)
    
    speed_return_pct = 0.0
    if (post_speed - pre_speed) > 0:
        speed_return_pct = (post_speed - year3_speed) / (post_speed - pre_speed)

    speed_erosion_pct = min(100.0, max(0.0, speed_return_pct * 100.0))

    return {
        "pre_expansion_mph": pre_speed,
        "initial_relief_mph": post_speed,
        "stabilized_3yr_mph": year3_speed,
        "speed_erosion_pct": speed_erosion_pct,
        "initial_relief_gain_mph": post_speed - pre_speed,
        "remaining_relief_mph": year3_speed - pre_speed,
    }

def estimate_induced_vmt_from_ncst(lane_miles_added: float, base_year: int) -> dict:
    """
    Read NCST outputs computationally or use a heuristic calculation 
    to output annual and 20-year CO2 equivalent penalties.
    """
    # NCST standard elasticity rule of thumb for Class 1 facilities is ~1.0
    # Assuming standard capacity generation arithmetic per lane mile:
    annual_vmt_penalty_millions = lane_miles_added * 2.1
    twenty_yr_vmt_millions = annual_vmt_penalty_millions * 20
    
    # Approx 400 grams CO2e per passenger mile
    co2_tons_annual = (annual_vmt_penalty_millions * 1e6 * 400) / 1e6
    co2_tons_20yr = co2_tons_annual * 20
    
    return {
        "annual_vmt_added_m": annual_vmt_penalty_millions,
        "20_yr_vmt_added_m": twenty_yr_vmt_millions,
        "annual_co2_penalty": co2_tons_annual,
        "20_yr_co2_penalty": co2_tons_20yr,
        "implied_mitigation_cost": twenty_yr_vmt_millions * 0.05 # Hypothetical $0.05 per VMT mile cost
    }

def compute_climate_floor_score(project_stats: dict) -> float:
    """
    Combine VMT reduction, safety, and air quality into a Statewide Project
    Prioritization Score (Virginia SMART SCALE style).
    Negative VMT or net-emissions actively hurts the project standing.
    """
    # Weighting: 40% VMT, 30% Safety, 30% Air Quality
    vmt_delta = project_stats.get('forecasted_vmt_delta_m', 0)
    safety_incidents = project_stats.get('safety_incidents', 0)
    pm25_delta = project_stats.get('pm25_delta_tons', 0)
    
    # Calculate inverted VMT impact (negative VMT is bad here, meaning added VMT is heavily penalized)
    # A negative vmt_delta (less cars) yields positive points
    vmt_score = (vmt_delta * -2.0)
    
    # Safety score base 50, minus incidents
    safety_score = max(0, 50 - (safety_incidents * 3))
    
    # Air quality PM25 penalty
    aq_score = min(50, max(-50, (pm25_delta * -10)))
    
    total_score = float(vmt_score + safety_score + aq_score)
    return {
        "vmt_delta": vmt_delta,
        "pm25_delta_tons": pm25_delta,
        "safety_incidents": safety_incidents,
        "vmt_score": vmt_score,
        "safety_score": safety_score,
        "aq_score": aq_score,
        "total_score": total_score
    }

