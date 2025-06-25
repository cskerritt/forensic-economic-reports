#!/usr/bin/env python3
"""
Life Expectancy Lookup Tool - Integrated for Economic Analysis Application

This tool looks up:
1. Life Expectancy (LE) - based on gender, race, and age
2. Work Life Expectancy (WLE) - based on gender, education, age, and activity status
3. Years to Final Separation (YFS) - based on gender, education, age, and activity status

Integrated from: https://github.com/cskerritt/ExpectancyLookUp
"""

import pandas as pd
import os
from datetime import datetime, date
from typing import Tuple, Optional, Dict, Any
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class ExpectancyLookup:
    def __init__(self):
        """Initialize the lookup tool with CSV data files."""
        # Define paths to CSV files in the application data directory
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'expectancy')
        self.le_path = os.path.join(data_dir, "le_data.csv")
        self.wle_path = os.path.join(data_dir, "wle_data.csv")
        self.yfs_path = os.path.join(data_dir, "yfs_data.csv")
        
        # Load data
        self.le_data = None
        self.wle_data = None
        self.yfs_data = None
        
        self._load_data()
    
    def _load_data(self):
        """Load all CSV data files."""
        try:
            logger.info("Loading expectancy data files...")
            
            # Check if data files exist
            if not all(os.path.exists(path) for path in [self.le_path, self.wle_path, self.yfs_path]):
                logger.warning("Expectancy data files not found. Using sample data structure.")
                self._create_sample_data()
                return
            
            # Load Life Expectancy data
            self.le_data = pd.read_csv(self.le_path, encoding='utf-8-sig')
            # Clean column names by stripping whitespace
            self.le_data.columns = self.le_data.columns.str.strip()
            logger.info(f"✓ Loaded Life Expectancy data: {len(self.le_data)} rows")
            
            # Load Work Life Expectancy data
            self.wle_data = pd.read_csv(self.wle_path, encoding='utf-8-sig')
            self.wle_data.columns = self.wle_data.columns.str.strip()
            logger.info(f"✓ Loaded Work Life Expectancy data: {len(self.wle_data)} rows")
            
            # Load Years to Final Separation data
            self.yfs_data = pd.read_csv(self.yfs_path, encoding='utf-8-sig')
            self.yfs_data.columns = self.yfs_data.columns.str.strip()
            logger.info(f"✓ Loaded Years to Final Separation data: {len(self.yfs_data)} rows")
            
            logger.info("Expectancy data loading complete!")
            
        except Exception as e:
            logger.error(f"Error loading expectancy data: {str(e)}")
            self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data structures for testing."""
        logger.info("Creating sample expectancy data structures...")
        
        # Sample Life Expectancy data
        self.le_data = pd.DataFrame({
            'Gender': ['Males', 'Females', 'Males', 'Females'] * 20,
            'Race': [None, None, 'White', 'White'] * 20,
            'Age Low': list(range(20, 100, 1)),
            'Age High': list(range(21, 101, 1)),
            'Expectation of Life': [75.5, 80.2, 76.1, 81.0] * 20
        })
        
        # Sample Work Life Expectancy data
        ages = list(range(20, 65))
        self.wle_data = pd.DataFrame({
            'Gender': (['Men'] * len(ages) + ['Women'] * len(ages)) * 3,
            'Education Level': (['High School'] * len(ages) * 2 + 
                              ['Bachelor\'s Degree'] * len(ages) * 2 +
                              ['Advanced Degree'] * len(ages) * 2),
            'Age': ages * 6,
            'Active?': ['Initially Active'] * len(ages) * 6,
            'Median': [max(0, 65 - age + (2 if 'Bachelor' in ed else 3 if 'Advanced' in ed else 0)) 
                      for ed in ['High School'] * len(ages) * 2 + 
                                ['Bachelor\'s Degree'] * len(ages) * 2 +
                                ['Advanced Degree'] * len(ages) * 2
                      for age in ages]
        })
        
        # Sample Years to Final Separation data
        self.yfs_data = pd.DataFrame({
            'Gender': (['Men'] * len(ages) + ['Women'] * len(ages)) * 3,
            'Education Level': (['High School'] * len(ages) * 2 + 
                              ['Bachelor\'s Degree'] * len(ages) * 2 +
                              ['Advanced Degree'] * len(ages) * 2),
            'Age': ages * 6,
            'Active ?': ['Initially Active'] * len(ages) * 6,
            'YFS median': [max(0, 67 - age + (1 if 'Bachelor' in ed else 2 if 'Advanced' in ed else 0)) 
                          for ed in ['High School'] * len(ages) * 2 + 
                                    ['Bachelor\'s Degree'] * len(ages) * 2 +
                                    ['Advanced Degree'] * len(ages) * 2
                          for age in ages]
        })
        
        logger.info("Sample expectancy data created successfully")
    
    def calculate_age(self, birth_date: date, reference_date: date) -> int:
        """Calculate age at reference date."""
        return reference_date.year - birth_date.year - ((reference_date.month, reference_date.day) < (birth_date.month, birth_date.day))
    
    def lookup_life_expectancy(self, gender: str, race: str, age: int) -> Optional[float]:
        """
        Look up life expectancy based on gender, race, and age.
        
        Args:
            gender: 'Males' or 'Females' or 'Men' or 'Women'
            race: Race category or 'N/A' for general population
            age: Age in years
            
        Returns:
            Life expectancy in years or None if not found
        """
        try:
            # Normalize gender input
            if gender in ['Men', 'Male']:
                gender = 'Males'
            elif gender in ['Women', 'Female']:
                gender = 'Females'
            
            # Handle race filtering - 'N/A' or 'General' should match NaN values
            if race in ['N/A', 'General', 'General Population', '', None]:
                race_filter = pd.isna(self.le_data['Race'])
            else:
                race_filter = (self.le_data['Race'] == race)
            
            # Filter data
            filtered = self.le_data[
                (self.le_data['Gender'] == gender) & 
                race_filter &
                (self.le_data['Age Low'] <= age) & 
                (self.le_data['Age High'] >= age)
            ]
            
            if not filtered.empty:
                return float(filtered.iloc[0]['Expectation of Life'])
            else:
                # Fallback: use closest age match
                age_diff = abs(self.le_data['Age Low'] - age)
                closest_idx = age_diff.idxmin()
                
                gender_race_match = self.le_data[
                    (self.le_data['Gender'] == gender) & race_filter
                ]
                
                if not gender_race_match.empty:
                    return float(gender_race_match.iloc[0]['Expectation of Life'])
                
                return None
                
        except Exception as e:
            logger.error(f"Error looking up life expectancy: {str(e)}")
            return None
    
    def lookup_work_life_expectancy(self, gender: str, education: str, age: int, active_status: str = "Initially Active") -> Optional[float]:
        """
        Look up work life expectancy (median value).
        
        Args:
            gender: 'Men' or 'Women' or 'Males' or 'Females'
            education: Education level
            age: Age in years
            active_status: 'Initially Active' or other status
            
        Returns:
            Work life expectancy median in years or None if not found
        """
        try:
            # Normalize gender input
            if gender in ['Males', 'Male']:
                gender = 'Men'
            elif gender in ['Females', 'Female']:
                gender = 'Women'
            
            # Filter data
            filtered = self.wle_data[
                (self.wle_data['Gender'] == gender) & 
                (self.wle_data['Education Level'] == education) &
                (self.wle_data['Age'] == age) &
                (self.wle_data['Active?'] == active_status)
            ]
            
            if not filtered.empty:
                return float(filtered.iloc[0]['Median'])
            else:
                # Fallback: find closest age match for same gender/education
                gender_ed_match = self.wle_data[
                    (self.wle_data['Gender'] == gender) & 
                    (self.wle_data['Education Level'] == education) &
                    (self.wle_data['Active?'] == active_status)
                ]
                
                if not gender_ed_match.empty:
                    age_diff = abs(gender_ed_match['Age'] - age)
                    closest_idx = age_diff.idxmin()
                    return float(gender_ed_match.loc[closest_idx, 'Median'])
                
                return None
                
        except Exception as e:
            logger.error(f"Error looking up work life expectancy: {str(e)}")
            return None
    
    def lookup_years_to_final_separation(self, gender: str, education: str, age: int, active_status: str = "Initially Active") -> Optional[float]:
        """
        Look up years to final separation (median value).
        
        Args:
            gender: 'Men' or 'Women' or 'Males' or 'Females'
            education: Education level
            age: Age in years
            active_status: 'Initially Active' or other status
            
        Returns:
            Years to final separation median or None if not found
        """
        try:
            # Normalize gender input
            if gender in ['Males', 'Male']:
                gender = 'Men'
            elif gender in ['Females', 'Female']:
                gender = 'Women'
            
            # Filter data
            filtered = self.yfs_data[
                (self.yfs_data['Gender'] == gender) & 
                (self.yfs_data['Education Level'] == education) &
                (self.yfs_data['Age'] == age) &
                (self.yfs_data['Active ?'] == active_status)
            ]
            
            if not filtered.empty:
                return float(filtered.iloc[0]['YFS median'])
            else:
                # Fallback: find closest age match for same gender/education
                gender_ed_match = self.yfs_data[
                    (self.yfs_data['Gender'] == gender) & 
                    (self.yfs_data['Education Level'] == education) &
                    (self.yfs_data['Active ?'] == active_status)
                ]
                
                if not gender_ed_match.empty:
                    age_diff = abs(gender_ed_match['Age'] - age)
                    closest_idx = age_diff.idxmin()
                    return float(gender_ed_match.loc[closest_idx, 'YFS median'])
                
                return None
                
        except Exception as e:
            logger.error(f"Error looking up years to final separation: {str(e)}")
            return None
    
    def get_available_options(self) -> Dict[str, list]:
        """Get available options for each parameter."""
        try:
            # Helper function to safely sort mixed types
            def safe_sort(items):
                # Convert to strings, remove NaN values, then sort
                clean_items = [str(item) for item in items if pd.notna(item)]
                return sorted(list(set(clean_items)))
            
            # Special handling for race - add 'General Population' for NaN values
            race_options = safe_sort(self.le_data['Race'].unique())
            if any(pd.isna(self.le_data['Race'])):
                race_options = ['General Population'] + race_options
            
            options = {
                'genders_le': safe_sort(self.le_data['Gender'].unique()),
                'races': race_options,
                'genders_wle': safe_sort(self.wle_data['Gender'].unique()),
                'education_levels': safe_sort(self.wle_data['Education Level'].unique()),
                'active_statuses_wle': safe_sort(self.wle_data['Active?'].unique()),
                'active_statuses_yfs': safe_sort(self.yfs_data['Active ?'].unique())
            }
            return options
        except Exception as e:
            logger.error(f"Error getting available options: {str(e)}")
            return {}
    
    def comprehensive_lookup(self, birth_date: date, injury_date: date, 
                           gender: str, race: str = "General Population", 
                           education: str = "High School", active_status: str = "Initially Active") -> Dict[str, Any]:
        """
        Perform comprehensive lookup with single data entry.
        
        Args:
            birth_date: Date of birth
            injury_date: Date of injury
            gender: Gender ('Men'/'Women' or 'Males'/'Females')
            race: Race for LE lookup
            education: Education level
            active_status: Work activity status
            
        Returns:
            Dictionary with all results
        """
        # Calculate age at injury
        age_at_injury = self.calculate_age(birth_date, injury_date)
        
        # Perform all lookups
        le = self.lookup_life_expectancy(gender, race, age_at_injury)
        wle = self.lookup_work_life_expectancy(gender, education, age_at_injury, active_status)
        yfs = self.lookup_years_to_final_separation(gender, education, age_at_injury, active_status)
        
        return {
            'input_data': {
                'birth_date': birth_date,
                'injury_date': injury_date,
                'age_at_injury': age_at_injury,
                'gender': gender,
                'race': race,
                'education': education,
                'active_status': active_status
            },
            'results': {
                'life_expectancy': le,
                'work_life_expectancy': wle,
                'years_to_final_separation': yfs
            }
        }

# Global instance for use throughout the application
_expectancy_lookup = None

def get_expectancy_lookup():
    """Get the global expectancy lookup instance."""
    global _expectancy_lookup
    if _expectancy_lookup is None:
        _expectancy_lookup = ExpectancyLookup()
    return _expectancy_lookup

def calculate_expectancies(birth_date, injury_date, gender, education_level, race="General Population"):
    """
    Calculate all expectancy values for an evaluee.
    
    Args:
        birth_date: Date of birth
        injury_date: Date of injury  
        gender: Gender
        education_level: Education level
        race: Race (optional, defaults to General Population)
        
    Returns:
        Dictionary with life_expectancy, work_life_expectancy, years_to_final_separation
    """
    try:
        lookup = get_expectancy_lookup()
        results = lookup.comprehensive_lookup(
            birth_date, injury_date, gender, race, education_level
        )
        return results['results']
    except Exception as e:
        logger.error(f"Error calculating expectancies: {str(e)}")
        return {
            'life_expectancy': None,
            'work_life_expectancy': None,
            'years_to_final_separation': None
        }