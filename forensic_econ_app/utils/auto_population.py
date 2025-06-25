"""
Auto-population utilities for reducing data entry
"""
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from .us_states import get_default_parameters, get_state_adjustment


def get_current_date():
    """Get current date in ISO format for date inputs"""
    return date.today().isoformat()


def get_current_datetime():
    """Get current datetime in ISO format for datetime inputs"""
    return datetime.now().isoformat()


def calculate_age_from_dob(date_of_birth, reference_date=None):
    """Calculate age from date of birth"""
    if reference_date is None:
        reference_date = date.today()
    
    if isinstance(date_of_birth, str):
        date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
    
    if isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d').date()
    
    age = relativedelta(reference_date, date_of_birth)
    return age.years


def calculate_retirement_date(date_of_birth, retirement_age=67):
    """Calculate expected retirement date based on date of birth"""
    if isinstance(date_of_birth, str):
        date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
    
    retirement_date = date_of_birth + relativedelta(years=retirement_age)
    return retirement_date.isoformat()


def calculate_work_life_expectancy(date_of_birth, gender='M', education_level='high_school'):
    """Calculate work life expectancy based on demographics"""
    current_age = calculate_age_from_dob(date_of_birth)
    
    # Normalize gender input to handle both formats
    gender_normalized = gender
    if gender in ['Men', 'Male', 'M']:
        gender_normalized = 'M'
    elif gender in ['Women', 'Female', 'F']:
        gender_normalized = 'F'
    else:
        gender_normalized = 'M'  # Default to male
    
    # Base work life expectancy by gender (approximate years of work remaining)
    base_wle = {
        'M': {20: 42, 25: 37, 30: 32, 35: 27, 40: 22, 45: 17, 50: 12, 55: 7, 60: 3},
        'F': {20: 38, 25: 33, 30: 28, 35: 23, 40: 18, 45: 13, 50: 8, 55: 5, 60: 2}
    }
    
    # Education adjustments (higher education = longer work life)
    education_adjustments = {
        'less_than_high_school': -2,
        'high_school': 0,
        'some_college': 1,
        'associates': 2,
        'bachelors': 3,
        'masters': 4,
        'doctorate': 5
    }
    
    # Find closest age bracket
    age_brackets = sorted(base_wle[gender_normalized].keys())
    closest_age = min(age_brackets, key=lambda x: abs(x - current_age))
    
    base_years = base_wle[gender_normalized][closest_age]
    education_adj = education_adjustments.get(education_level, 0)
    
    # Adjust for current age if different from bracket
    age_diff = current_age - closest_age
    adjusted_years = max(0, base_years - age_diff + education_adj)
    
    work_end_date = date.today() + relativedelta(years=adjusted_years)
    return work_end_date.isoformat()


def get_smart_defaults(evaluee_data=None, form_type=None):
    """Get smart defaults for forms based on evaluee data and form type"""
    defaults = {
        'report_date': get_current_date(),
        'created_date': get_current_date(),
    }
    
    if evaluee_data:
        try:
            # Add age if date of birth is available
            if hasattr(evaluee_data, 'date_of_birth') and evaluee_data.date_of_birth:
                defaults['current_age'] = calculate_age_from_dob(evaluee_data.date_of_birth)
                defaults['retirement_date'] = calculate_retirement_date(evaluee_data.date_of_birth)
                
                # Add work life expectancy if we have enough demographic data
                if hasattr(evaluee_data, 'gender') and evaluee_data.gender:
                    education = getattr(evaluee_data, 'education_level', 'high_school')
                    defaults['work_end_date'] = calculate_work_life_expectancy(
                        evaluee_data.date_of_birth, 
                        evaluee_data.gender, 
                        education
                    )
            
            # Add state-specific defaults
            if hasattr(evaluee_data, 'state') and evaluee_data.state:
                state_defaults = get_default_parameters(evaluee_data.state)
                defaults.update(state_defaults)
        except Exception as e:
            # Log error but continue with basic defaults
            import logging
            logging.warning(f"Error calculating smart defaults: {e}")
            pass
    
    # Form-specific defaults
    if form_type == 'earnings':
        defaults.update({
            'growth_rate': 3.2,  # 3.2% annual growth
            'adjustment_factor': 100,  # 100% adjustment
            'discount_rate': 3.5,  # 3.5% discount rate
        })
    elif form_type == 'household':
        defaults.update({
            'growth_rate': 4.0,  # 4% for household services
            'discount_rate': 4.0,
        })
    elif form_type == 'life_care_plan':
        defaults.update({
            'inflation_rate': 2.5,  # 2.5% medical inflation
            'discount_rate': 3.0,
        })
    
    return defaults


