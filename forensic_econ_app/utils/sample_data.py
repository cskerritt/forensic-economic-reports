"""
Sample Data Generator for Testing Economic Analysis Tool

This module provides sample data sets for testing the economic analysis functionality,
including earnings scenarios, evaluee information, and various calculation parameters.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
import random


class SampleDataGenerator:
    """Generate sample data for testing purposes."""
    
    def __init__(self):
        self.sample_occupations = [
            "Software Engineer", "Registered Nurse", "Teacher", "Accountant", 
            "Construction Worker", "Sales Manager", "Marketing Specialist", 
            "Mechanical Engineer", "Physical Therapist", "Police Officer"
        ]
        
        self.sample_injuries = [
            "Motor vehicle accident resulting in back injury and chronic pain",
            "Workplace fall causing shoulder injury and limited range of motion",
            "Construction accident resulting in traumatic brain injury",
            "Slip and fall incident causing knee injury requiring multiple surgeries",
            "Industrial accident resulting in hand injury and reduced dexterity",
            "Sports-related injury causing permanent leg disability",
            "Medical malpractice resulting in neurological complications"
        ]
        
        self.states = [
            "California", "Texas", "Florida", "New York", "Pennsylvania", 
            "Illinois", "Ohio", "Georgia", "North Carolina", "Michigan"
        ]
        
        self.education_levels = [
            "High School", "Associate's Degree", "Bachelor's Degree", 
            "Master's Degree", "Doctorate"
        ]
    
    def generate_sample_evaluee(self, sample_type="moderate_case"):
        """Generate a sample evaluee with realistic data."""
        samples = {
            "high_earner": {
                "first_name": "Michael",
                "last_name": "Thompson",
                "occupation": "Software Engineer",
                "base_earnings": 125000,
                "education_level": "Master's Degree",
                "age_at_injury": 35,
                "injury_severity": "moderate",
                "residual_capacity": 0.4  # 40% residual capacity
            },
            "moderate_case": {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "occupation": "Registered Nurse",
                "base_earnings": 75000,
                "education_level": "Bachelor's Degree",
                "age_at_injury": 42,
                "injury_severity": "significant",
                "residual_capacity": 0.2  # 20% residual capacity
            },
            "construction_worker": {
                "first_name": "Robert",
                "last_name": "Martinez",
                "occupation": "Construction Worker",
                "base_earnings": 55000,
                "education_level": "High School",
                "age_at_injury": 28,
                "injury_severity": "severe",
                "residual_capacity": 0.0  # Total disability
            },
            "young_professional": {
                "first_name": "Jennifer",
                "last_name": "Chen",
                "occupation": "Marketing Specialist",
                "base_earnings": 62000,
                "education_level": "Bachelor's Degree",
                "age_at_injury": 26,
                "injury_severity": "moderate",
                "residual_capacity": 0.5  # 50% residual capacity
            },
            "senior_worker": {
                "first_name": "David",
                "last_name": "Wilson",
                "occupation": "Mechanical Engineer",
                "base_earnings": 95000,
                "education_level": "Bachelor's Degree",
                "age_at_injury": 55,
                "injury_severity": "significant",
                "residual_capacity": 0.3  # 30% residual capacity
            }
        }
        
        template = samples.get(sample_type, samples["moderate_case"])
        
        # Generate dates
        injury_date = datetime.now() - timedelta(days=random.randint(30, 730))  # 1 month to 2 years ago
        birth_date = injury_date - timedelta(days=template["age_at_injury"] * 365.25)
        
        # Calculate work life expectancy based on age and occupation
        remaining_years = 65 - template["age_at_injury"]  # Assume retirement at 65
        work_life_expectancy = max(5, remaining_years - random.randint(0, 5))
        
        # Calculate life expectancy (roughly)
        life_expectancy = 78 - template["age_at_injury"]  # Average life expectancy
        
        return {
            "first_name": template["first_name"],
            "last_name": template["last_name"],
            "date_of_birth": birth_date.date(),
            "date_of_injury": injury_date.date(),
            "state": random.choice(self.states),
            "occupation": template["occupation"],
            "education_level": template["education_level"],
            "base_earnings": template["base_earnings"],
            "life_expectancy": life_expectancy,
            "work_life_expectancy": work_life_expectancy,
            "years_to_final_separation": work_life_expectancy - 2,  # Usually 2 years before work life ends
            "injury_description": random.choice(self.sample_injuries),
            "injury_severity": template["injury_severity"],
            "residual_capacity": template["residual_capacity"],
            "uses_discounting": True,
            "discount_rates": [2.5, 3.0, 3.5]
        }
    
    def generate_sample_scenarios(self, evaluee_data):
        """Generate sample earnings scenarios for testing."""
        scenarios = []
        
        base_wage = evaluee_data["base_earnings"]
        injury_date = evaluee_data["date_of_injury"]
        birth_date = evaluee_data["date_of_birth"]
        work_life_expectancy = evaluee_data["work_life_expectancy"]
        residual_capacity = evaluee_data["residual_capacity"]
        
        # Calculate end date
        end_date = injury_date + timedelta(days=work_life_expectancy * 365.25)
        
        # Conservative Scenario
        scenarios.append({
            "scenario_name": "Conservative Scenario",
            "description": "Conservative economic assumptions with lower growth projections",
            "start_date": injury_date,
            "end_date": end_date,
            "wage_base": base_wage,
            "residual_base": base_wage * residual_capacity,
            "growth_rate": 0.02,  # 2% growth
            "discount_rate": 0.03,  # 3% discount
            "use_pre_post_injury": True,
            "injury_date": injury_date,
            "pre_injury_wage": base_wage,
            "post_injury_wage": base_wage * residual_capacity,
            "pre_injury_growth_rate": 0.025,
            "post_injury_growth_rate": 0.015,
            "methodology": "Conservative methodology using lower bound economic assumptions",
            "assumptions": [
                "Conservative wage growth based on inflation trends",
                "Higher discount rate reflecting economic uncertainty",
                "Minimal career advancement assumptions",
                "Conservative residual earning capacity estimate"
            ]
        })
        
        # Moderate Scenario
        scenarios.append({
            "scenario_name": "Moderate Scenario", 
            "description": "Realistic economic assumptions based on historical averages",
            "start_date": injury_date,
            "end_date": end_date,
            "wage_base": base_wage,
            "residual_base": base_wage * residual_capacity,
            "growth_rate": 0.035,  # 3.5% growth
            "discount_rate": 0.025,  # 2.5% discount
            "use_pre_post_injury": True,
            "injury_date": injury_date,
            "pre_injury_wage": base_wage,
            "post_injury_wage": base_wage * residual_capacity,
            "pre_injury_growth_rate": 0.035,
            "post_injury_growth_rate": 0.02,
            "methodology": "Moderate methodology using historical economic averages",
            "assumptions": [
                "Standard wage growth based on BLS historical data",
                "Market-based discount rate",
                "Typical career advancement patterns",
                "Realistic residual earning capacity assessment"
            ]
        })
        
        # Optimistic Scenario
        scenarios.append({
            "scenario_name": "Optimistic Scenario",
            "description": "Optimistic economic assumptions for maximum loss calculation",
            "start_date": injury_date,
            "end_date": end_date,
            "wage_base": base_wage,
            "residual_base": base_wage * (residual_capacity * 0.7),  # Even lower residual capacity
            "growth_rate": 0.05,  # 5% growth
            "discount_rate": 0.02,  # 2% discount
            "use_pre_post_injury": True,
            "injury_date": injury_date,
            "pre_injury_wage": base_wage,
            "post_injury_wage": base_wage * (residual_capacity * 0.7),
            "pre_injury_growth_rate": 0.045,
            "post_injury_growth_rate": 0.025,
            "methodology": "Optimistic methodology using favorable economic assumptions",
            "assumptions": [
                "High wage growth reflecting strong economic performance",
                "Low discount rate based on favorable market conditions", 
                "Strong career advancement potential",
                "Conservative residual capacity reflecting injury impact"
            ]
        })
        
        return scenarios
    
    def generate_household_services_data(self, evaluee_data):
        """Generate sample household services scenarios."""
        return {
            "scenario_name": "Standard Household Services",
            "base_rate": 25.00,  # $25/hour
            "hours_per_week": 20,
            "growth_rate": 0.03,
            "discount_rate": 0.025,
            "stages": [
                {
                    "stage_name": "Current Period",
                    "years": 10,
                    "hours_per_week": 20,
                    "rate_per_hour": 25.00
                },
                {
                    "stage_name": "Later Period", 
                    "years": 15,
                    "hours_per_week": 15,
                    "rate_per_hour": 30.00
                }
            ]
        }
    
    def get_predefined_samples(self):
        """Get a list of predefined sample data sets."""
        return {
            "high_earner": {
                "name": "High-Income Software Engineer",
                "description": "35-year-old software engineer with $125K salary, moderate injury",
                "typical_loss_range": "$800K - $1.2M"
            },
            "moderate_case": {
                "name": "Registered Nurse - Standard Case",
                "description": "42-year-old nurse with $75K salary, significant injury",
                "typical_loss_range": "$400K - $600K"
            },
            "construction_worker": {
                "name": "Construction Worker - Severe Injury",
                "description": "28-year-old construction worker, total disability",
                "typical_loss_range": "$600K - $900K"
            },
            "young_professional": {
                "name": "Young Marketing Professional",
                "description": "26-year-old marketing specialist, long work life ahead",
                "typical_loss_range": "$500K - $800K"
            },
            "senior_worker": {
                "name": "Senior Engineer - Pre-Retirement",
                "description": "55-year-old mechanical engineer, shorter remaining work life",
                "typical_loss_range": "$200K - $350K"
            }
        }


# Global instance
_sample_generator = None

def get_sample_generator():
    """Get the global sample data generator instance."""
    global _sample_generator
    if _sample_generator is None:
        _sample_generator = SampleDataGenerator()
    return _sample_generator

def create_sample_evaluee(sample_type="moderate_case"):
    """Create a sample evaluee with realistic data."""
    generator = get_sample_generator()
    return generator.generate_sample_evaluee(sample_type)

def create_sample_scenarios(evaluee_data):
    """Create sample earnings scenarios for an evaluee."""
    generator = get_sample_generator()
    return generator.generate_sample_scenarios(evaluee_data)