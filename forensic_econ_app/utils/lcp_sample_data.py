"""
Life Care Plan Sample Data Generator

Provides realistic sample data for testing and demonstration of the Life Care Plan module.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
import random
from typing import Dict, List, Any

# Sample names and demographics
FIRST_NAMES = ["John", "Jane", "Michael", "Sarah", "Robert", "Emily", "David", "Lisa", "James", "Mary"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

# Sample diagnoses
PRIMARY_DIAGNOSES = [
    "Traumatic Brain Injury (TBI)",
    "Spinal Cord Injury - C5 Complete",
    "Multiple Trauma with Orthopedic Injuries",
    "Severe Burns - 40% TBSA",
    "Amputation - Below Knee Bilateral",
    "Chronic Pain Syndrome",
    "Post-Traumatic Stress Disorder (PTSD)",
    "Cerebral Palsy",
    "Stroke with Hemiplegia",
    "Multiple Sclerosis"
]

SECONDARY_DIAGNOSES = [
    "Depression", "Anxiety Disorder", "Chronic Pain", "Sleep Disorder",
    "Cognitive Impairment", "Mobility Limitation", "Visual Impairment",
    "Hearing Loss", "Diabetes Type 2", "Hypertension"
]

# Sample occupations
OCCUPATIONS = [
    "Software Engineer", "Teacher", "Nurse", "Construction Worker",
    "Sales Manager", "Accountant", "Mechanic", "Chef", "Police Officer",
    "Administrative Assistant"
]

# Sample medical services
MEDICAL_SERVICES = [
    {
        "name": "Primary Care Physician",
        "description": "Regular check-ups and general medical care",
        "unit_cost": Decimal("150.00"),
        "frequency": 12,  # times per year
        "service_type": "recurring"
    },
    {
        "name": "Physical Therapy",
        "description": "Rehabilitation and mobility improvement",
        "unit_cost": Decimal("125.00"),
        "frequency": 104,  # 2x per week
        "service_type": "recurring"
    },
    {
        "name": "Occupational Therapy",
        "description": "Daily living skills training",
        "unit_cost": Decimal("110.00"),
        "frequency": 52,  # weekly
        "service_type": "recurring"
    },
    {
        "name": "Medications",
        "description": "Monthly prescription medications",
        "unit_cost": Decimal("450.00"),
        "frequency": 12,
        "service_type": "recurring"
    },
    {
        "name": "Wheelchair - Power",
        "description": "Electric wheelchair with custom modifications",
        "unit_cost": Decimal("25000.00"),
        "replacement_years": 5,
        "service_type": "distributed"
    },
    {
        "name": "Home Modifications",
        "description": "Ramps, bathroom modifications, door widening",
        "unit_cost": Decimal("35000.00"),
        "service_type": "one_time"
    },
    {
        "name": "Psychological Counseling",
        "description": "Mental health support",
        "unit_cost": Decimal("175.00"),
        "frequency": 24,  # bi-weekly
        "service_type": "recurring"
    },
    {
        "name": "Home Health Aide",
        "description": "Daily living assistance",
        "unit_cost": Decimal("30.00"),
        "frequency": 1460,  # 4 hours/day
        "service_type": "recurring"
    },
    {
        "name": "Medical Equipment Supplies",
        "description": "Catheters, wound care, etc.",
        "unit_cost": Decimal("300.00"),
        "frequency": 12,
        "service_type": "recurring"
    },
    {
        "name": "Neuropsychological Testing",
        "description": "Annual cognitive assessment",
        "unit_cost": Decimal("2500.00"),
        "frequency": 1,
        "service_type": "recurring"
    }
]


def generate_sample_evaluee(user_id: int) -> Dict[str, Any]:
    """Generate a sample evaluee with realistic data."""
    
    # Generate basic demographics
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    # Generate dates
    birth_year = random.randint(1970, 2005)
    birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28))
    
    injury_year = random.randint(2020, 2024)
    injury_date = date(injury_year, random.randint(1, 12), random.randint(1, 28))
    
    # Calculate age and life expectancy
    current_age = (date.today() - birth_date).days // 365
    life_expectancy = random.randint(70, 85) - current_age
    
    # Generate address
    states = ["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "MI"]
    
    evaluee_data = {
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": birth_date,
        "date_of_injury": injury_date,
        "gender": random.choice(["Male", "Female"]),
        "address": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Elm', 'Maple', 'First'])} Street",
        "city": random.choice(["Los Angeles", "Houston", "Miami", "New York", "Philadelphia"]),
        "state": random.choice(states),
        "zip_code": f"{random.randint(10000, 99999)}",
        "phone": f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
        "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
        "primary_diagnosis": random.choice(PRIMARY_DIAGNOSES),
        "secondary_diagnoses": ", ".join(random.sample(SECONDARY_DIAGNOSES, random.randint(1, 3))),
        "injury_description": f"Individual sustained injuries in a {random.choice(['motor vehicle accident', 'workplace incident', 'fall', 'sports injury'])}. "
                            f"Primary injuries include {random.choice(['head trauma', 'spinal damage', 'multiple fractures', 'severe burns'])}.",
        "current_medical_status": random.choice([
            "Stable with ongoing therapy needs",
            "Improving but requires continued care",
            "Chronic condition requiring lifetime management",
            "Post-acute rehabilitation phase"
        ]),
        "life_expectancy": life_expectancy,
        "life_expectancy_source": random.choice([
            "CDC Life Tables",
            "Physician Assessment",
            "Actuarial Analysis",
            "Medical Literature"
        ]),
        "pre_injury_income": Decimal(str(random.randint(30000, 120000))),
        "occupation": random.choice(OCCUPATIONS),
        "education_level": random.choice([
            "High School",
            "Some College",
            "Bachelor's Degree",
            "Master's Degree",
            "Vocational Training"
        ])
    }
    
    return evaluee_data


def generate_sample_life_care_plan(evaluee_id: int) -> Dict[str, Any]:
    """Generate a sample life care plan."""
    
    plan_data = {
        "evaluee_id": evaluee_id,
        "plan_name": f"Comprehensive Life Care Plan - {datetime.now().year}",
        "description": "Complete medical and rehabilitation care plan based on current assessment",
        "base_year": datetime.now().year,
        "discount_rate": Decimal("3.5"),
        "inflation_rate": Decimal("2.5"),
        "medical_inflation_rate": Decimal("4.0"),
        "notes": "Plan developed based on medical records review, clinical evaluation, and consultation with treating physicians."
    }
    
    return plan_data


def generate_sample_services() -> List[Dict[str, Any]]:
    """Generate a list of sample services for a life care plan."""
    
    # Select a subset of services
    num_services = random.randint(6, 10)
    selected_services = random.sample(MEDICAL_SERVICES, num_services)
    
    services = []
    for i, service_template in enumerate(selected_services):
        service = {
            "name": service_template["name"],
            "description": service_template["description"],
            "category": random.choice([
                "Medical Care",
                "Therapy",
                "Equipment",
                "Medications",
                "Home Care",
                "Transportation"
            ]),
            "provider": f"{random.choice(['Regional', 'City', 'County'])} Medical Center",
            "unit_cost": service_template["unit_cost"],
            "unit_type": "visit" if "frequency" in service_template else "each",
            "frequency": service_template.get("frequency", 1),
            "frequency_unit": "year",
            "service_type": service_template["service_type"],
            "start_age": None,
            "end_age": None,
            "replacement_years": service_template.get("replacement_years"),
            "inflation_type": "medical",
            "notes": f"Recommended by treating physician",
            "sort_order": i
        }
        
        # Add age ranges for some services
        if random.random() > 0.7:
            service["start_age"] = random.randint(0, 20)
            service["end_age"] = service["start_age"] + random.randint(20, 50)
        
        services.append(service)
    
    return services


def create_complete_sample_data(user_id: int) -> Dict[str, Any]:
    """Create a complete sample dataset for demonstration."""
    
    return {
        "evaluee": generate_sample_evaluee(user_id),
        "life_care_plan": generate_sample_life_care_plan,  # Function to be called with evaluee_id
        "services": generate_sample_services()
    }