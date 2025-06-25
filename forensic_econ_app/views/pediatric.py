from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, jsonify
from forensic_econ_app.models import Evaluee, Analysis
from forensic_econ_app.models.models import db
from forensic_econ_app.calculators.education_projections import (
    calculate_education_probabilities,
    get_education_projection,
    calculate_weighted_projections,
    apply_discount_rates
)
import json
from decimal import Decimal
from datetime import datetime

bp = Blueprint('pediatric', __name__, url_prefix='/pediatric')


@bp.route('/analysis/<int:evaluee_id>', methods=['GET', 'POST'])
def create_analysis(evaluee_id):
    """Create a new pediatric economic analysis."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)
    
    if not evaluee.is_pediatric_case:
        flash('This evaluee is not marked as a pediatric case.', 'warning')
        return redirect(url_for('evaluee.detail', evaluee_id=evaluee_id))
    
    if request.method == 'POST':
        title = request.form.get('title', 'Pediatric Economic Analysis')
        current_age = int(request.form.get('current_age', 0))
        retirement_age = int(request.form.get('retirement_age', 67))
        
        # Get regional adjustment as percentage
        regional_adjustment_pct = float(request.form.get('regional_adjustment', 0))
        regional_adjustment = regional_adjustment_pct / 100
        
        # Get gender adjustment
        gender = request.form.get('gender', 'neutral')
        gender_adjustment = 0.0
        if gender == 'female':
            gender_adjustment = -0.18  # Example adjustment for gender wage gap
        
        # Get growth rate as percentage
        growth_rate_pct = float(request.form.get('growth_rate', 3))
        growth_rate = growth_rate_pct / 100
        
        # Educational scenarios to analyze
        education_scenarios = []
        if evaluee.calculate_hs_diploma:
            education_scenarios.append("High School Diploma")
        if evaluee.calculate_some_college:
            education_scenarios.append("Some College")
        if evaluee.calculate_associates:
            education_scenarios.append("Associate's Degree")
        if evaluee.calculate_bachelors:
            education_scenarios.append("Bachelor's Degree")
            
        if not education_scenarios:
            flash('At least one educational scenario must be selected.', 'danger')
            return render_template('pediatric/create.html', evaluee=evaluee)
        
        # Determine if statistical retirement data should be used
        use_statistical_retirement = bool(request.form.get('use_statistical_retirement', True))
        
        # Calculate education probabilities based on parental education
        education_probs = calculate_education_probabilities(
            evaluee.parent1_education, 
            evaluee.parent2_education
        )
        
        # Calculate weighted projections across education levels
        projections = calculate_weighted_projections(
            current_age=current_age,
            retirement_age=retirement_age if not use_statistical_retirement else None,
            education_probabilities=education_probs,
            regional_adjustment=regional_adjustment,
            gender_adjustment=gender_adjustment,
            growth_rate=growth_rate,
            date_of_birth=evaluee.date_of_birth.date() if evaluee.date_of_birth else None
        )
        
        # Calculate individual education level projections
        scenario_results = {}
        for edu_level in education_scenarios:
            scenario = get_education_projection(
                education_level=edu_level,
                current_age=current_age,
                retirement_age=retirement_age if not use_statistical_retirement else None,
                regional_adjustment=regional_adjustment,
                gender_adjustment=gender_adjustment,
                growth_rate=growth_rate,
                date_of_birth=evaluee.date_of_birth.date() if evaluee.date_of_birth else None,
                use_statistical_retirement=use_statistical_retirement
            )
            scenario_results[edu_level] = scenario
        
        # Apply discount rates if enabled
        discount_values = {}
        if evaluee.discounting and evaluee.discount_rates:
            # Apply to weighted projections
            discount_values['weighted'] = apply_discount_rates(
                projections['weighted_projections'], 
                evaluee.discount_rates, 
                current_age
            )
            
            # Apply to each education scenario
            for edu_level, scenario in scenario_results.items():
                discount_values[edu_level] = apply_discount_rates(
                    scenario['income_projections'],
                    evaluee.discount_rates,
                    current_age
                )
        
        # Create new analysis record
        analysis = Analysis(
            evaluee_id=evaluee.id,
            analysis_type='pediatric',
            title=title,
            parameters={
                'current_age': current_age,
                'retirement_age': retirement_age,
                'regional_adjustment': regional_adjustment,
                'gender': gender,
                'gender_adjustment': gender_adjustment,
                'growth_rate': growth_rate,
                'education_scenarios': education_scenarios,
                'education_probabilities': education_probs,
                'use_statistical_retirement': use_statistical_retirement
            },
            results={
                'weighted_projections': projections['weighted_projections'],
                'weighted_total': projections['weighted_total_lifetime_earnings'],
                'scenario_results': {
                    edu: {
                        'projections': scenario['income_projections'],
                        'total': scenario['total_lifetime_earnings'],
                        'entry_age': scenario['work_entry_age'],
                        'years_until_entry': scenario['years_until_entry'],
                        'days_to_maturity': scenario['days_to_maturity'],
                        'retirement_age': scenario['retirement_age'],
                        'statistical_retirement_age': scenario['statistical_retirement_age'],
                        'worklife_expectancy': scenario['worklife_expectancy'],
                        'worklife_ratio': scenario['worklife_ratio'],
                        'age_final_separation': scenario['age_final_separation']
                    } for edu, scenario in scenario_results.items()
                },
                'discount_values': discount_values
            },
            created_at=datetime.now()
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        flash(f'Pediatric economic analysis created successfully!', 'success')
        return redirect(url_for('pediatric.detail', analysis_id=analysis.id))
    
    return render_template('pediatric/create.html', evaluee=evaluee)


@bp.route('/detail/<int:analysis_id>')
def detail(analysis_id):
    """View a specific pediatric economic analysis."""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    if analysis.analysis_type != 'pediatric':
        flash('This is not a pediatric analysis.', 'warning')
        return redirect(url_for('evaluee.detail', evaluee_id=analysis.evaluee_id))
    
    evaluee = Evaluee.query.get_or_404(analysis.evaluee_id)
    
    return render_template('pediatric/detail.html', analysis=analysis, evaluee=evaluee)


@bp.route('/chart_data/<int:analysis_id>')
def chart_data(analysis_id):
    """Return chart data for the analysis in JSON format."""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    if analysis.analysis_type != 'pediatric':
        return jsonify({'error': 'Not a pediatric analysis'}), 400
    
    # Get parameters and results
    params = analysis.parameters
    results = analysis.results
    
    # Create data for different chart types
    chart_data = {
        'weighted_projection': {
            'labels': [f'Year {i+1}' for i in range(len(results['weighted_projections']))],
            'datasets': [{
                'label': 'Weighted Income Projection',
                'data': results['weighted_projections'],
                'borderColor': 'rgba(75, 192, 192, 1)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            }]
        },
        'education_scenarios': {
            'labels': [f'Year {i+1}' for i in range(max(
                len(data['projections']) for data in results['scenario_results'].values()
            ))],
            'datasets': [
                {
                    'label': f'{edu_level}',
                    'data': data['projections'],
                    'borderColor': f'hsl({i * 50}, 70%, 50%)',
                    'backgroundColor': f'hsla({i * 50}, 70%, 50%, 0.2)',
                } for i, (edu_level, data) in enumerate(results['scenario_results'].items())
            ]
        },
        'total_earnings': {
            'labels': list(results['scenario_results'].keys()) + ['Weighted Average'],
            'datasets': [{
                'label': 'Total Lifetime Earnings',
                'data': [
                    data['total'] for data in results['scenario_results'].values()
                ] + [results['weighted_total']],
                'backgroundColor': [
                    f'hsla({i * 50}, 70%, 50%, 0.6)' for i in range(len(results['scenario_results']) + 1)
                ],
            }]
        }
    }
    
    # Add discount rate data if available
    if 'discount_values' in results and results['discount_values']:
        discount_datasets = []
        for rate, value in results['discount_values'].get('weighted', {}).items():
            discount_datasets.append({
                'label': f'{rate}% Discount Rate',
                'value': value,
                'backgroundColor': f'hsla({float(rate) * 30}, 70%, 50%, 0.6)',
            })
        
        chart_data['discount_values'] = {
            'labels': [f'{rate}%' for rate in results['discount_values'].get('weighted', {}).keys()],
            'datasets': [{
                'label': 'Present Value at Different Discount Rates',
                'data': list(results['discount_values'].get('weighted', {}).values()),
                'backgroundColor': [
                    f'hsla({float(rate) * 30}, 70%, 50%, 0.6)' for rate in results['discount_values'].get('weighted', {}).keys()
                ],
            }]
        }
    
    return jsonify(chart_data)


@bp.route('/<int:analysis_id>/delete', methods=['POST'])
def delete(analysis_id):
    """Delete a pediatric analysis."""
    analysis = Analysis.query.get_or_404(analysis_id)
    evaluee_id = analysis.evaluee_id
    
    db.session.delete(analysis)
    db.session.commit()
    
    flash('Pediatric economic analysis deleted successfully.', 'success')
    return redirect(url_for('evaluee.detail', evaluee_id=evaluee_id)) 