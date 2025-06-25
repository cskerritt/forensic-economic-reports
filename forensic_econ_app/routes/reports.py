from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from ..models.models import db, Evaluee, EarningsScenario, HouseholdServicesScenario
from ..utils.enhanced_calculator import calculate_comprehensive_analysis, get_enhanced_calculator
from ..utils.wage_data_api import lookup_occupation_wages
from ..utils.document_generator import generate_professional_report, get_document_generator
from ..utils.report_generator import EconomicReportGenerator, generate_scenario_comparison_report
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
from io import BytesIO
import json
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

bp = Blueprint('reports', __name__)

@bp.route('/reports/<int:evaluee_id>/combined')
@login_required
def combined_report(evaluee_id):
    """Generate a combined report with earnings, medical costs, and household services."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)

    # Check if user has access to this evaluee
    if evaluee.user_id != current_user.id:
        flash('You do not have access to this evaluee.', 'danger')
        return redirect(url_for('evaluee.index'))

    # Get the latest earnings scenario
    earnings_scenario = EarningsScenario.query.filter_by(evaluee_id=evaluee_id).order_by(EarningsScenario.created_at.desc()).first()

    # Medical cost analysis has been removed
    medical_analysis = None
    medical_procedures = []

    # Get the latest household services scenario
    household_scenario = HouseholdServicesScenario.query.filter_by(evaluee_id=evaluee_id).order_by(HouseholdServicesScenario.created_at.desc()).first()

    # Calculate current age if date of birth is available
    current_age = None
    if evaluee.date_of_birth:
        current_age = (datetime.now() - evaluee.date_of_birth).days / 365.25

    # Calculate total damages
    total_damages = 0
    if earnings_scenario and earnings_scenario.present_value:
        total_damages += earnings_scenario.present_value

    # Medical costs have been removed

    if household_scenario and household_scenario.present_value:
        total_damages += household_scenario.present_value

    return render_template(
        'reports/combined_report.html',
        evaluee=evaluee,
        earnings_scenario=earnings_scenario,
        medical_analysis=medical_analysis,
        medical_procedures=medical_procedures,
        household_scenario=household_scenario,
        current_age=current_age,
        total_damages=total_damages
    )

@bp.route('/reports/<int:evaluee_id>/download', methods=['GET'])
@login_required
def download_combined_report(evaluee_id):
    """Download a combined report as Excel."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)

    # Check if user has access to this evaluee
    if evaluee.user_id != current_user.id:
        flash('You do not have access to this evaluee.', 'danger')
        return redirect(url_for('evaluee.index'))

    # Get the IDs from the query parameters
    earnings_id = request.args.get('earnings_id', type=int, default=0)
    household_id = request.args.get('household_id', type=int, default=0)

    # Get the scenarios/analyses
    earnings_scenario = None
    if earnings_id > 0:
        earnings_scenario = EarningsScenario.query.get(earnings_id)

    # Medical cost analysis has been removed
    medical_analysis = None

    household_scenario = None
    if household_id > 0:
        household_scenario = HouseholdServicesScenario.query.get(household_id)

    # Create Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book

        # Create summary sheet
        summary_df = pd.DataFrame({
            'Category': ['Evaluee Information', '', '', '', '', '', 'Economic Damages', '', '', ''],
            'Item': ['Name', 'Date of Birth', 'Date of Injury', 'Current Age', 'Life Expectancy', 'Work Life Expectancy',
                    'Earnings Loss', 'Medical Costs', 'Household Services', 'Total Damages'],
            'Value': [
                f"{evaluee.first_name} {evaluee.last_name}",
                evaluee.date_of_birth.strftime('%Y-%m-%d') if evaluee.date_of_birth else 'Not set',
                evaluee.date_of_injury.strftime('%Y-%m-%d') if evaluee.date_of_injury else 'Not set',
                f"{((datetime.now() - evaluee.date_of_birth).days / 365.25):.2f} years" if evaluee.date_of_birth else 'Not set',
                f"{evaluee.life_expectancy} years" if evaluee.life_expectancy else 'Not set',
                f"{evaluee.work_life_expectancy:.2f} years" if evaluee.work_life_expectancy else 'Not set',
                f"${earnings_scenario.present_value:,.2f}" if earnings_scenario and earnings_scenario.present_value else 'N/A',
                'N/A',  # Medical costs have been removed
                f"${household_scenario.present_value:,.2f}" if household_scenario and household_scenario.present_value else 'N/A',
                f"${(earnings_scenario.present_value if earnings_scenario and earnings_scenario.present_value else 0) + (household_scenario.present_value if household_scenario and household_scenario.present_value else 0):,.2f}"
            ]
        })

        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        # Format summary sheet
        summary_sheet = writer.sheets['Summary']
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
        for col_num, value in enumerate(summary_df.columns.values):
            summary_sheet.write(0, col_num, value, header_format)

        # Add earnings sheet if available
        if earnings_scenario:
            # Create earnings data
            earnings_data = []
            start_date = earnings_scenario.start_date
            end_date = earnings_scenario.end_date
            current_date = start_date

            while current_date <= end_date:
                year = current_date.year
                age = ((current_date - evaluee.date_of_birth).days / 365.25) if evaluee.date_of_birth else None

                # Calculate wage for this year
                years_from_start = (current_date - start_date).days / 365.25
                wage = earnings_scenario.wage_base * (1 + earnings_scenario.growth_rate) ** years_from_start

                # Calculate present value
                years_to_discount = (current_date - start_date).days / 365.25
                present_value = wage / (1 + earnings_scenario.discount_rate) ** years_to_discount

                earnings_data.append({
                    'Year': year,
                    'Age': f"{age:.2f}" if age else 'N/A',
                    'Wage': wage,
                    'Present Value': present_value
                })

                # Move to next year
                current_date = datetime(current_date.year + 1, current_date.month, current_date.day)

            # Create DataFrame and write to Excel
            earnings_df = pd.DataFrame(earnings_data)
            earnings_df.to_excel(writer, sheet_name='Earnings Loss', index=False)

            # Format earnings sheet
            earnings_sheet = writer.sheets['Earnings Loss']
            for col_num, value in enumerate(earnings_df.columns.values):
                earnings_sheet.write(0, col_num, value, header_format)

        # Medical costs functionality has been removed

        # Add household services sheet if available
        if household_scenario:
            # Create household data
            household_data = []
            start_date = household_scenario.start_date
            end_date = household_scenario.end_date
            current_date = start_date

            while current_date <= end_date:
                year = current_date.year
                age = ((current_date - evaluee.date_of_birth).days / 365.25) if evaluee.date_of_birth else None

                # Calculate rate for this year
                years_from_start = (current_date - start_date).days / 365.25
                rate = household_scenario.base_rate * (1 + household_scenario.growth_rate) ** years_from_start

                # Calculate annual value
                annual_value = rate * household_scenario.hours_per_week * 52

                # Calculate present value
                years_to_discount = (current_date - start_date).days / 365.25
                present_value = annual_value / (1 + household_scenario.discount_rate) ** years_to_discount

                household_data.append({
                    'Year': year,
                    'Age': f"{age:.2f}" if age else 'N/A',
                    'Hourly Rate': rate,
                    'Annual Value': annual_value,
                    'Present Value': present_value
                })

                # Move to next year
                current_date = datetime(current_date.year + 1, current_date.month, current_date.day)

            # Create DataFrame and write to Excel
            household_df = pd.DataFrame(household_data)
            household_df.to_excel(writer, sheet_name='Household Services', index=False)

            # Format household sheet
            household_sheet = writer.sheets['Household Services']
            for col_num, value in enumerate(household_df.columns.values):
                household_sheet.write(0, col_num, value, header_format)

    # Set up response
    output.seek(0)
    filename = f"{evaluee.last_name}_{evaluee.first_name}_Combined_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@bp.route('/reports/<int:evaluee_id>/enhanced')
