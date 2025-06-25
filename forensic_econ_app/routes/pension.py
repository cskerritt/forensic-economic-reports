from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from ..models.models import db, Evaluee, PensionScenario
from datetime import datetime

pension = Blueprint('pension', __name__)

@pension.route('/pension/<int:evaluee_id>')
@login_required
def pension_form(evaluee_id):
    """Display pension analysis form."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)
    if evaluee.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('evaluee.index'))
    
    scenarios = PensionScenario.query.filter_by(evaluee_id=evaluee_id).order_by(
        PensionScenario.created_at.desc()
    ).all()
    
    return render_template('pension/form.html', 
                         evaluee=evaluee, 
                         scenarios=scenarios)

@pension.route('/pension/<int:evaluee_id>/scenario/<int:scenario_id>/retirement_options')
@login_required
def get_retirement_options(evaluee_id, scenario_id):
    """Get retirement options for a pension scenario."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)
    if evaluee.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    scenario = PensionScenario.query.get_or_404(scenario_id)
    if scenario.evaluee_id != evaluee_id:
        return jsonify({'error': 'Invalid scenario'}), 400
    
    if scenario.calculation_method != 'payments':
        return jsonify({'error': 'Retirement options only available for payment scenarios'}), 400
    
    # Calculate retirement options
    options = scenario.calculate_retirement_options()
    
    return jsonify({'options': options})

@pension.route('/pension/<int:evaluee_id>', methods=['POST'])
@login_required
def create_scenario(evaluee_id):
    """Create a new pension scenario."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)
    if evaluee.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('evaluee.index'))
    
    try:
        # Basic scenario parameters
        scenario = PensionScenario(
            evaluee_id=evaluee_id,
            scenario_name=request.form.get('scenario_name'),
            calculation_method=request.form.get('calculation_method'),
            growth_rate=float(request.form.get('growth_rate')) / 100,  # Convert from percentage
            discount_rate=float(request.form.get('discount_rate')) / 100  # Convert from percentage
        )
        
        # Pension type parameters
        scenario.pension_type = request.form.get('pension_type', 'defined_benefit')
        
        if scenario.pension_type in ['defined_contribution', 'hybrid']:
            employer_match = request.form.get('employer_match_percentage')
            if employer_match:
                scenario.employer_match_percentage = float(employer_match)
            
            vesting_period = request.form.get('vesting_period')
            if vesting_period:
                scenario.vesting_period = int(vesting_period)
            
            vesting_percentage = request.form.get('vesting_percentage')
            if vesting_percentage:
                scenario.vesting_percentage = float(vesting_percentage)
        
        # Social Security parameters
        scenario.include_social_security = 'include_social_security' in request.form
        
        if scenario.include_social_security:
            ss_start_age = request.form.get('social_security_start_age')
            if ss_start_age:
                scenario.social_security_start_age = int(ss_start_age)
            
            ss_benefit = request.form.get('social_security_benefit')
            if ss_benefit:
                scenario.social_security_benefit = float(ss_benefit)
        
        # Early retirement parameters
        early_retirement_age = request.form.get('early_retirement_age')
        if early_retirement_age:
            scenario.early_retirement_age = int(early_retirement_age)
        
        early_retirement_penalty = request.form.get('early_retirement_penalty')
        if early_retirement_penalty:
            scenario.early_retirement_penalty = float(early_retirement_penalty) / 100  # Convert from percentage
        
        # Calculation method specific parameters
        if scenario.calculation_method == 'contributions':
            scenario.years_to_retirement = int(request.form.get('years_to_retirement'))
            scenario.annual_contribution = float(request.form.get('annual_contribution'))
        else:  # payments
            scenario.retirement_age = int(request.form.get('retirement_age'))
            scenario.life_expectancy = int(request.form.get('life_expectancy'))
            scenario.annual_pension_benefit = float(request.form.get('annual_pension_benefit'))
        
        # Calculate present value
        scenario.calculate_present_value()
        
        db.session.add(scenario)
        db.session.commit()
        
        flash('Pension scenario created successfully.')
        return redirect(url_for('pension.view_scenario', 
                              evaluee_id=evaluee_id, 
                              scenario_id=scenario.id))
    
    except ValueError as e:
        flash(f'Invalid input: {str(e)}')
    except Exception as e:
        flash('Error creating scenario.')
    
    return redirect(url_for('pension.pension_form', evaluee_id=evaluee_id))

@pension.route('/pension/<int:evaluee_id>/scenario/<int:scenario_id>')
@login_required
def view_scenario(evaluee_id, scenario_id):
    """View a pension scenario."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)
    if evaluee.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('evaluee.index'))
    
    scenario = PensionScenario.query.get_or_404(scenario_id)
    if scenario.evaluee_id != evaluee_id:
        flash('Invalid scenario.')
        return redirect(url_for('pension.pension_form', evaluee_id=evaluee_id))
    
    return render_template('pension/view_scenario.html',
                         evaluee=evaluee,
                         scenario=scenario)

