from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import logging

# Delay model imports to avoid dependency issues at module level
def get_models():
    """Import models only when needed to avoid initialization issues."""
    try:
        from ..models.models import db, Evaluee, EarningsScenario, HouseholdServicesScenario, HouseholdServicesStage
        return db, Evaluee, EarningsScenario, HouseholdServicesScenario, HouseholdServicesStage
    except ImportError as e:
        raise ImportError(f"Failed to import models: {e}")

def get_sample_utils():
    """Import sample utilities only when needed."""
    try:
        from ..utils.sample_data import get_sample_generator, create_sample_evaluee, create_sample_scenarios
        return get_sample_generator, create_sample_evaluee, create_sample_scenarios
    except ImportError as e:
        raise ImportError(f"Failed to import sample data utilities: {e}")

logger = logging.getLogger(__name__)

bp = Blueprint('sample_data', __name__)

@bp.route('/sample-data')
@login_required
def sample_data_page():
    """Display sample data options page."""
    try:
        get_sample_generator, _, _ = get_sample_utils()
        generator = get_sample_generator()
        predefined_samples = generator.get_predefined_samples()
        
        return render_template('sample_data/index.html', 
                             predefined_samples=predefined_samples)
    except Exception as e:
        logger.error(f"Error loading sample data page: {str(e)}")
        flash(f'Error loading sample data page: {str(e)}', 'danger')
        return redirect(url_for('evaluee.index'))

