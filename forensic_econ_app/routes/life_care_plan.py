"""
Life Care Plan Routes

Flask routes for managing life care plans, scenarios, and services.
Adapted from mcp_streamlit for Flask integration.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime, date
from decimal import Decimal
import logging

from ..models.models import db
from ..models.life_care_plan import (
    LCPEvaluee, LifeCarePlan, LCPScenario, LCPServiceTable, LCPService, 
    LCPServiceAssignment, ServiceType, ServiceCategory
)
from ..utils.life_care_calculator import LifeCarePlanCalculator
from ..utils.life_care_exporters import create_life_care_plan_export

logger = logging.getLogger(__name__)

bp = Blueprint('life_care_plan', __name__, url_prefix='/life-care-plan')


# Evaluee Management Routes

@bp.route('/evaluees')
@login_required
def evaluees_index():
    """List all life care plan evaluees for the current user."""
    evaluees = LCPEvaluee.query.filter_by(user_id=current_user.id).order_by(LCPEvaluee.created_at.desc()).all()
    return render_template('life_care_plan/evaluees/index.html', evaluees=evaluees)


@bp.route('/evaluees/create', methods=['GET', 'POST'])
@login_required
def create_evaluee():
    """Create a new life care plan evaluee."""
    if request.method == 'POST':
        try:
            evaluee = LCPEvaluee(
                user_id=current_user.id,
                first_name=request.form.get('first_name', '').strip(),
                last_name=request.form.get('last_name', '').strip(),
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d'),
                date_of_injury=datetime.strptime(request.form.get('date_of_injury'), '%Y-%m-%d') if request.form.get('date_of_injury') else None,
                gender=request.form.get('gender'),
                address=request.form.get('address'),
                city=request.form.get('city'),
                state=request.form.get('state'),
                zip_code=request.form.get('zip_code'),
                phone=request.form.get('phone'),
                email=request.form.get('email'),
                primary_diagnosis=request.form.get('primary_diagnosis'),
                secondary_diagnoses=request.form.get('secondary_diagnoses'),
                injury_description=request.form.get('injury_description'),
                current_medical_status=request.form.get('current_medical_status'),
                life_expectancy=Decimal(request.form.get('life_expectancy')) if request.form.get('life_expectancy') else None,
                life_expectancy_source=request.form.get('life_expectancy_source'),
                pre_injury_income=Decimal(request.form.get('pre_injury_income')) if request.form.get('pre_injury_income') else None,
                occupation=request.form.get('occupation'),
                education_level=request.form.get('education_level')
            )
            
            db.session.add(evaluee)
            db.session.commit()
            
            flash(f'Evaluee "{evaluee.full_name}" created successfully.', 'success')
            return redirect(url_for('life_care_plan.view_evaluee', evaluee_id=evaluee.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating evaluee: {str(e)}")
            flash(f'Error creating evaluee: {str(e)}', 'danger')
    
    return render_template('life_care_plan/evaluees/create.html')


@bp.route('/evaluees/<int:evaluee_id>')
@login_required
def view_evaluee(evaluee_id):
    """View evaluee details and associated life care plans."""
    evaluee = LCPEvaluee.query.filter_by(id=evaluee_id, user_id=current_user.id).first_or_404()
    plans = LifeCarePlan.query.filter_by(evaluee_id=evaluee_id, user_id=current_user.id).order_by(LifeCarePlan.created_at.desc()).all()
    
    return render_template('life_care_plan/evaluees/view.html', evaluee=evaluee, plans=plans)


@bp.route('/evaluees/<int:evaluee_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_evaluee(evaluee_id):
    """Edit evaluee information."""
    evaluee = LCPEvaluee.query.filter_by(id=evaluee_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            evaluee.first_name = request.form.get('first_name', '').strip()
            evaluee.last_name = request.form.get('last_name', '').strip()
            evaluee.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d')
            evaluee.date_of_injury = datetime.strptime(request.form.get('date_of_injury'), '%Y-%m-%d') if request.form.get('date_of_injury') else None
            evaluee.gender = request.form.get('gender')
            evaluee.address = request.form.get('address')
            evaluee.city = request.form.get('city')
            evaluee.state = request.form.get('state')
            evaluee.zip_code = request.form.get('zip_code')
            evaluee.phone = request.form.get('phone')
            evaluee.email = request.form.get('email')
            evaluee.primary_diagnosis = request.form.get('primary_diagnosis')
            evaluee.secondary_diagnoses = request.form.get('secondary_diagnoses')
            evaluee.injury_description = request.form.get('injury_description')
            evaluee.current_medical_status = request.form.get('current_medical_status')
            evaluee.life_expectancy = Decimal(request.form.get('life_expectancy')) if request.form.get('life_expectancy') else None
            evaluee.life_expectancy_source = request.form.get('life_expectancy_source')
            evaluee.pre_injury_income = Decimal(request.form.get('pre_injury_income')) if request.form.get('pre_injury_income') else None
            evaluee.occupation = request.form.get('occupation')
            evaluee.education_level = request.form.get('education_level')
            evaluee.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Evaluee "{evaluee.full_name}" updated successfully.', 'success')
            return redirect(url_for('life_care_plan.view_evaluee', evaluee_id=evaluee.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating evaluee: {str(e)}")
            flash(f'Error updating evaluee: {str(e)}', 'danger')
    
    return render_template('life_care_plan/evaluees/edit.html', evaluee=evaluee)


# Life Care Plan Management Routes

@bp.route('/plans')
@login_required
def plans_index():
    """List all life care plans for the current user."""
    plans = LifeCarePlan.query.filter_by(user_id=current_user.id).order_by(LifeCarePlan.created_at.desc()).all()
    return render_template('life_care_plan/plans/index.html', plans=plans)


@bp.route('/evaluees/<int:evaluee_id>/plans/create', methods=['GET', 'POST'])
@login_required
def create_plan(evaluee_id):
    """Create a new life care plan for an evaluee."""
    evaluee = LCPEvaluee.query.filter_by(id=evaluee_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            plan = LifeCarePlan(
                evaluee_id=evaluee_id,
                user_id=current_user.id,
                plan_name=request.form.get('plan_name', '').strip(),
                plan_description=request.form.get('plan_description'),
                projection_start_age=Decimal(request.form.get('projection_start_age', '0')),
                projection_end_age=Decimal(request.form.get('projection_end_age', '75')),
                discount_rate=Decimal(request.form.get('discount_rate', '0.025')),
                inflation_rate=Decimal(request.form.get('inflation_rate', '0.03')),
                include_attendant_care=bool(request.form.get('include_attendant_care')),
                include_equipment_replacement=bool(request.form.get('include_equipment_replacement')),
                use_present_value=bool(request.form.get('use_present_value')),
                methodology_notes=request.form.get('methodology_notes'),
                assumptions=request.form.get('assumptions'),
                limitations=request.form.get('limitations')
            )
            
            db.session.add(plan)
            db.session.flush()  # Get the plan ID
            
            # Create default scenario
            default_scenario = LCPScenario(
                life_care_plan_id=plan.id,
                scenario_name='Default Scenario',
                scenario_description='Primary life care plan scenario',
                is_default=True
            )
            
            db.session.add(default_scenario)
            db.session.commit()
            
            flash(f'Life care plan "{plan.plan_name}" created successfully.', 'success')
            return redirect(url_for('life_care_plan.view_plan', plan_id=plan.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating plan: {str(e)}")
            flash(f'Error creating plan: {str(e)}', 'danger')
    
    return render_template('life_care_plan/plans/create.html', evaluee=evaluee)


@bp.route('/plans/<int:plan_id>')
@login_required
def view_plan(plan_id):
    """View life care plan details."""
    plan = LifeCarePlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    
    # Get calculation results for default scenario
    default_scenario = plan.default_scenario
    results = None
    summary = None
    
    if default_scenario and default_scenario.service_assignments:
        try:
            calculator = LifeCarePlanCalculator(plan)
            results = calculator.calculate_scenario(default_scenario)
            summary = calculator.generate_cost_summary(results)
        except Exception as e:
            logger.error(f"Error calculating plan: {str(e)}")
            flash(f'Error calculating plan: {str(e)}', 'warning')
    
    return render_template('life_care_plan/plans/view.html', 
                         plan=plan, results=results, summary=summary)


@bp.route('/plans/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_plan(plan_id):
    """Edit life care plan settings."""
    plan = LifeCarePlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            plan.plan_name = request.form.get('plan_name', '').strip()
            plan.plan_description = request.form.get('plan_description')
            plan.projection_start_age = Decimal(request.form.get('projection_start_age', '0'))
            plan.projection_end_age = Decimal(request.form.get('projection_end_age', '75'))
            plan.discount_rate = Decimal(request.form.get('discount_rate', '0.025'))
            plan.inflation_rate = Decimal(request.form.get('inflation_rate', '0.03'))
            plan.include_attendant_care = bool(request.form.get('include_attendant_care'))
            plan.include_equipment_replacement = bool(request.form.get('include_equipment_replacement'))
            plan.use_present_value = bool(request.form.get('use_present_value'))
            plan.methodology_notes = request.form.get('methodology_notes')
            plan.assumptions = request.form.get('assumptions')
            plan.limitations = request.form.get('limitations')
            plan.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Plan "{plan.plan_name}" updated successfully.', 'success')
            return redirect(url_for('life_care_plan.view_plan', plan_id=plan.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating plan: {str(e)}")
            flash(f'Error updating plan: {str(e)}', 'danger')
    
    return render_template('life_care_plan/plans/edit.html', plan=plan)


# Service Management Routes

@bp.route('/plans/<int:plan_id>/services')
@login_required
def manage_services(plan_id):
    """Manage services for a life care plan."""
    plan = LifeCarePlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    
    # Group services by table
    service_tables = LCPServiceTable.query.filter_by(life_care_plan_id=plan_id).order_by(LCPServiceTable.display_order).all()
    
    return render_template('life_care_plan/services/manage.html', plan=plan, service_tables=service_tables)


@bp.route('/plans/<int:plan_id>/service-tables/create', methods=['GET', 'POST'])
@login_required
def create_service_table(plan_id):
    """Create a new service table."""
    plan = LifeCarePlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            service_table = LCPServiceTable(
                life_care_plan_id=plan_id,
                table_name=request.form.get('table_name', '').strip(),
                table_description=request.form.get('table_description'),
                category=request.form.get('category'),
                display_order=int(request.form.get('display_order', 0))
            )
            
            db.session.add(service_table)
            db.session.commit()
            
            flash(f'Service table "{service_table.table_name}" created successfully.', 'success')
            return redirect(url_for('life_care_plan.manage_services', plan_id=plan_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating service table: {str(e)}")
            flash(f'Error creating service table: {str(e)}', 'danger')
    
    categories = [cat.value for cat in ServiceCategory]
    return render_template('life_care_plan/services/create_table.html', plan=plan, categories=categories)


@bp.route('/service-tables/<int:table_id>/services/create', methods=['GET', 'POST'])
@login_required
def create_service(table_id):
    """Create a new service in a service table."""
    service_table = LCPServiceTable.query.join(LifeCarePlan).filter(
        LCPServiceTable.id == table_id,
        LifeCarePlan.user_id == current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        try:
            service = LCPService(
                service_table_id=table_id,
                service_name=request.form.get('service_name', '').strip(),
                service_description=request.form.get('service_description'),
                service_type=request.form.get('service_type'),
                category=request.form.get('category'),
                unit_cost=Decimal(request.form.get('unit_cost', '0')),
                cost_year=int(request.form.get('cost_year', datetime.now().year)),
                frequency_per_year=Decimal(request.form.get('frequency_per_year')) if request.form.get('frequency_per_year') else None,
                start_age=Decimal(request.form.get('start_age', '0')),
                end_age=Decimal(request.form.get('end_age')) if request.form.get('end_age') else None,
                service_age=Decimal(request.form.get('service_age')) if request.form.get('service_age') else None,
                total_instances=int(request.form.get('total_instances')) if request.form.get('total_instances') else None,
                distribution_start_age=Decimal(request.form.get('distribution_start_age')) if request.form.get('distribution_start_age') else None,
                distribution_end_age=Decimal(request.form.get('distribution_end_age')) if request.form.get('distribution_end_age') else None,
                replacement_cycle_years=int(request.form.get('replacement_cycle_years')) if request.form.get('replacement_cycle_years') else None,
                include_replacement=bool(request.form.get('include_replacement')),
                notes=request.form.get('notes'),
                assumptions=request.form.get('assumptions'),
                source=request.form.get('source'),
                display_order=int(request.form.get('display_order', 0))
            )
            
            db.session.add(service)
            db.session.commit()
            
            flash(f'Service "{service.service_name}" created successfully.', 'success')
            return redirect(url_for('life_care_plan.manage_services', plan_id=service_table.life_care_plan_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating service: {str(e)}")
            flash(f'Error creating service: {str(e)}', 'danger')
    
    service_types = [st.value for st in ServiceType]
    categories = [cat.value for cat in ServiceCategory]
    
    return render_template('life_care_plan/services/create_service.html', 
                         service_table=service_table, service_types=service_types, categories=categories)


# Scenario Management Routes

@bp.route('/plans/<int:plan_id>/scenarios')
@login_required
def manage_scenarios(plan_id):
    """Manage scenarios for a life care plan."""
    plan = LifeCarePlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    
    return render_template('life_care_plan/scenarios/manage.html', plan=plan)


@bp.route('/plans/<int:plan_id>/scenarios/create', methods=['GET', 'POST'])
@login_required
def create_scenario(plan_id):
    """Create a new scenario."""
    plan = LifeCarePlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            scenario = LCPScenario(
                life_care_plan_id=plan_id,
                scenario_name=request.form.get('scenario_name', '').strip(),
                scenario_description=request.form.get('scenario_description'),
                discount_rate=Decimal(request.form.get('discount_rate')) if request.form.get('discount_rate') else None,
                inflation_rate=Decimal(request.form.get('inflation_rate')) if request.form.get('inflation_rate') else None,
                assumptions=request.form.get('assumptions'),
                methodology_notes=request.form.get('methodology_notes')
            )
            
            db.session.add(scenario)
            db.session.commit()
            
            flash(f'Scenario "{scenario.scenario_name}" created successfully.', 'success')
            return redirect(url_for('life_care_plan.manage_scenarios', plan_id=plan_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating scenario: {str(e)}")
            flash(f'Error creating scenario: {str(e)}', 'danger')
    
    return render_template('life_care_plan/scenarios/create.html', plan=plan)


@bp.route('/scenarios/<int:scenario_id>/calculate')
@login_required
def calculate_scenario(scenario_id):
    """Calculate and display scenario results."""
    scenario = LCPScenario.query.join(LifeCarePlan).filter(
        LCPScenario.id == scenario_id,
        LifeCarePlan.user_id == current_user.id
    ).first_or_404()
    
    try:
        calculator = LifeCarePlanCalculator(scenario.life_care_plan)
        results = calculator.calculate_scenario(scenario)
        summary = calculator.generate_cost_summary(results)
        
        # Update stored results
        scenario.total_cost = results.total_cost
        scenario.present_value = results.present_value
        scenario.calculation_date = results.calculation_date
        
        # Update service assignment results
        for calc in results.service_calculations:
            assignment = LCPServiceAssignment.query.filter_by(
                scenario_id=scenario_id,
                service_id=calc.service_id
            ).first()
            if assignment:
                assignment.total_cost = calc.total_cost
                assignment.present_value = calc.present_value
                assignment.first_year_cost = calc.first_year_cost
        
        db.session.commit()
        
        return render_template('life_care_plan/scenarios/results.html', 
                             scenario=scenario, results=results, summary=summary)
        
    except Exception as e:
        logger.error(f"Error calculating scenario: {str(e)}")
        flash(f'Error calculating scenario: {str(e)}', 'danger')
        return redirect(url_for('life_care_plan.manage_scenarios', plan_id=scenario.life_care_plan_id))


# API Routes

@bp.route('/api/plans/<int:plan_id>/validate')
@login_required
def validate_plan(plan_id):
    """Validate a life care plan."""
    plan = LifeCarePlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    
    try:
        calculator = LifeCarePlanCalculator(plan)
        errors = calculator.validate_plan()
        
        return jsonify({
            'success': True,
            'valid': len(errors) == 0,
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"Error validating plan: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/scenarios/<int:scenario_id>/quick-calculate')
@login_required
def quick_calculate_scenario(scenario_id):
    """Quick calculation for AJAX updates."""
    scenario = LCPScenario.query.join(LifeCarePlan).filter(
        LCPScenario.id == scenario_id,
        LifeCarePlan.user_id == current_user.id
    ).first_or_404()
    
    try:
        calculator = LifeCarePlanCalculator(scenario.life_care_plan)
        results = calculator.calculate_scenario(scenario)
        
        return jsonify({
            'success': True,
            'total_cost': float(results.total_cost),
            'present_value': float(results.present_value),
            'number_of_services': len(results.service_calculations),
            'category_totals': {k: float(v) for k, v in results.category_totals.items()}
        })
        
    except Exception as e:
        logger.error(f"Error in quick calculation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Export Routes

@bp.route('/plans/<int:plan_id>/export/<format>')
@login_required
def export_plan(plan_id, format):
    """Export a life care plan to Excel or Word format."""
    plan = LifeCarePlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    
    if format not in ['excel', 'word']:
        flash('Invalid export format requested.', 'danger')
        return redirect(url_for('life_care_plan.view_plan', plan_id=plan_id))
    
    try:
        # Calculate all scenarios
        calculator = LifeCarePlanCalculator(plan)
        scenario_results = []
        
        for scenario in plan.scenarios:
            if scenario.service_assignments:  # Only calculate scenarios with services
                results = calculator.calculate_scenario(scenario)
                scenario_results.append(results)
        
        if not scenario_results:
            flash('No scenarios with services found to export.', 'warning')
            return redirect(url_for('life_care_plan.view_plan', plan_id=plan_id))
        
        # Generate export
        file_content = create_life_care_plan_export(plan, scenario_results, format)
        
        # Determine filename and content type
        evaluee_name = plan.evaluee.full_name.replace(' ', '_')
        plan_name = plan.plan_name.replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'excel':
            filename = f"LCP_{evaluee_name}_{plan_name}_{timestamp}.xlsx"
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:  # word
            filename = f"LCP_{evaluee_name}_{plan_name}_{timestamp}.docx"
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        # Create file-like object
        import io
        file_obj = io.BytesIO(file_content)
        file_obj.seek(0)
        
        return send_file(
            file_obj,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        logger.error(f"Error exporting plan: {str(e)}")
        flash(f'Error exporting plan: {str(e)}', 'danger')
        return redirect(url_for('life_care_plan.view_plan', plan_id=plan_id))


@bp.route('/create-sample-data', methods=['POST'])
@login_required
def create_sample_data():
    """Create sample life care plan data for demonstration."""
    try:
        from ..utils.lcp_sample_data import create_complete_sample_data
        
        # Generate sample data
        sample_data = create_complete_sample_data(current_user.id)
        
        # Create evaluee
        evaluee = LCPEvaluee(**sample_data['evaluee'])
        db.session.add(evaluee)
        db.session.flush()  # Get the evaluee ID
        
        # Create life care plan
        plan_data = sample_data['life_care_plan'](evaluee.id)
        plan = LifeCarePlan(**plan_data)
        db.session.add(plan)
        db.session.flush()  # Get the plan ID
        
        # Create default scenario
        scenario = LCPScenario(
            plan_id=plan.id,
            name="Primary Scenario",
            description="Main life care plan scenario with all recommended services",
            discount_rate=plan.discount_rate,
            inflation_rate=plan.inflation_rate,
            medical_inflation_rate=plan.medical_inflation_rate,
            is_active=True
        )
        db.session.add(scenario)
        db.session.flush()
        
        # Create service table
        service_table = LCPServiceTable(
            plan_id=plan.id,
            name="Comprehensive Care Services",
            description="All recommended medical and support services"
        )
        db.session.add(service_table)
        db.session.flush()
        
        # Create services and assignments
        services_data = sample_data['services']
        for service_data in services_data:
            service = LCPService(
                table_id=service_table.id,
                **service_data
            )
            db.session.add(service)
            db.session.flush()
            
            # Create service assignment
            assignment = LCPServiceAssignment(
                scenario_id=scenario.id,
                service_id=service.id,
                is_included=True,
                override_unit_cost=None,
                override_frequency=None,
                notes=None
            )
            db.session.add(assignment)
        
        db.session.commit()
        
        flash(f'Sample life care plan created successfully for {evaluee.first_name} {evaluee.last_name}!', 'success')
        return redirect(url_for('life_care_plan.view_evaluee', evaluee_id=evaluee.id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating sample data: {str(e)}")
        flash(f'Error creating sample data: {str(e)}', 'danger')
        return redirect(url_for('life_care_plan.evaluees_index'))