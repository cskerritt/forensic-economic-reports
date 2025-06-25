import os
import pandas as pd
from typing import Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the absolute path to the CSV files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
YFS_TABLE_PATH = os.path.join(BASE_DIR, 'YFS Table.csv')
WLE_TABLE_PATH = os.path.join(BASE_DIR, 'WLE Table.csv')

# Log the file paths
logger.info(f"YFS Table path: {YFS_TABLE_PATH}")
logger.info(f"WLE Table path: {WLE_TABLE_PATH}")
logger.info(f"Files exist: YFS={os.path.exists(YFS_TABLE_PATH)}, WLE={os.path.exists(WLE_TABLE_PATH)}")

# Load the CSV files
try:
    yfs_df = pd.read_csv(YFS_TABLE_PATH)
    wle_df = pd.read_csv(WLE_TABLE_PATH)
    logger.info(f"Successfully loaded YFS and WLE tables from {BASE_DIR}")
    logger.info(f"YFS table shape: {yfs_df.shape}, columns: {list(yfs_df.columns)}")
    logger.info(f"WLE table shape: {wle_df.shape}, columns: {list(wle_df.columns)}")
except Exception as e:
    logger.error(f"Error loading CSV files: {e}")
    yfs_df = None
    wle_df = None

def get_closest_row(df, gender, education_level, age, active=True):
    """
    Find the closest matching row in the dataframe based on the given parameters.
    
    Args:
        df: The dataframe to search in
        gender: The gender to match ('Men' or 'Women')
        education_level: The education level to match
        age: The age to match
        active: Whether to look for initially active individuals (default: True)
    
    Returns:
        The closest matching row or None if no match found
    """
    if df is None:
        logger.error("DataFrame is None, cannot perform lookup")
        return None
    
    # Determine the active column name based on the dataframe columns
    active_col = None
    if 'Active?' in df.columns:
        active_col = 'Active?'
    elif 'Active ?' in df.columns:
        active_col = 'Active ?'
    
    if active_col is None:
        logger.error(f"Active column not found in dataframe columns: {list(df.columns)}")
        return None
    
    # Filter by gender and active status
    filtered_df = df[
        (df['Gender'] == gender) & 
        (df[active_col] == 'Initially Active' if active else 'Not Active')
    ]
    
    # Try to find exact education level match
    education_matches = filtered_df[filtered_df['Education Level'] == education_level]
    
    # If no exact match, fall back to 'All Education Levels'
    if education_matches.empty:
        education_matches = filtered_df[filtered_df['Education Level'] == 'All Education Levels']
    
    # If still no match, return None
    if education_matches.empty:
        logger.warning(f"No education level match found for {gender}, {education_level}, active={active}")
        return None
    
    # Find the closest age
    age_float = float(age)
    education_matches = education_matches.copy()  # Create a copy to avoid SettingWithCopyWarning
    education_matches['Age'] = education_matches['Age'].astype(float)
    closest_row = education_matches.iloc[(education_matches['Age'] - age_float).abs().argsort()[:1]]
    
    if closest_row.empty:
        logger.warning(f"No age match found for {gender}, {education_level}, age={age}, active={active}")
        return None
    
    return closest_row.iloc[0]

def lookup_yfs_median(gender, education_level, age, active=True) -> Optional[float]:
    """
    Look up the YFS median value from the YFS table.
    
    Args:
        gender: 'Men' or 'Women'
        education_level: Education level string
        age: Age as a float or int
        active: Whether to look for initially active individuals (default: True)
    
    Returns:
        The YFS median value or None if not found
    """
    logger.info(f"Looking up YFS median for gender={gender}, education_level={education_level}, age={age}, active={active}")
    row = get_closest_row(yfs_df, gender, education_level, age, active)
    if row is not None and 'YFS median' in row:
        result = float(row['YFS median'])
        logger.info(f"Found YFS median: {result}")
        return result
    logger.warning(f"YFS median not found for gender={gender}, education_level={education_level}, age={age}")
    return None

def lookup_wle_median(gender, education_level, age, active=True) -> Optional[float]:
    """
    Look up the WLE median value from the WLE table.
    
    Args:
        gender: 'Men' or 'Women'
        education_level: Education level string
        age: Age as a float or int
        active: Whether to look for initially active individuals (default: True)
    
    Returns:
        The WLE median value or None if not found
    """
    logger.info(f"Looking up WLE median for gender={gender}, education_level={education_level}, age={age}, active={active}")
    row = get_closest_row(wle_df, gender, education_level, age, active)
    if row is not None and 'Median' in row:
        result = float(row['Median'])
        logger.info(f"Found WLE median: {result}")
        return result
    logger.warning(f"WLE median not found for gender={gender}, education_level={education_level}, age={age}")
    return None

def lookup_worklife_values(gender, education_level, age, active=True) -> Tuple[Optional[float], Optional[float]]:
    """
    Look up both WLE and YFS median values.
    
    Args:
        gender: 'Men' or 'Women'
        education_level: Education level string
        age: Age as a float or int
        active: Whether to look for initially active individuals (default: True)
    
    Returns:
        Tuple of (wle_median, yfs_median) or (None, None) if not found
    """
    logger.info(f"Looking up worklife values for gender={gender}, education_level={education_level}, age={age}, active={active}")
    wle_value = lookup_wle_median(gender, education_level, age, active)
    yfs_value = lookup_yfs_median(gender, education_level, age, active)
    logger.info(f"Worklife values: WLE={wle_value}, YFS={yfs_value}")
    return wle_value, yfs_value 