def validate_date_sequence(start_date, injury_date=None, report_date=None, end_date=None):
    """Validate that dates are in logical sequence"""
    dates = []
    labels = []
    
    if start_date:
        dates.append(datetime.strptime(start_date, '%Y-%m-%d') if isinstance(start_date, str) else start_date)
        labels.append('Start Date')
    
    if injury_date:
        dates.append(datetime.strptime(injury_date, '%Y-%m-%d') if isinstance(injury_date, str) else injury_date)
        labels.append('Injury Date')
    
    if report_date:
        dates.append(datetime.strptime(report_date, '%Y-%m-%d') if isinstance(report_date, str) else report_date)
        labels.append('Report Date')
    
    if end_date:
        dates.append(datetime.strptime(end_date, '%Y-%m-%d') if isinstance(end_date, str) else end_date)
        labels.append('End Date')
    
    # Check if dates are in ascending order
    errors = []
    for i in range(len(dates) - 1):
        if dates[i] >= dates[i + 1]:
            errors.append(f"{labels[i]} must be before {labels[i + 1]}")
    
    return errors


def suggest_corrections(field_name, field_value, evaluee_data=None):
    """Suggest corrections for common data entry errors"""
    suggestions = []
    
    if field_name == 'wage_base' and field_value:
        try:
            wage = float(field_value)
            if wage < 1000:
                suggestions.append("Wage seems low. Did you mean to enter an annual salary?")
            elif wage > 500000:
                suggestions.append("Wage seems high. Please verify this amount.")
            elif wage > 100000 and evaluee_data and hasattr(evaluee_data, 'state'):
                # Check against state averages
                adjustment = get_state_adjustment(evaluee_data.state)
                national_avg = 55000
                state_avg = national_avg * adjustment
                if wage > state_avg * 3:
                    suggestions.append(f"Wage is significantly above {evaluee_data.state} average (${state_avg:,.0f})")
        except ValueError:
            suggestions.append("Please enter a valid number for wage")
    
    elif field_name == 'growth_rate' and field_value:
        try:
            rate = float(field_value)
            if rate > 20:
                suggestions.append("Growth rate seems high. Did you enter as a percentage? (e.g., 3.5 for 3.5%)")
            elif rate < 0:
                suggestions.append("Negative growth rate - please verify this is intentional")
        except ValueError:
            suggestions.append("Please enter a valid number for growth rate")
    
    return suggestions


def get_occupation_defaults(occupation_title=None, state=None):
    """Get default wage and growth data for occupation (integrates with existing BLS API)"""
    defaults = {}
    
    # This would integrate with the existing wage_data_api.py functionality
    if occupation_title and state:
        try:
            from .wage_data_api import get_wage_data
            wage_data = get_wage_data(occupation_title, state)
            if wage_data:
                defaults.update({
                    'suggested_wage': wage_data.get('annual_wage'),
                    'wage_source': 'BLS Data',
                    'regional_adjustment': wage_data.get('regional_adjustment', 1.0),
                })
        except ImportError:
            # wage_data_api not available
            pass
    
    return defaults