@bp.route('/sample-data/load/<sample_type>')
@login_required
def load_sample_data(sample_type):
    """Load predefined sample data and create evaluee with scenarios."""
    try:
        # Get imports
        db, Evaluee, EarningsScenario, HouseholdServicesScenario, HouseholdServicesStage = get_models()
        get_sample_generator, create_sample_evaluee, create_sample_scenarios = get_sample_utils()
        
        # Generate sample evaluee data
        evaluee_data = create_sample_evaluee(sample_type)
        
        # Create evaluee in database
        evaluee = Evaluee(
            user_id=current_user.id,
            first_name=evaluee_data['first_name'],
            last_name=evaluee_data['last_name'],
            date_of_birth=evaluee_data['date_of_birth'],
            date_of_injury=evaluee_data['date_of_injury'],
            state=evaluee_data['state'],
            education_level=evaluee_data['education_level'],
            life_expectancy=evaluee_data['life_expectancy'],
            work_life_expectancy=evaluee_data['work_life_expectancy'],
            years_to_final_separation=evaluee_data['years_to_final_separation'],
            uses_discounting=evaluee_data['uses_discounting']
        )
        
        db.session.add(evaluee)
        db.session.flush()  # Get the evaluee ID
        
        # Generate and create sample scenarios
        sample_scenarios = create_sample_scenarios(evaluee_data)
        
        for scenario_data in sample_scenarios:
            scenario = EarningsScenario(
                evaluee_id=evaluee.id,
                scenario_name=scenario_data['scenario_name'],
                start_date=scenario_data['start_date'],
                end_date=scenario_data['end_date'],
                wage_base=scenario_data['wage_base'],
                residual_base=scenario_data['residual_base'],
                growth_rate=scenario_data['growth_rate'],
                adjustment_factor=1.0,
                # Pre/Post injury fields
                injury_date=scenario_data.get('injury_date'),
                pre_injury_wage=scenario_data.get('pre_injury_wage'),
                post_injury_wage=scenario_data.get('post_injury_wage'),
                pre_injury_growth_rate=scenario_data.get('pre_injury_growth_rate'),
                post_injury_growth_rate=scenario_data.get('post_injury_growth_rate')
            )
            
            # Calculate pre/post injury values if applicable
            if scenario.injury_date:
                scenario.calculate_pre_post_injury_values(scenario_data['discount_rate'])
            else:
                # Calculate traditional present value
                from ..utils.calculations import calculate_present_value
                years = (scenario.end_date - scenario.start_date).days / 365.25
                annual_loss = scenario.wage_base - scenario.residual_base
                scenario.present_value = calculate_present_value(
                    annual_loss, years, scenario.growth_rate, scenario_data['discount_rate']
                )
                scenario.total_loss = annual_loss * years * (1 + scenario.growth_rate) ** (years/2)
            
            db.session.add(scenario)
        
        # Create sample household services scenario
        generator = get_sample_generator()
        household_data = generator.generate_household_services_data(evaluee_data)
        
        household_scenario = HouseholdServicesScenario(
            evaluee_id=evaluee.id,
            scenario_name=household_data['scenario_name'],
            base_rate=household_data['base_rate'],
            hours_per_week=household_data['hours_per_week'],
            growth_rate=household_data['growth_rate'],
            discount_rate=household_data['discount_rate']
        )
        
        db.session.add(household_scenario)
        db.session.flush()  # Get the household scenario ID
        
        # Add household service stages
        for stage_data in household_data['stages']:
            stage = HouseholdServicesStage(
                scenario_id=household_scenario.id,
                stage_name=stage_data['stage_name'],
                years=stage_data['years'],
                hours_per_week=stage_data['hours_per_week'],
                rate_per_hour=stage_data['rate_per_hour']
            )
            db.session.add(stage)
        
        # Calculate household services present value
        household_scenario.calculate_present_value()
        
        db.session.commit()
        
        flash(f'Sample data "{sample_type}" loaded successfully! Evaluee created with multiple scenarios.', 'success')
        return redirect(url_for('evaluee.view', evaluee_id=evaluee.id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error loading sample data: {str(e)}")
        flash(f'Error loading sample data: {str(e)}', 'danger')
        return redirect(url_for('sample_data.sample_data_page'))

@bp.route('/sample-data/custom', methods=['GET', 'POST'])
@login_required 
def custom_sample_data():
    """Create custom sample data with user inputs."""
    if request.method == 'POST':
        try:
            # Get imports
            db, Evaluee, EarningsScenario, HouseholdServicesScenario, HouseholdServicesStage = get_models()
            get_sample_generator, create_sample_evaluee, create_sample_scenarios = get_sample_utils()
            # Get custom parameters from form
            first_name = request.form.get('first_name', 'Test')
            last_name = request.form.get('last_name', 'User')
            age_at_injury = int(request.form.get('age_at_injury', 35))
            base_earnings = float(request.form.get('base_earnings', 75000))
            occupation = request.form.get('occupation', 'Professional')
            education_level = request.form.get('education_level', "Bachelor's Degree")
            state = request.form.get('state', 'California')
            injury_severity = request.form.get('injury_severity', 'moderate')
            
            # Calculate residual capacity based on injury severity
            residual_capacity_map = {
                'mild': 0.7,      # 70% residual capacity
                'moderate': 0.4,  # 40% residual capacity  
                'severe': 0.1,    # 10% residual capacity
                'total': 0.0      # Total disability
            }
            residual_capacity = residual_capacity_map.get(injury_severity, 0.4)
            
            # Generate dates
            injury_date = datetime.now().date()
            birth_date = datetime(
                injury_date.year - age_at_injury,
                injury_date.month,
                injury_date.day
            ).date()
            
            # Calculate work life expectancy
            remaining_years = 65 - age_at_injury
            work_life_expectancy = max(5, remaining_years)
            life_expectancy = 78 - age_at_injury
            
            # Create custom evaluee data
            evaluee_data = {
                'first_name': first_name,
                'last_name': last_name,
                'date_of_birth': birth_date,
                'date_of_injury': injury_date,
                'state': state,
                'occupation': occupation,
                'education_level': education_level,
                'base_earnings': base_earnings,
                'life_expectancy': life_expectancy,
                'work_life_expectancy': work_life_expectancy,
                'years_to_final_separation': work_life_expectancy - 2,
                'injury_description': f'Custom test case - {injury_severity} injury',
                'injury_severity': injury_severity,
                'residual_capacity': residual_capacity,
                'uses_discounting': True,
                'discount_rates': [2.5, 3.0, 3.5]
            }
            
            # Create evaluee in database  
            evaluee = Evaluee(
                user_id=current_user.id,
                first_name=evaluee_data['first_name'],
                last_name=evaluee_data['last_name'],
                date_of_birth=evaluee_data['date_of_birth'],
                date_of_injury=evaluee_data['date_of_injury'],
                state=evaluee_data['state'],
                education_level=evaluee_data['education_level'],
                life_expectancy=evaluee_data['life_expectancy'],
                work_life_expectancy=evaluee_data['work_life_expectancy'],
                years_to_final_separation=evaluee_data['years_to_final_separation'],
                uses_discounting=evaluee_data['uses_discounting']
            )
            
            db.session.add(evaluee)
            db.session.flush()
            
            # Generate scenarios based on custom data
            sample_scenarios = create_sample_scenarios(evaluee_data)
            
            for scenario_data in sample_scenarios:
                scenario = EarningsScenario(
                    evaluee_id=evaluee.id,
                    scenario_name=scenario_data['scenario_name'],
                    start_date=scenario_data['start_date'],
                    end_date=scenario_data['end_date'],
                    wage_base=scenario_data['wage_base'],
                    residual_base=scenario_data['residual_base'],
                    growth_rate=scenario_data['growth_rate'],
                    adjustment_factor=1.0,
                    injury_date=scenario_data.get('injury_date'),
                    pre_injury_wage=scenario_data.get('pre_injury_wage'),
                    post_injury_wage=scenario_data.get('post_injury_wage'),
                    pre_injury_growth_rate=scenario_data.get('pre_injury_growth_rate'),
                    post_injury_growth_rate=scenario_data.get('post_injury_growth_rate')
                )
                
                # Calculate values
                if scenario.injury_date:
                    scenario.calculate_pre_post_injury_values(scenario_data['discount_rate'])
                
                db.session.add(scenario)
            
            db.session.commit()
            
            flash('Custom sample data created successfully!', 'success')
            return redirect(url_for('evaluee.view', evaluee_id=evaluee.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating custom sample data: {str(e)}")
            flash(f'Error creating custom sample data: {str(e)}', 'danger')
            return redirect(url_for('sample_data.custom_sample_data'))
    
    # GET request - show form
    return render_template('sample_data/custom.html')

@bp.route('/api/sample-data/preview/<sample_type>')
@login_required
def preview_sample_data(sample_type):
    """Preview sample data without creating it."""
    try:
        # Get imports
        get_sample_generator, create_sample_evaluee, create_sample_scenarios = get_sample_utils()
        
        evaluee_data = create_sample_evaluee(sample_type)
        scenarios = create_sample_scenarios(evaluee_data)
        
        # Format dates for JSON serialization
        evaluee_data['date_of_birth'] = evaluee_data['date_of_birth'].strftime('%Y-%m-%d')
        evaluee_data['date_of_injury'] = evaluee_data['date_of_injury'].strftime('%Y-%m-%d')
        
        for scenario in scenarios:
            scenario['start_date'] = scenario['start_date'].strftime('%Y-%m-%d')
            scenario['end_date'] = scenario['end_date'].strftime('%Y-%m-%d')
            if scenario.get('injury_date'):
                scenario['injury_date'] = scenario['injury_date'].strftime('%Y-%m-%d')
        
        return jsonify({
            'success': True,
            'evaluee_data': evaluee_data,
            'scenarios': scenarios
        })
        
    except Exception as e:
        logger.error(f"Error previewing sample data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500