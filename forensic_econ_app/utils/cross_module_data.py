"""
Cross-module data sharing utilities
Reduces duplicate data entry by sharing evaluee information across modules
"""
from datetime import datetime, date
from ..models.models import Evaluee, EarningsScenario, HouseholdServicesScenario


def get_evaluee_context(evaluee_id):
    """Get comprehensive evaluee context for use across modules"""
    evaluee = Evaluee.query.get(evaluee_id)
    if not evaluee:
        return None
    
    # Basic demographic info
    context = {
        'evaluee': evaluee,
        'demographic_data': {
            'name': f"{evaluee.first_name} {evaluee.last_name}",
            'age': evaluee.current_age,
            'gender': evaluee.gender,
            'state': evaluee.state,
            'date_of_birth': evaluee.date_of_birth,
            'date_of_injury': evaluee.date_of_injury,
            'regional_adjustment': float(evaluee.regional_adjustment) if evaluee.regional_adjustment else 1.0,
        },
        'economic_params': {
            'uses_discounting': evaluee.uses_discounting,
            'discount_rates': evaluee.discount_rates,
            'regional_adjustment': float(evaluee.regional_adjustment) if evaluee.regional_adjustment else 1.0,
        }
    }
    
    # Get latest earnings data for cross-module use
    latest_earnings = EarningsScenario.query.filter_by(evaluee_id=evaluee_id).order_by(EarningsScenario.created_at.desc()).first()
    if latest_earnings:
        context['latest_earnings'] = {
            'wage_base': float(latest_earnings.wage_base) if latest_earnings.wage_base else None,
            'growth_rate': float(latest_earnings.growth_rate) if latest_earnings.growth_rate else None,
            'start_date': latest_earnings.start_date,
            'end_date': latest_earnings.end_date,
            'injury_date': latest_earnings.injury_date,
            'report_date': latest_earnings.report_date,
        }
    
    # Get latest household services data
    latest_household = HouseholdServicesScenario.query.filter_by(evaluee_id=evaluee_id).order_by(HouseholdServicesScenario.created_at.desc()).first()
    if latest_household:
        context['latest_household'] = {
            'growth_rate': float(latest_household.growth_rate) if latest_household.growth_rate else None,
            'start_date': latest_household.start_date,
            'end_date': latest_household.end_date,
        }
    
    return context


def get_shared_defaults(evaluee_id, module_type):
    """Get smart defaults for a specific module based on evaluee and existing data"""
    context = get_evaluee_context(evaluee_id)
    if not context:
        return {}
    
    defaults = {
        'report_date': date.today().isoformat(),
        'evaluee_name': context['demographic_data']['name'],
        'state': context['demographic_data']['state'],
        'age': context['demographic_data']['age'],
    }
    
    # Add regional adjustment
    if context['economic_params']['regional_adjustment']:
        defaults['regional_adjustment'] = context['economic_params']['regional_adjustment']
    
    # Module-specific defaults
    if module_type == 'earnings':
        defaults.update({
            'growth_rate': 3.2,
            'discount_rate': 3.5,
            'adjustment_factor': 100,
        })
        
        # Use existing earnings data if available
        if context.get('latest_earnings'):
            latest = context['latest_earnings']
            if latest['start_date']:
                defaults['suggested_start_date'] = latest['start_date'].isoformat()
            if latest['end_date']:
                defaults['suggested_end_date'] = latest['end_date'].isoformat()
            if latest['injury_date']:
                defaults['injury_date'] = latest['injury_date'].isoformat()
            if latest['report_date']:
                defaults['report_date'] = latest['report_date'].isoformat()
            if latest['growth_rate']:
                defaults['growth_rate'] = latest['growth_rate']
    
    elif module_type == 'household':
        defaults.update({
            'growth_rate': 4.0,
            'discount_rate': 4.0,
        })
        
        # Use existing household data if available
        if context.get('latest_household'):
            latest = context['latest_household']
            if latest['growth_rate']:
                defaults['growth_rate'] = latest['growth_rate']
    
    elif module_type == 'life_care_plan':
        defaults.update({
            'inflation_rate': 2.5,
            'discount_rate': 3.0,
        })
    
    elif module_type == 'fringe_benefits':
        defaults.update({
            'growth_rate': 3.2,
            'discount_rate': 3.5,
        })
        
        # Use wage data from earnings if available
        if context.get('latest_earnings') and context['latest_earnings']['wage_base']:
            defaults['base_wage'] = context['latest_earnings']['wage_base']
    
    return defaults