@pension.route('/pension/<int:evaluee_id>/scenario/<int:scenario_id>/edit', 
              methods=['GET', 'POST'])
@login_required
def edit_scenario(evaluee_id, scenario_id):
    """Edit a pension scenario."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)
    if evaluee.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('evaluee.index'))
    
    scenario = PensionScenario.query.get_or_404(scenario_id)
    if scenario.evaluee_id != evaluee_id:
        flash('Invalid scenario.')
        return redirect(url_for('pension.pension_form', evaluee_id=evaluee_id))
    
    if request.method == 'POST':
        try:
            # Basic scenario parameters
            scenario.scenario_name = request.form.get('scenario_name')
            scenario.calculation_method = request.form.get('calculation_method')
            scenario.growth_rate = float(request.form.get('growth_rate')) / 100
            scenario.discount_rate = float(request.form.get('discount_rate')) / 100
            
            # Pension type parameters
            scenario.pension_type = request.form.get('pension_type', 'defined_benefit')
            
            if scenario.pension_type in ['defined_contribution', 'hybrid']:
                employer_match = request.form.get('employer_match_percentage')
                if employer_match:
                    scenario.employer_match_percentage = float(employer_match)
                
                vesting_period = request.form.get('vesting_period')
                if vesting_period:
                    scenario.vesting_period = int(vesting_period)
                
                vesting_percentage = request.form.get('vesting_percentage')
                if vesting_percentage:
                    scenario.vesting_percentage = float(vesting_percentage)
            
            # Social Security parameters
            scenario.include_social_security = 'include_social_security' in request.form
            
            if scenario.include_social_security:
                ss_start_age = request.form.get('social_security_start_age')
                if ss_start_age:
                    scenario.social_security_start_age = int(ss_start_age)
                
                ss_benefit = request.form.get('social_security_benefit')
                if ss_benefit:
                    scenario.social_security_benefit = float(ss_benefit)
            
            # Early retirement parameters
            early_retirement_age = request.form.get('early_retirement_age')
            if early_retirement_age:
                scenario.early_retirement_age = int(early_retirement_age)
            else:
                scenario.early_retirement_age = None
            
            early_retirement_penalty = request.form.get('early_retirement_penalty')
            if early_retirement_penalty:
                scenario.early_retirement_penalty = float(early_retirement_penalty) / 100
            
            # Calculation method specific parameters
            if scenario.calculation_method == 'contributions':
                scenario.years_to_retirement = int(request.form.get('years_to_retirement'))
                scenario.annual_contribution = float(request.form.get('annual_contribution'))
                # Clear payments fields
                scenario.retirement_age = None
                scenario.life_expectancy = None
                scenario.annual_pension_benefit = None
            else:  # payments
                scenario.retirement_age = int(request.form.get('retirement_age'))
                scenario.life_expectancy = int(request.form.get('life_expectancy'))
                scenario.annual_pension_benefit = float(request.form.get('annual_pension_benefit'))
                # Clear contributions fields
                scenario.years_to_retirement = None
                scenario.annual_contribution = None
            
            # Recalculate present value
            scenario.calculate_present_value()
            
            db.session.commit()
            flash('Scenario updated successfully.')
            return redirect(url_for('pension.view_scenario', 
                                  evaluee_id=evaluee_id, 
                                  scenario_id=scenario_id))
        
        except ValueError as e:
            flash(f'Invalid input: {str(e)}')
        except Exception as e:
            flash(f'Error updating scenario: {str(e)}')
    
    return render_template('pension/edit_scenario.html', 
                         evaluee=evaluee, 
                         scenario=scenario)

@pension.route('/pension/<int:evaluee_id>/scenario/<int:scenario_id>/delete', 
              methods=['POST'])
@login_required
def delete_scenario(evaluee_id, scenario_id):
    """Delete a pension scenario."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)
    if evaluee.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('evaluee.index'))
    
    scenario = PensionScenario.query.get_or_404(scenario_id)
    if scenario.evaluee_id != evaluee_id:
        flash('Invalid scenario.')
        return redirect(url_for('pension.pension_form', evaluee_id=evaluee_id))
    
    try:
        db.session.delete(scenario)
        db.session.commit()
        flash('Scenario deleted successfully.')
    except Exception as e:
        flash('Error deleting scenario.')
    
    return redirect(url_for('pension.pension_form', evaluee_id=evaluee_id)) 