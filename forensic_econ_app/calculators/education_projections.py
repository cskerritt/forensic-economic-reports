"""
Educational attainment income and employment projections for pediatric cases.

This module contains functions for projecting future income based on educational attainment.
Data is sourced from US Bureau of Labor Statistics and US Census Bureau.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, date, timedelta


# National average earnings by education level (2023 data, median weekly earnings)
# Source: Bureau of Labor Statistics, Current Population Survey
WEEKLY_EARNINGS_BY_EDUCATION = {
    "Less than High School": 708,
    "High School Diploma": 899,
    "Some College": 992,
    "Associate's Degree": 1058,
    "Bachelor's Degree": 1493,
    "Master's Degree": 1737,
    "Professional Degree": 2206,
    "Doctoral Degree": 2109
}

# Annual earnings (52 weeks)
ANNUAL_EARNINGS_BY_EDUCATION = {
    level: weekly * 52 for level, weekly in WEEKLY_EARNINGS_BY_EDUCATION.items()
}

# Unemployment rates by education level (2023 data, percent)
# Source: Bureau of Labor Statistics, Current Population Survey
UNEMPLOYMENT_RATES_BY_EDUCATION = {
    "Less than High School": 5.6,
    "High School Diploma": 3.9,
    "Some College": 3.3,
    "Associate's Degree": 2.7,
    "Bachelor's Degree": 2.2,
    "Master's Degree": 2.0,
    "Professional Degree": 1.2,
    "Doctoral Degree": 1.6
}

# Labor force participation rates by education level (2021 data, percent)
# Source: Bureau of Labor Statistics - keep these values as they weren't updated
PARTICIPATION_RATES_BY_EDUCATION = {
    "Less than High School": 45.2,
    "High School Diploma": 57.8,
    "Some College": 63.4,
    "Associate's Degree": 66.2,
    "Bachelor's Degree": 74.3,
    "Master's Degree": 76.2,
    "Professional Degree": 76.8,
    "Doctoral Degree": 77.9
}

# Typical workforce entry ages by education level
WORKFORCE_ENTRY_AGE = {
    "High School Diploma": 18,
    "Some College": 19,
    "Associate's Degree": 20,
    "Bachelor's Degree": 22,
    "Master's Degree": 24,
    "Professional Degree": 26,
    "Doctoral Degree": 27
}

# Statistical retirement data by education level
# Source: Gary R. Skoog, James E. Ciecka, and Kurt V. Krueger (2019)
# "The Markov Model of Labor Force Activity 2012-17: Extended Tables of Central Tendency,
# Shape, Percentile Points, and Bootstrap Standard Errors"
STATISTICAL_RETIREMENT_DATA = {
    "High School Diploma": {
        "entry_age": 18.00,
        "wle": 37.87,
        "retirement_age": 55.87,
        "yfs": 47.50,  # Years to Final Separation
        "age_final_separation": 65.50,
        "worklife_ratio": 79.73  # Percentage
    },
    "Some College": {
        "entry_age": 19.00,
        "wle": 38.54,
        "retirement_age": 57.54,
        "yfs": 46.50,
        "age_final_separation": 65.50,
        "worklife_ratio": 82.88  # Percentage
    },
    "Associate's Degree": {
        "entry_age": 20.00,
        "wle": 39.85,
        "retirement_age": 59.85,
        "yfs": 45.50,
        "age_final_separation": 65.50,
        "worklife_ratio": 87.58  # Percentage
    },
    "Bachelor's Degree": {
        "entry_age": 22.00,
        "wle": 40.68,
        "retirement_age": 62.68,
        "yfs": 45.50,
        "age_final_separation": 67.50,
        "worklife_ratio": 89.41  # Percentage
    }
}

# Probability of attaining education level based on parental education
# Source: US Census Bureau, Educational Attainment in the United States
# These are simplified probabilities for reference
EDUCATION_PROBABILITY_BY_PARENT = {
    # Indexed by [parent_education][child_education]
    "Less than High School": {
        "Less than High School": 0.35,
        "High School Diploma": 0.35,
        "Some College": 0.15,
        "Associate's Degree": 0.08,
        "Bachelor's Degree": 0.05,
        "Master's Degree": 0.01,
        "Professional Degree": 0.005,
        "Doctoral Degree": 0.005
    },
    "High School Diploma": {
        "Less than High School": 0.15,
        "High School Diploma": 0.40,
        "Some College": 0.20,
        "Associate's Degree": 0.10,
        "Bachelor's Degree": 0.10,
        "Master's Degree": 0.03,
        "Professional Degree": 0.01,
        "Doctoral Degree": 0.01
    },
    "Some College": {
        "Less than High School": 0.10,
        "High School Diploma": 0.25,
        "Some College": 0.30,
        "Associate's Degree": 0.15,
        "Bachelor's Degree": 0.15,
        "Master's Degree": 0.03,
        "Professional Degree": 0.01,
        "Doctoral Degree": 0.01
    },
    "Associate's Degree": {
        "Less than High School": 0.05,
        "High School Diploma": 0.20,
        "Some College": 0.25,
        "Associate's Degree": 0.25,
        "Bachelor's Degree": 0.18,
        "Master's Degree": 0.05,
        "Professional Degree": 0.01,
        "Doctoral Degree": 0.01
    },
    "Bachelor's Degree": {
        "Less than High School": 0.03,
        "High School Diploma": 0.12,
        "Some College": 0.18,
        "Associate's Degree": 0.15,
        "Bachelor's Degree": 0.38,
        "Master's Degree": 0.10,
        "Professional Degree": 0.02,
        "Doctoral Degree": 0.02
    },
    "Master's Degree": {
        "Less than High School": 0.02,
        "High School Diploma": 0.08,
        "Some College": 0.13,
        "Associate's Degree": 0.12,
        "Bachelor's Degree": 0.35,
        "Master's Degree": 0.20,
        "Professional Degree": 0.05,
        "Doctoral Degree": 0.05
    },
    "Professional Degree": {
        "Less than High School": 0.01,
        "High School Diploma": 0.05,
        "Some College": 0.08,
        "Associate's Degree": 0.10,
        "Bachelor's Degree": 0.35,
        "Master's Degree": 0.20,
        "Professional Degree": 0.15,
        "Doctoral Degree": 0.06
    },
    "Doctoral Degree": {
        "Less than High School": 0.01,
        "High School Diploma": 0.04,
        "Some College": 0.08,
        "Associate's Degree": 0.08,
        "Bachelor's Degree": 0.33,
        "Master's Degree": 0.25,
        "Professional Degree": 0.06,
        "Doctoral Degree": 0.15
    },
    "N/A": {
        "Less than High School": 0.10,
        "High School Diploma": 0.25,
        "Some College": 0.20,
        "Associate's Degree": 0.15,
        "Bachelor's Degree": 0.20,
        "Master's Degree": 0.06,
        "Professional Degree": 0.02,
        "Doctoral Degree": 0.02
    }
}


def get_education_projection(
    education_level: str,
    current_age: int,
    retirement_age: int = None,
    work_life_adjustment: float = 0.0,
    growth_rate: float = 0.03,
    gender_adjustment: float = 0.0,
    regional_adjustment: float = 0.0,
    date_of_birth: Optional[date] = None,
    use_statistical_retirement: bool = True
) -> Dict:
    """
    Calculate income projections based on educational attainment.
    
    Args:
        education_level: The level of education (must match keys in ANNUAL_EARNINGS_BY_EDUCATION)
        current_age: Current age of the individual
        retirement_age: Expected retirement age (if None, will use statistical data)
        work_life_adjustment: Adjustment factor for worklife expectancy (+ or - percentage)
        growth_rate: Annual income growth rate
        gender_adjustment: Adjustment factor for gender wage differences (percentage)
        regional_adjustment: Regional income adjustment factor (percentage)
        date_of_birth: Date of birth for more precise maturity calculations
        use_statistical_retirement: Whether to use statistical retirement data
        
    Returns:
        Dictionary with income projection data
    """
    # Get base earnings for this education level
    if education_level not in ANNUAL_EARNINGS_BY_EDUCATION:
        raise ValueError(f"Unknown education level: {education_level}")
    
    base_annual_income = ANNUAL_EARNINGS_BY_EDUCATION[education_level]
    
    # Apply adjustments
    adjusted_income = base_annual_income * (1 + regional_adjustment) * (1 + gender_adjustment)
    
    # Get work entry age based on education level
    entry_age = WORKFORCE_ENTRY_AGE.get(education_level, 18)  # Default to 18 if not found
    
    # Use statistical retirement age if available and requested
    if use_statistical_retirement and education_level in STATISTICAL_RETIREMENT_DATA:
        stat_data = STATISTICAL_RETIREMENT_DATA[education_level]
        
        # Override entry age if needed
        entry_age = stat_data["entry_age"]
        
        # Use statistical retirement age if not provided
        if retirement_age is None:
            retirement_age = stat_data["retirement_age"]
            
        # Get worklife expectancy
        worklife_expectancy = stat_data["wle"]
        worklife_ratio = stat_data["worklife_ratio"] / 100  # Convert to decimal
        age_final_separation = stat_data["age_final_separation"]
        
    else:
        # Use default retirement age
        if retirement_age is None:
            retirement_age = 67  # Standard retirement age
        
        # Calculate basic worklife expectancy
        worklife_expectancy = retirement_age - entry_age
        worklife_ratio = 1.0  # Default to 100%
        age_final_separation = retirement_age
    
    # Years until the child reaches occupational maturity
    years_until_entry = max(0, entry_age - current_age)
    
    # Calculate years in workforce from entry age to retirement
    years_in_workforce = worklife_expectancy
    
    # Apply worklife adjustment
    adjusted_years = int(years_in_workforce * (1 + work_life_adjustment))
    
    # Generate year-by-year projections
    projections = []
    current_income = adjusted_income
    
    # Add pre-workforce years (zero earnings until occupational maturity reached)
    for _ in range(years_until_entry):
        projections.append(0)  # No income during education years/before workforce entry
    
    # Add working years with growth
    for year in range(adjusted_years):
        projections.append(current_income)
        current_income *= (1 + growth_rate)  # Apply growth rate
    
    # Get unemployment rate
    unemployment_rate = UNEMPLOYMENT_RATES_BY_EDUCATION.get(education_level, 5.0) / 100
    
    # Get labor force participation rate
    participation_rate = PARTICIPATION_RATES_BY_EDUCATION.get(education_level, 60.0) / 100
    
    # Calculate days to occupational maturity with precise date calculations
    days_to_maturity = years_until_entry * 365  # Default approximation
    
    if date_of_birth:
        today = date.today()
        # Calculate the date when the person reaches their entry age
        birth_year, birth_month, birth_day = date_of_birth.year, date_of_birth.month, date_of_birth.day
        maturity_date = date(birth_year + entry_age, birth_month, birth_day)
        
        # If the maturity date is in the past, set days to zero
        if maturity_date <= today:
            days_to_maturity = 0
        else:
            days_to_maturity = (maturity_date - today).days
    
    return {
        "education_level": education_level,
        "base_annual_income": base_annual_income,
        "adjusted_annual_income": adjusted_income,
        "work_entry_age": entry_age,
        "retirement_age": retirement_age,
        "statistical_retirement_age": STATISTICAL_RETIREMENT_DATA.get(education_level, {}).get("retirement_age") 
            if education_level in STATISTICAL_RETIREMENT_DATA else None,
        "worklife_expectancy": worklife_expectancy,
        "worklife_ratio": worklife_ratio * 100,  # Convert to percentage for display
        "age_final_separation": age_final_separation,
        "years_until_entry": years_until_entry,
        "days_to_maturity": days_to_maturity,
        "years_in_workforce": adjusted_years,
        "unemployment_rate": unemployment_rate,
        "participation_rate": participation_rate,
        "income_projections": projections,
        "total_lifetime_earnings": sum(projections),
        "present_value_factor": None  # To be calculated later with discount rates
    }


def calculate_education_probabilities(parent1_education: str, parent2_education: Optional[str] = None) -> Dict[str, float]:
    """
    Calculate the probability of a child achieving different education levels
    based on their parents' education.
    
    Args:
        parent1_education: Education level of first parent
        parent2_education: Education level of second parent (optional)
        
    Returns:
        Dictionary mapping education levels to probabilities
    """
    # Standardize parent education categories to match our data
    def standardize_education(edu):
        if not edu or edu == "" or edu == "N/A":
            return "N/A"  # Use N/A as default
        return edu
    
    parent1 = standardize_education(parent1_education)
    
    # If parent1 is not in our probability dictionary, use N/A
    if parent1 not in EDUCATION_PROBABILITY_BY_PARENT:
        parent1 = "N/A"
    
    # If only one parent's education is provided or second parent is N/A
    if not parent2_education or standardize_education(parent2_education) == "N/A":
        return EDUCATION_PROBABILITY_BY_PARENT[parent1]
    
    # If both parents' education is provided, average the probabilities
    parent2 = standardize_education(parent2_education)
    
    # If parent2 is not in our probability dictionary, use N/A
    if parent2 not in EDUCATION_PROBABILITY_BY_PARENT:
        parent2 = "N/A"
    
    p1_probs = EDUCATION_PROBABILITY_BY_PARENT[parent1]
    p2_probs = EDUCATION_PROBABILITY_BY_PARENT[parent2]
    
    # Average the probabilities
    avg_probs = {}
    for edu_level in p1_probs.keys():
        avg_probs[edu_level] = (p1_probs[edu_level] + p2_probs.get(edu_level, p1_probs[edu_level])) / 2
    
    return avg_probs


def calculate_weighted_projections(
    current_age: int,
    retirement_age: int = None,
    education_probabilities: Optional[Dict[str, float]] = None,
    regional_adjustment: float = 0.0,
    gender_adjustment: float = 0.0,
    growth_rate: float = 0.03,
    date_of_birth: Optional[date] = None,
    use_statistical_retirement: bool = True
) -> Dict:
    """
    Calculate weighted income projections based on probabilities of different
    education levels.
    
    Args:
        current_age: Current age of the individual
        retirement_age: Expected retirement age
        education_probabilities: Dictionary mapping education levels to probabilities
        regional_adjustment: Regional income adjustment factor
        gender_adjustment: Gender-based income adjustment factor
        growth_rate: Annual income growth rate
        date_of_birth: Date of birth for more precise maturity calculations
        use_statistical_retirement: Whether to use statistical retirement data
        
    Returns:
        Dictionary with weighted projection data
    """
    # If no probabilities provided, use default distribution
    if not education_probabilities:
        education_probabilities = {
            "High School Diploma": 0.3,
            "Some College": 0.2,
            "Associate's Degree": 0.2,
            "Bachelor's Degree": 0.2,
            "Master's Degree": 0.08,
            "Professional Degree": 0.01,
            "Doctoral Degree": 0.01
        }
    
    projections_by_level = {}
    weighted_total = 0
    weighted_projections = []
    max_projection_length = 0
    
    # Calculate projections for each education level
    for edu_level, probability in education_probabilities.items():
        # Skip tiny probabilities
        if probability < 0.01:
            continue
        
        projection = get_education_projection(
            education_level=edu_level,
            current_age=current_age,
            retirement_age=retirement_age,
            regional_adjustment=regional_adjustment,
            gender_adjustment=gender_adjustment,
            growth_rate=growth_rate,
            date_of_birth=date_of_birth,
            use_statistical_retirement=use_statistical_retirement
        )
        
        projections_by_level[edu_level] = projection
        weighted_total += projection["total_lifetime_earnings"] * probability
        
        # Track the maximum projection length
        projection_length = len(projection["income_projections"])
        if projection_length > max_projection_length:
            max_projection_length = projection_length
    
    # Create weighted projection array (year by year)
    weighted_projections = [0] * max_projection_length
    
    for edu_level, projection in projections_by_level.items():
        probability = education_probabilities[edu_level]
        income_array = projection["income_projections"]
        
        # Pad shorter arrays with zeros
        padded_income = income_array + [0] * (max_projection_length - len(income_array))
        
        # Add weighted values to the result
        for i in range(max_projection_length):
            weighted_projections[i] += padded_income[i] * probability
    
    return {
        "education_probabilities": education_probabilities,
        "projections_by_level": projections_by_level,
        "weighted_projections": weighted_projections,
        "weighted_total_lifetime_earnings": weighted_total
    }


def apply_discount_rates(
    projections: List[float],
    discount_rates: List[float],
    current_age: int
) -> Dict[float, float]:
    """
    Apply various discount rates to income projections.
    
    Args:
        projections: List of yearly income projections
        discount_rates: List of discount rates to apply (as percentages)
        current_age: Current age of the individual
        
    Returns:
        Dictionary mapping discount rates to present values
    """
    present_values = {}
    
    for rate in discount_rates:
        discount_factor = rate / 100  # Convert percentage to decimal
        
        present_value = 0
        for i, income in enumerate(projections):
            # Discount from the future year to present
            present_value += income / ((1 + discount_factor) ** (i))
        
        present_values[rate] = present_value
    
    return present_values 