@login_required  
def enhanced_analysis_report(evaluee_id):
    """Generate enhanced economic analysis report with all new features."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)

    # Check if user has access to this evaluee
    if evaluee.user_id != current_user.id:
        flash('You do not have access to this evaluee.', 'danger')
        return redirect(url_for('evaluee.index'))

    try:
        # Prepare evaluee data for analysis
        evaluee_data = {
            'first_name': evaluee.first_name,
            'last_name': evaluee.last_name,
            'date_of_birth': evaluee.date_of_birth,
            'date_of_injury': evaluee.date_of_injury,
            'base_earnings': evaluee.base_earnings or 0,
            'education_level': evaluee.education_level,
            'gender': evaluee.gender,
            'life_expectancy': evaluee.life_expectancy,
            'work_life_expectancy': evaluee.work_life_expectancy,
            'years_to_final_separation': evaluee.years_to_final_separation,
            'occupation': getattr(evaluee, 'occupation', 'General'),
            'state': getattr(evaluee, 'state', 'National'),
            'msa': getattr(evaluee, 'msa', None),
            'wage_growth_rate': 0.032,
            'discount_rate': 0.045,
            'fringe_benefits_rate': 0.28
        }
        
        # Perform comprehensive analysis
        analysis_results = calculate_comprehensive_analysis(evaluee_data)
        
        return render_template(
            'reports/enhanced_analysis.html',
            evaluee=evaluee,
            evaluee_data=evaluee_data,
            analysis_results=analysis_results
        )
        
    except Exception as e:
        logger.error(f"Error generating enhanced analysis: {str(e)}")
        flash(f'Error generating enhanced analysis: {str(e)}', 'danger')
        return redirect(url_for('evaluee.view', evaluee_id=evaluee_id))

@bp.route('/reports/<int:evaluee_id>/wage-lookup')
@login_required
def wage_lookup_report(evaluee_id):
    """Generate wage lookup and market analysis report."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)

    # Check if user has access to this evaluee
    if evaluee.user_id != current_user.id:
        flash('You do not have access to this evaluee.', 'danger')
        return redirect(url_for('evaluee.index'))

    try:
        # Get occupation and location info
        occupation = getattr(evaluee, 'occupation', 'General Worker')
        state = getattr(evaluee, 'state', 'National')
        msa = getattr(evaluee, 'msa', None)
        
        # Lookup wage data
        wage_data = lookup_occupation_wages(occupation, state, msa)
        
        return render_template(
            'reports/wage_lookup.html',
            evaluee=evaluee,
            wage_data=wage_data,
            occupation=occupation,
            state=state,
            msa=msa
        )
        
    except Exception as e:
        logger.error(f"Error generating wage lookup: {str(e)}")
        flash(f'Error generating wage lookup: {str(e)}', 'danger')
        return redirect(url_for('evaluee.view', evaluee_id=evaluee_id))