def suggest_scenario_name(evaluee_id, module_type, scenario_count=None):
    """Generate intelligent scenario names"""
    context = get_evaluee_context(evaluee_id)
    if not context:
        return f"{module_type.title()} Scenario"
    
    evaluee_name = context['demographic_data']['name']
    age = context['demographic_data']['age']
    
    # Get scenario count if not provided
    if scenario_count is None:
        if module_type == 'earnings':
            scenario_count = len(context['evaluee'].earnings_scenarios)
        else:
            scenario_count = 0
    
    scenario_num = scenario_count + 1
    
    # Generate context-aware names
    if module_type == 'earnings':
        if scenario_num == 1:
            return f"{evaluee_name} - Base Earnings"
        elif scenario_num == 2:
            return f"{evaluee_name} - Alternative Scenario"
        else:
            return f"{evaluee_name} - Scenario {scenario_num}"
    
    elif module_type == 'household':
        if age and age < 18:
            return f"{evaluee_name} - Pediatric Household Services"
        elif age and age > 65:
            return f"{evaluee_name} - Senior Household Services"
        else:
            return f"{evaluee_name} - Household Services"
    
    elif module_type == 'life_care_plan':
        return f"{evaluee_name} - Life Care Plan"
    
    elif module_type == 'fringe_benefits':
        return f"{evaluee_name} - Fringe Benefits"
    
    return f"{evaluee_name} - {module_type.title()}"


def get_consistent_dates(evaluee_id):
    """Get consistent date ranges across all modules for an evaluee"""
    context = get_evaluee_context(evaluee_id)
    if not context:
        return None
    
    # Find the most comprehensive date range
    earliest_start = None
    latest_end = None
    common_injury_date = None
    common_report_date = None
    
    # Check earnings scenarios
    if context.get('latest_earnings'):
        earnings = context['latest_earnings']
        if earnings['start_date']:
            earliest_start = earnings['start_date']
        if earnings['end_date']:
            latest_end = earnings['end_date']
        if earnings['injury_date']:
            common_injury_date = earnings['injury_date']
        if earnings['report_date']:
            common_report_date = earnings['report_date']
    
    # Check household scenarios
    if context.get('latest_household'):
        household = context['latest_household']
        if household['start_date']:
            if not earliest_start or household['start_date'] < earliest_start:
                earliest_start = household['start_date']
        if household['end_date']:
            if not latest_end or household['end_date'] > latest_end:
                latest_end = household['end_date']
    
    return {
        'suggested_start_date': earliest_start.isoformat() if earliest_start else None,
        'suggested_end_date': latest_end.isoformat() if latest_end else None,
        'injury_date': common_injury_date.isoformat() if common_injury_date else None,
        'report_date': common_report_date.isoformat() if common_report_date else date.today().isoformat(),
    }


def validate_cross_module_consistency(evaluee_id):
    """Validate consistency across modules and suggest corrections"""
    context = get_evaluee_context(evaluee_id)
    if not context:
        return []
    
    warnings = []
    
    # Check for inconsistent date ranges
    if context.get('latest_earnings') and context.get('latest_household'):
        earnings_dates = context['latest_earnings']
        household_dates = context['latest_household']
        
        if (earnings_dates['start_date'] and household_dates['start_date'] and 
            abs((earnings_dates['start_date'] - household_dates['start_date']).days) > 365):
            warnings.append({
                'type': 'date_inconsistency',
                'message': 'Earnings and household services have very different start dates',
                'suggestion': 'Consider using consistent date ranges across modules'
            })
    
    # Check for missing demographic data
    if not context['demographic_data']['date_of_birth']:
        warnings.append({
            'type': 'missing_demographic',
            'message': 'Date of birth not set',
            'suggestion': 'Set date of birth for automatic age calculation and work life expectancy'
        })
    
    if not context['demographic_data']['date_of_injury']:
        warnings.append({
            'type': 'missing_injury_date',
            'message': 'Date of injury not set',
            'suggestion': 'Set injury date for proper pre/post injury analysis'
        })
    
    return warnings


def get_module_completion_status(evaluee_id):
    """Get completion status across all modules for dashboard display"""
    evaluee = Evaluee.query.get(evaluee_id)
    if not evaluee:
        return {}
    
    status = {
        'demographics': {
            'completed': bool(evaluee.date_of_birth and evaluee.gender and evaluee.state),
            'fields_completed': sum([
                bool(evaluee.date_of_birth),
                bool(evaluee.gender), 
                bool(evaluee.state),
                bool(evaluee.date_of_injury)
            ]),
            'total_fields': 4
        },
        'earnings': {
            'completed': len(evaluee.earnings_scenarios) > 0,
            'scenario_count': len(evaluee.earnings_scenarios)
        },
        'household': {
            'completed': len(getattr(evaluee, 'household_scenarios', [])) > 0,
            'scenario_count': len(getattr(evaluee, 'household_scenarios', []))
        },
        'life_care_plan': {
            'completed': False,  # TODO: Add LCP completion check
            'scenario_count': 0
        }
    }
    
    # Calculate overall completion percentage
    total_modules = len(status)
    completed_modules = sum(1 for module in status.values() if module['completed'])
    status['overall_completion'] = int((completed_modules / total_modules) * 100)
    
    return status