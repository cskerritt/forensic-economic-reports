from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from ..models.models import db, Evaluee
from ..utils.expectancy_lookup import calculate_expectancies, get_expectancy_lookup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('demographics', __name__)

@bp.route('/demographics/<int:evaluee_id>', methods=['GET', 'POST'])
def form(evaluee_id):
    evaluee = Evaluee.query.get_or_404(evaluee_id)

    # Calculate age at injury and other time-based values
    age_at_injury = None
    age_today = None
    time_since_injury = None

    if evaluee.date_of_birth and evaluee.date_of_injury:
        age_at_injury = (evaluee.date_of_injury - evaluee.date_of_birth).days / 365.25
        age_today = (datetime.now() - evaluee.date_of_birth).days / 365.25
        time_since_injury = (datetime.now() - evaluee.date_of_injury).days / 365.25

    if request.method == 'POST':
        try:
            # Handle form submission with validation and error handling
            date_of_birth = request.form.get('date_of_birth')
            date_of_injury = request.form.get('date_of_injury')
            life_expectancy = request.form.get('life_expectancy')
            work_life_expectancy = request.form.get('work_life_expectancy')
            years_to_final_separation = request.form.get('years_to_final_separation')
            gender = request.form.get('gender')
            education_level = request.form.get('education_level')

            # Validate required fields
            if not date_of_birth or not date_of_injury:
                flash('Date of birth and date of injury are required.', 'danger')
                return redirect(url_for('demographics.form', evaluee_id=evaluee_id))
            
            if not gender or not education_level:
                flash('Gender and education level are required.', 'danger')
                return redirect(url_for('demographics.form', evaluee_id=evaluee_id))

            # Update evaluee with form data
            birth_date = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            injury_date = datetime.strptime(date_of_injury, '%Y-%m-%d').date()
            
            evaluee.date_of_birth = birth_date
            evaluee.date_of_injury = injury_date
            evaluee.gender = gender
            evaluee.education_level = education_level
            
            # Auto-calculate expectancies if not manually provided
            if life_expectancy and work_life_expectancy and years_to_final_separation:
                # Use manually entered values
                evaluee.life_expectancy = float(life_expectancy)
                evaluee.work_life_expectancy = float(work_life_expectancy)
                evaluee.years_to_final_separation = float(years_to_final_separation)
                flash('Demographics updated with manual expectancy values.', 'success')
            else:
                # Auto-calculate using the expectancy lookup tool
                try:
                    expectancies = calculate_expectancies(
                        birth_date, injury_date, gender, education_level
                    )
                    
                    if expectancies['life_expectancy']:
                        evaluee.life_expectancy = expectancies['life_expectancy']
                    if expectancies['work_life_expectancy']:
                        evaluee.work_life_expectancy = expectancies['work_life_expectancy']
                    if expectancies['years_to_final_separation']:
                        evaluee.years_to_final_separation = expectancies['years_to_final_separation']
                    
                    flash('Demographics updated with auto-calculated expectancy values.', 'success')
                except Exception as e:
                    logger.error(f"Error calculating expectancies: {str(e)}")
                    flash('Demographics updated, but expectancy calculations failed. Please enter values manually.', 'warning')

            db.session.commit()
            return redirect(url_for('evaluee.view', evaluee_id=evaluee_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating demographics: {str(e)}', 'danger')
            return redirect(url_for('demographics.form', evaluee_id=evaluee_id))

    # Get available options for dropdowns
    try:
        lookup = get_expectancy_lookup()
        options = lookup.get_available_options()
    except Exception as e:
        logger.error(f"Error getting expectancy options: {str(e)}")
        options = {}

    return render_template(
        'demographics/form.html',
        evaluee=evaluee,
        evaluee_id=evaluee_id,
        age_at_injury=age_at_injury,
        age_today=age_today,
        time_since_injury=time_since_injury,
        expectancy_options=options
    )

@bp.route('/api/calculate-expectancies', methods=['POST'])
def api_calculate_expectancies():
    """API endpoint to calculate expectancies based on demographics."""
    try:
        data = request.get_json()
        
        # Parse dates
        birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        injury_date = datetime.strptime(data['injury_date'], '%Y-%m-%d').date()
        
        # Calculate expectancies
        expectancies = calculate_expectancies(
            birth_date, 
            injury_date, 
            data['gender'], 
            data['education_level'],
            data.get('race', 'General Population')
        )
        
        return jsonify({
            'success': True,
            'expectancies': expectancies
        })
        
    except Exception as e:
        logger.error(f"Error in API calculate expectancies: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