@bp.route('/reports/<int:evaluee_id>/professional-document')
@login_required
def download_professional_document(evaluee_id):
    """Download professional Word document report."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)

    # Check if user has access to this evaluee
    if evaluee.user_id != current_user.id:
        flash('You do not have access to this evaluee.', 'danger')
        return redirect(url_for('evaluee.index'))

    try:
        # Get report type from query parameter
        report_type = request.args.get('type', 'comprehensive')
        
        # Prepare evaluee data
        evaluee_data = {
            'first_name': evaluee.first_name,
            'last_name': evaluee.last_name,
            'date_of_birth': evaluee.date_of_birth,
            'date_of_injury': evaluee.date_of_injury,
            'base_earnings': evaluee.base_earnings or 0,
            'education_level': evaluee.education_level,
            'gender': evaluee.gender,
            'life_expectancy': evaluee.life_expectancy,
            'work_life_expectancy': evaluee.work_life_expectancy,
            'occupation': getattr(evaluee, 'occupation', 'General'),
            'state': getattr(evaluee, 'state', 'National'),
            'injury_description': getattr(evaluee, 'injury_description', 'Injury details not provided.')
        }
        
        # Perform comprehensive analysis
        analysis_results = calculate_comprehensive_analysis(evaluee_data)
        
        # Generate professional document
        doc_buffer = generate_professional_report(evaluee_data, analysis_results, report_type)
        
        # Determine filename based on report type
        report_names = {
            'comprehensive': 'Comprehensive_Economic_Loss_Report',
            'settlement': 'Settlement_Analysis_Report',
            'expert_witness': 'Expert_Witness_Report'
        }
        
        report_name = report_names.get(report_type, 'Economic_Report')
        filename = f"{evaluee.last_name}_{evaluee.first_name}_{report_name}_{datetime.now().strftime('%Y%m%d')}.docx"
        
        return send_file(
            doc_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        logger.error(f"Error generating professional document: {str(e)}")
        flash(f'Error generating document: {str(e)}', 'danger')
        return redirect(url_for('evaluee.view', evaluee_id=evaluee_id))

@bp.route('/api/reports/<int:evaluee_id>/scenario-comparison')
@login_required
def api_scenario_comparison(evaluee_id):
    """API endpoint for scenario comparison data."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)

    # Check if user has access to this evaluee
    if evaluee.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    try:
        # Prepare evaluee data
        evaluee_data = {
            'first_name': evaluee.first_name,
            'last_name': evaluee.last_name,
            'date_of_birth': evaluee.date_of_birth,
            'date_of_injury': evaluee.date_of_injury,
            'base_earnings': evaluee.base_earnings or 0,
            'education_level': evaluee.education_level,
            'gender': evaluee.gender,
            'work_life_expectancy': evaluee.work_life_expectancy,
        }
        
        # Get enhanced calculator and run multi-scenario analysis
        calculator = get_enhanced_calculator()
        scenario_results = calculator.calculate_multi_scenario_analysis(evaluee_data)
        
        # Format data for charts
        chart_data = {
            'scenarios': [],
            'losses': [],
            'parameters': {}
        }
        
        for scenario_name, scenario_data in scenario_results.get('scenarios', {}).items():
            chart_data['scenarios'].append(scenario_name.title())
            chart_data['losses'].append(scenario_data.get('total_loss', 0))
            chart_data['parameters'][scenario_name] = scenario_data.get('parameters', {})
        
        chart_data['summary'] = scenario_results.get('summary', {})
        chart_data['settlement'] = scenario_results.get('settlement_analysis', {})
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
        
    except Exception as e:
        logger.error(f"Error in scenario comparison API: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/reports/<int:evaluee_id>/wage-data')
@login_required
def api_wage_data(evaluee_id):
    """API endpoint for wage data lookup."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)

    # Check if user has access to this evaluee
    if evaluee.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    try:
        occupation = request.args.get('occupation', getattr(evaluee, 'occupation', 'General'))
        state = request.args.get('state', getattr(evaluee, 'state', 'National'))
        msa = request.args.get('msa', getattr(evaluee, 'msa', None))
        
        # Lookup wage data
        wage_data = lookup_occupation_wages(occupation, state, msa)
        
        return jsonify({
            'success': True,
            'wage_data': wage_data
        })
        
    except Exception as e:
        logger.error(f"Error in wage data API: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/reports/<int:evaluee_id>/word-document')
@login_required
def generate_word_document(evaluee_id):
    """Generate a professional Word document report."""
    try:
        evaluee = Evaluee.query.get_or_404(evaluee_id)
        
        # Check if user has access to this evaluee
        if evaluee.user_id != current_user.id:
            flash('You do not have access to this evaluee.', 'danger')
            return redirect(url_for('evaluee.index'))
        
        # Get report type from query parameter
        report_type = request.args.get('type', 'comprehensive')
        
        # Prepare evaluee data for the document generator
        evaluee_data = {
            'first_name': evaluee.first_name,
            'last_name': evaluee.last_name,
            'date_of_birth': evaluee.date_of_birth,
            'date_of_injury': evaluee.date_of_injury,
            'education_level': evaluee.education_level,
            'occupation': getattr(evaluee, 'occupation', 'Not specified'),
            'state': evaluee.state,
            'base_earnings': getattr(evaluee, 'base_earnings', 0),
            'life_expectancy': evaluee.life_expectancy,
            'work_life_expectancy': evaluee.work_life_expectancy,
            'years_to_final_separation': evaluee.years_to_final_separation,
            'injury_description': getattr(evaluee, 'injury_description', 'Injury details not provided.')
        }
        
        # Get actual earnings scenarios from database
        earnings_scenarios = []
        for scenario in evaluee.earnings_scenarios:
            scenario_data = {
                'scenario_name': scenario.scenario_name,
                'description': f'Economic analysis scenario spanning {scenario.start_date.strftime("%Y-%m-%d")} to {scenario.end_date.strftime("%Y-%m-%d")}',
                'start_date': scenario.start_date,
                'end_date': scenario.end_date,
                'wage_base': float(scenario.wage_base),
                'residual_wage': float(scenario.residual_base) if scenario.residual_base else 0,
                'growth_rate': float(scenario.growth_rate) if scenario.growth_rate else 0,
                'discount_rate': 0.03,  # Default discount rate
                'methodology': 'Present value analysis using established forensic economic principles',
                'assumptions': [
                    f'Pre-injury annual wage: ${float(scenario.wage_base):,.2f}',
                    f'Post-injury residual capacity: ${float(scenario.residual_base) if scenario.residual_base else 0:,.2f}',
                    f'Annual wage growth rate: {float(scenario.growth_rate)*100:.1f}%' if scenario.growth_rate else 'No growth assumed',
                    'Present value discounting applied to future losses',
                    'Work life expectancy based on actuarial data and individual circumstances'
                ],
                'present_value': float(scenario.present_value) if scenario.present_value else 0,
                'total_loss': float(scenario.total_loss) if scenario.total_loss else 0,
                # Pre/Post injury details if available
                'injury_date': scenario.injury_date,
                'pre_injury_wage': float(scenario.pre_injury_wage) if scenario.pre_injury_wage else None,
                'post_injury_wage': float(scenario.post_injury_wage) if scenario.post_injury_wage else None,
                'pre_injury_growth_rate': float(scenario.pre_injury_growth_rate) if scenario.pre_injury_growth_rate else None,
                'post_injury_growth_rate': float(scenario.post_injury_growth_rate) if scenario.post_injury_growth_rate else None,
                'pre_injury_present_value': float(scenario.pre_injury_present_value) if scenario.pre_injury_present_value else None,
                'post_injury_present_value': float(scenario.post_injury_present_value) if scenario.post_injury_present_value else None
            }
            earnings_scenarios.append(scenario_data)
        
        # Get comprehensive economic analysis
        try:
            calculator = get_enhanced_calculator()
            analysis_results = calculator.calculate_comprehensive_analysis(evaluee_data)
            # Add actual earnings scenarios to analysis results
            analysis_results['earnings_scenarios'] = earnings_scenarios
        except Exception as e:
            logger.warning(f"Could not generate comprehensive analysis: {str(e)}")
            # Create basic analysis structure if enhanced analysis fails
            analysis_results = {
                'multi_scenario_analysis': {
                    'scenarios': {
                        'conservative': {'total_loss': 0, 'parameters': {'wage_growth_rate': 0.02, 'discount_rate': 0.03}},
                        'moderate': {'total_loss': 0, 'parameters': {'wage_growth_rate': 0.03, 'discount_rate': 0.025}},
                        'aggressive': {'total_loss': 0, 'parameters': {'wage_growth_rate': 0.04, 'discount_rate': 0.02}}
                    },
                    'summary': {
                        'avg_loss': 0,
                        'min_loss': 0,
                        'max_loss': 0,
                        'range_spread': 0,
                        'coefficient_of_variation': 0
                    },
                    'settlement_analysis': {
                        'recommended_target': 0,
                        'confidence_level': 0.75,
                        'conservative_low': 0,
                        'conservative_high': 0,
                        'moderate_low': 0,
                        'moderate_high': 0,
                        'aggressive_low': 0,
                        'aggressive_high': 0
                    }
                },
                'career_trajectory': {
                    'current_stage': 'mid_career',
                    'age_at_injury': evaluee_data.get('date_of_injury', datetime.now()).year - evaluee_data.get('date_of_birth', datetime.now()).year if evaluee_data.get('date_of_birth') and evaluee_data.get('date_of_injury') else 35,
                    'education_factor': 1.0,
                    'industry_growth_rate': 0.025,
                    'peak_earning_age': 55,
                    'peak_earning_amount': evaluee_data.get('base_earnings', 0) * 1.5,
                    'lost_earning_potential': evaluee_data.get('base_earnings', 0) * 10
                },
                'wage_baseline_analysis': {
                    'market_analysis': {
                        'market_mean': evaluee_data.get('base_earnings', 0),
                        'market_median': evaluee_data.get('base_earnings', 0) * 0.9,
                        'earnings_percentile': 50,
                        'regional_adjustment': 1.0,
                        'growth_rate': 0.025
                    }
                },
                'earnings_scenarios': earnings_scenarios
            }
        
        # Generate the Word document
        generator = get_document_generator()
        doc_buffer = generator.create_comprehensive_report(evaluee_data, analysis_results, report_type)
        
        # Create filename based on evaluee name and report type
        filename = f"Economic_Analysis_{evaluee.first_name}_{evaluee.last_name}_{report_type}_{datetime.now().strftime('%Y%m%d')}.docx"
        
        return send_file(
            doc_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        logger.error(f"Error generating Word document: {str(e)}")
        flash(f'Error generating Word document: {str(e)}', 'danger')
        return redirect(url_for('evaluee.view', evaluee_id=evaluee_id))


@bp.route('/reports/<int:evaluee_id>/pdf')
@login_required
def generate_pdf_report(evaluee_id):
    """Generate comprehensive PDF report for an evaluee"""
    try:
        evaluee = Evaluee.query.get_or_404(evaluee_id)
        
        # Check if user has access to this evaluee
        if evaluee.user_id != current_user.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('evaluee.index'))
        
        # Generate PDF report
        generator = EconomicReportGenerator()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            output_path = tmp_file.name
        
        # Generate the report
        generator.generate_comprehensive_report(evaluee_id, output_path)
        
        # Create filename
        filename = f"Economic_Analysis_{evaluee.first_name}_{evaluee.last_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Send file and clean up
        def remove_file(response):
            try:
                os.remove(output_path)
            except Exception:
                pass
            return response
        
        response = send_file(
            output_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        response.call_on_close(lambda: remove_file(response))
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        flash(f'Error generating PDF report: {str(e)}', 'danger')
        return redirect(url_for('evaluee.view', evaluee_id=evaluee_id))


@bp.route('/reports/<int:evaluee_id>/scenarios/compare')
@login_required
def scenario_comparison_report(evaluee_id):
    """Generate PDF comparison report for multiple scenarios"""
    try:
        evaluee = Evaluee.query.get_or_404(evaluee_id)
        
        # Check if user has access to this evaluee
        if evaluee.user_id != current_user.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('evaluee.index'))
        
        # Get scenario IDs from query parameters
        scenario_ids = request.args.getlist('scenarios')
        if not scenario_ids:
            flash('Please select at least one scenario to compare.', 'warning')
            return redirect(url_for('evaluee.view', evaluee_id=evaluee_id))
        
        # Convert to integers
        scenario_ids = [int(sid) for sid in scenario_ids if sid.isdigit()]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            output_path = tmp_file.name
        
        # Generate comparison report
        generate_scenario_comparison_report(evaluee_id, scenario_ids, output_path)
        
        # Create filename
        filename = f"Scenario_Comparison_{evaluee.first_name}_{evaluee.last_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Send file and clean up
        def remove_file(response):
            try:
                os.remove(output_path)
            except Exception:
                pass
            return response
        
        response = send_file(
            output_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        response.call_on_close(lambda: remove_file(response))
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating scenario comparison report: {str(e)}")
        flash(f'Error generating comparison report: {str(e)}', 'danger')
        return redirect(url_for('evaluee.view', evaluee_id=evaluee_id))


@bp.route('/reports/<int:evaluee_id>/executive-summary')
@login_required  
def executive_summary_report(evaluee_id):
    """Generate executive summary PDF report"""
    try:
        evaluee = Evaluee.query.get_or_404(evaluee_id)
        
        # Check if user has access to this evaluee
        if evaluee.user_id != current_user.id:
            flash('Access denied.', 'danger')
            return redirect(url_for('evaluee.index'))
        
        # Generate executive summary (lighter version of full report)
        generator = EconomicReportGenerator()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            output_path = tmp_file.name
        
        # Create a simplified document for executive summary
        from reportlab.platypus import SimpleDocTemplate
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        
        # Add executive summary content only
        story.extend(generator._create_title_page(evaluee))
        story.extend(generator._create_executive_summary(evaluee))
        story.extend(generator._create_evaluee_overview(evaluee))
        
        # Build PDF
        doc.build(story)
        
        # Create filename
        filename = f"Executive_Summary_{evaluee.first_name}_{evaluee.last_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Send file and clean up
        def remove_file(response):
            try:
                os.remove(output_path)
            except Exception:
                pass
            return response
        
        response = send_file(
            output_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        response.call_on_close(lambda: remove_file(response))
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating executive summary: {str(e)}")
        flash(f'Error generating executive summary: {str(e)}', 'danger')
        return redirect(url_for('evaluee.view', evaluee_id=evaluee_id))
