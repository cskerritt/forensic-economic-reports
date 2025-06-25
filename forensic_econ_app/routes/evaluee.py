from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, jsonify
)
from flask_login import login_required, current_user
from ..models.models import db, Evaluee
from datetime import timedelta, datetime
from sqlalchemy import desc
from ..utils.us_states import get_state_adjustment, validate_state
from ..utils.auto_population import calculate_age_from_dob, calculate_retirement_date

bp = Blueprint('evaluee', __name__)

@bp.route('/')
@login_required
def index():
    """List all evaluees."""
    evaluees = Evaluee.query.filter_by(user_id=current_user.id).order_by(Evaluee.created_at.desc()).all()

    # Calculate completion percentage for each evaluee
    for evaluee in evaluees:
        completion_percentage = 0
        total_fields = 0
        completed_fields = 0

        # Check demographics
        if evaluee.date_of_birth:
            completed_fields += 1
        if evaluee.date_of_injury:
            completed_fields += 1
        if evaluee.gender:
            completed_fields += 1
        if evaluee.education_level:
            completed_fields += 1
        total_fields += 4

        # Check worklife
        if evaluee.work_life_expectancy:
            completed_fields += 1
        if evaluee.years_to_final_separation:
            completed_fields += 1
        total_fields += 2

        # Check earnings
        if hasattr(evaluee, 'base_earnings') and evaluee.base_earnings:
            completed_fields += 1
        total_fields += 1

        # Calculate percentage
        if total_fields > 0:
            completion_percentage = int((completed_fields / total_fields) * 100)

        evaluee.completion_percentage = completion_percentage

    return render_template('evaluee/index.html', evaluees=evaluees)

@bp.route('/dashboard')
@login_required
def dashboard():
    """Show the user dashboard with statistics and recent evaluees."""
    # Get all evaluees for the current user
    evaluees = Evaluee.query.filter_by(user_id=current_user.id).order_by(desc(Evaluee.created_at)).all()

    # Get recent evaluees (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_evaluees = Evaluee.query.filter_by(user_id=current_user.id).filter(
        Evaluee.created_at >= thirty_days_ago
    ).order_by(desc(Evaluee.created_at)).all()

    # Calculate completion percentage for each evaluee
    for evaluee in evaluees:
        completion_percentage = 0
        total_fields = 0
        completed_fields = 0

        # Check demographics
        if evaluee.date_of_birth:
            completed_fields += 1
        if evaluee.date_of_injury:
            completed_fields += 1
        if evaluee.gender:
            completed_fields += 1
        if evaluee.education_level:
            completed_fields += 1
        total_fields += 4

        # Check worklife
        if evaluee.work_life_expectancy:
            completed_fields += 1
        if evaluee.years_to_final_separation:
            completed_fields += 1
        total_fields += 2

        # Check earnings
        if hasattr(evaluee, 'base_earnings') and evaluee.base_earnings:
            completed_fields += 1
        total_fields += 1

        # Calculate percentage
        if total_fields > 0:
            completion_percentage = int((completed_fields / total_fields) * 100)

        evaluee.completion_percentage = completion_percentage

    # Separate completed and in-progress evaluees
    completed_evaluees = [e for e in evaluees if e.completion_percentage == 100]
    in_progress_evaluees = [e for e in evaluees if e.completion_percentage < 100]

    # Mock activity data (in a real app, this would come from a database table)
    activities = [
        {
            'action': 'Created Evaluee',
            'description': f"{evaluee.first_name} {evaluee.last_name}",
            'timestamp': evaluee.created_at
        } for evaluee in recent_evaluees[:5]
    ]

    # Get scenario counts for charts
    earnings_scenarios = sum(len(e.earnings_scenarios) for e in evaluees if hasattr(e, 'earnings_scenarios'))

    # Handle healthcare_scenarios safely
    try:
        healthcare_scenarios = sum(len(e.healthcare_scenarios) for e in evaluees if hasattr(e, 'healthcare_scenarios'))
    except Exception:
        healthcare_scenarios = 0

    # Handle household_services_scenarios safely
    try:
        household_scenarios = sum(len(e.household_services_scenarios) for e in evaluees if hasattr(e, 'household_services_scenarios'))
    except Exception:
        household_scenarios = 0

    # Handle fringe_benefit_scenarios safely
    try:
        fringe_benefit_scenarios = sum(len(e.fringe_benefit_scenarios) for e in evaluees if hasattr(e, 'fringe_benefit_scenarios'))
    except Exception:
        fringe_benefit_scenarios = 0

    # Generate activity data for the activity chart
    activity_dates = []
    activity_counts = []

    # Get activity for the last 7 days
    for i in range(7, 0, -1):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime('%m/%d')
        activity_dates.append(date_str)

        # Count evaluees created on this date
        count = sum(1 for e in evaluees if e.created_at.date() == date.date())
        activity_counts.append(count)

    return render_template(
        'evaluee/dashboard.html',
        evaluees=evaluees,
        recent_evaluees=recent_evaluees,
        completed_evaluees=completed_evaluees,
        in_progress_evaluees=in_progress_evaluees,
        activities=activities,
        # Chart data
        earnings_scenarios=earnings_scenarios,
        healthcare_scenarios=healthcare_scenarios,
        household_scenarios=household_scenarios,
        fringe_benefit_scenarios=fringe_benefit_scenarios,
        activity_dates=','.join(activity_dates),
        activity_counts=','.join(map(str, activity_counts))
    )

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new evaluee."""
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        state = request.form.get('state', '').strip()
        uses_discounting = 'discounting' in request.form

        if not all([first_name, last_name, state]):
            flash('All fields are required.')
            return redirect(url_for('evaluee.create'))

        # Parse discount rates
        try:
            if uses_discounting:
                rates_str = request.form.get('discount_rates', '3,5,7')
                discount_rates = [float(x.strip()) for x in rates_str.split(',') if x.strip()]
            else:
                discount_rates = [0.0]
        except ValueError:
            flash('Invalid discount rates format. Use comma-separated numbers.')
            return redirect(url_for('evaluee.create'))

        # Get demographic fields
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        current_age = request.form.get('current_age')
        regional_adjustment = request.form.get('regional_adjustment')
        
        # Get pediatric case fields
        is_pediatric_case = 'is_pediatric_case' in request.form
        calculate_hs_diploma = 'calculate_hs_diploma' in request.form
        calculate_some_college = 'calculate_some_college' in request.form
        calculate_associates = 'calculate_associates' in request.form
        calculate_bachelors = 'calculate_bachelors' in request.form
        parent1_education = request.form.get('parent1_education', 'Unknown')
        parent2_education = request.form.get('parent2_education', 'Unknown')
        
        # Validate and auto-populate fields
        validated_state = validate_state(state)
        if not validated_state:
            flash(f'Invalid state: {state}. Please select a valid state.')
            return redirect(url_for('evaluee.create'))
        
        # Auto-calculate demographic fields
        calculated_age = None
        retirement_date = None
        if date_of_birth:
            try:
                dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
                calculated_age = calculate_age_from_dob(dob)
                retirement_date = datetime.strptime(calculate_retirement_date(dob), '%Y-%m-%d')
            except ValueError as e:
                flash(f'Invalid date of birth format. Please select a valid date.')
                return redirect(url_for('evaluee.create'))
        
        # Get regional adjustment for state
        state_adjustment = get_state_adjustment(validated_state)

        evaluee = Evaluee(
            user_id=current_user.id,
            first_name=first_name,
            last_name=last_name,
            state=validated_state,
            uses_discounting=uses_discounting,
            discount_rates=discount_rates,
            date_of_birth=dob if date_of_birth else None,
            gender=gender if gender else 'M',
            current_age=calculated_age,
            regional_adjustment=state_adjustment,
            retirement_date=retirement_date,
            is_pediatric_case=is_pediatric_case,
            calculate_hs_diploma=calculate_hs_diploma,
            calculate_some_college=calculate_some_college,
            calculate_associates=calculate_associates,
            calculate_bachelors=calculate_bachelors,
            parent1_education=parent1_education,
            parent2_education=parent2_education if is_pediatric_case else 'N/A'
        )

        try:
            db.session.add(evaluee)
            db.session.commit()
            flash('Evaluee created successfully.')
            return redirect(url_for('evaluee.view', evaluee_id=evaluee.id))
        except Exception as e:
            current_app.logger.error(f'Error creating evaluee: {str(e)}')
            db.session.rollback()
            flash('An error occurred while creating the evaluee.')
            return redirect(url_for('evaluee.create'))

    return render_template('evaluee/create.html')

@bp.route('/<int:evaluee_id>')
@login_required
def view(evaluee_id):
    """View evaluee details."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)
    if evaluee.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('evaluee.index'))

    # Calculate age today and age at injury in decimal format
    age_today_decimal = None
    age_at_injury_decimal = None

    if evaluee.date_of_birth:
        # Calculate age today in decimal
        today = datetime.now()
        birth_date = evaluee.date_of_birth
        age_years = today.year - birth_date.year

        # Adjust for month and day
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age_years -= 1

        # Calculate the decimal part
        if birth_date.month == 2 and birth_date.day == 29:  # Handle leap year birthdays
            birth_date_this_year = birth_date.replace(year=today.year if not (today.month, today.day) < (birth_date.month, birth_date.day) else today.year - 1, day=28)
        else:
            birth_date_this_year = birth_date.replace(year=today.year if not (today.month, today.day) < (birth_date.month, birth_date.day) else today.year - 1)

        days_since_last_birthday = (today - birth_date_this_year).days
        days_in_year = 366 if (birth_date_this_year.year % 4 == 0 and birth_date_this_year.year % 100 != 0) or birth_date_this_year.year % 400 == 0 else 365
        decimal_part = days_since_last_birthday / days_in_year

        age_today_decimal = age_years + decimal_part

        # Calculate age at injury if date of injury is available
        if evaluee.date_of_injury:
            injury_date = evaluee.date_of_injury
            age_at_injury_years = injury_date.year - birth_date.year

            # Adjust for month and day
            if (injury_date.month, injury_date.day) < (birth_date.month, birth_date.day):
                age_at_injury_years -= 1

            # Calculate the decimal part
            if birth_date.month == 2 and birth_date.day == 29:  # Handle leap year birthdays
                birth_date_injury_year = birth_date.replace(year=injury_date.year if not (injury_date.month, injury_date.day) < (birth_date.month, birth_date.day) else injury_date.year - 1, day=28)
            else:
                birth_date_injury_year = birth_date.replace(year=injury_date.year if not (injury_date.month, injury_date.day) < (birth_date.month, birth_date.day) else injury_date.year - 1)

            days_since_injury_birthday = (injury_date - birth_date_injury_year).days
            injury_days_in_year = 366 if (birth_date_injury_year.year % 4 == 0 and birth_date_injury_year.year % 100 != 0) or birth_date_injury_year.year % 400 == 0 else 365
            injury_decimal_part = days_since_injury_birthday / injury_days_in_year

            age_at_injury_decimal = age_at_injury_years + injury_decimal_part

    return render_template('evaluee/view.html', evaluee=evaluee, timedelta=timedelta,
                          age_today_decimal=age_today_decimal, age_at_injury_decimal=age_at_injury_decimal,
                          datetime=datetime)



@bp.route('/<int:evaluee_id>/wizard')
@login_required
def wizard(evaluee_id):
    """Show the step-by-step wizard for completing an evaluee's information."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)
    if evaluee.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('evaluee.index'))

    return render_template('evaluee/wizard.html', evaluee=evaluee)

@bp.route('/<int:evaluee_id>/complete-wizard', methods=['POST'])
@login_required
def complete_wizard(evaluee_id):
    """Process the completed wizard form."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)
    if evaluee.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('evaluee.index'))

    # Process form data from all wizard steps
    if request.method == 'POST':
        try:
            # Demographics
            if 'date_of_birth' in request.form and request.form['date_of_birth']:
                evaluee.date_of_birth = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d')

            if 'date_of_injury' in request.form and request.form['date_of_injury']:
                evaluee.date_of_injury = datetime.strptime(request.form['date_of_injury'], '%Y-%m-%d')

            if 'gender' in request.form:
                evaluee.gender = request.form['gender']

            if 'education_level' in request.form:
                evaluee.education_level = request.form['education_level']

            if 'life_expectancy' in request.form and request.form['life_expectancy']:
                evaluee.life_expectancy = float(request.form['life_expectancy'])

            # Worklife
            if 'work_life_expectancy' in request.form and request.form['work_life_expectancy']:
                evaluee.work_life_expectancy = float(request.form['work_life_expectancy'])

            if 'years_to_final_separation' in request.form and request.form['years_to_final_separation']:
                evaluee.years_to_final_separation = float(request.form['years_to_final_separation'])

            evaluee.worklife_manual_override = 'worklife_manual_override' in request.form

            # Save changes
            db.session.commit()
            flash('Evaluation completed successfully!')
            return redirect(url_for('evaluee.view', evaluee_id=evaluee.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error completing wizard: {str(e)}')
            flash(f'An error occurred: {str(e)}')
            return redirect(url_for('evaluee.wizard', evaluee_id=evaluee.id))

    return redirect(url_for('evaluee.wizard', evaluee_id=evaluee.id))

@bp.route('/api/evaluee/<int:evaluee_id>/autosave', methods=['POST'])
@login_required
def autosave(evaluee_id):
    """Autosave evaluee data during wizard completion."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)
    if evaluee.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Access denied'})

    try:
        data = request.json
        step = data.get('step')
        form_data = data.get('data', {})

        # Process data based on the current step
        if step == 0:  # Demographics
            if 'date_of_birth' in form_data and form_data['date_of_birth']:
                evaluee.date_of_birth = datetime.strptime(form_data['date_of_birth'], '%Y-%m-%d')

            if 'date_of_injury' in form_data and form_data['date_of_injury']:
                evaluee.date_of_injury = datetime.strptime(form_data['date_of_injury'], '%Y-%m-%d')

            if 'gender' in form_data:
                evaluee.gender = form_data['gender']

            if 'education_level' in form_data:
                evaluee.education_level = form_data['education_level']

            if 'life_expectancy' in form_data and form_data['life_expectancy']:
                evaluee.life_expectancy = float(form_data['life_expectancy'])

        elif step == 1:  # Worklife
            if 'work_life_expectancy' in form_data and form_data['work_life_expectancy']:
                evaluee.work_life_expectancy = float(form_data['work_life_expectancy'])

            if 'years_to_final_separation' in form_data and form_data['years_to_final_separation']:
                evaluee.years_to_final_separation = float(form_data['years_to_final_separation'])

            evaluee.worklife_manual_override = form_data.get('worklife_manual_override', False)

        # Add more steps as needed

        db.session.commit()
        return jsonify({'success': True, 'message': 'Data saved successfully'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error autosaving data: {str(e)}')
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/edit/<int:evaluee_id>', methods=['GET', 'POST'])
@login_required
def edit(evaluee_id):
    evaluee = Evaluee.query.get_or_404(evaluee_id)

    # Ensure user owns this evaluee
    if evaluee.user_id != current_user.id:
        flash("You don't have permission to edit this evaluee.", "danger")
        return redirect(url_for('evaluee.index'))

    if request.method == 'POST':
        # Update evaluee data from form
        evaluee.first_name = request.form['first_name']
        evaluee.last_name = request.form['last_name']
        evaluee.state = request.form['state']

        evaluee.uses_discounting = 'discounting' in request.form

        if evaluee.uses_discounting and request.form['discount_rates']:
            # Parse discount rates from comma-separated string
            rates_str = request.form['discount_rates']
            try:
                # Remove spaces and split by comma
                rates = [float(r.strip()) for r in rates_str.split(',') if r.strip()]
                evaluee.discount_rates = rates
            except ValueError:
                flash('Invalid format for discount rates. Please use comma-separated numbers.', 'danger')
                return render_template('evaluee/edit.html', evaluee=evaluee)
        else:
            evaluee.discount_rates = []

        # Handle pediatric case fields
        evaluee.is_pediatric_case = 'is_pediatric_case' in request.form

        if evaluee.is_pediatric_case:
            evaluee.calculate_hs_diploma = 'calculate_hs_diploma' in request.form
            evaluee.calculate_some_college = 'calculate_some_college' in request.form
            evaluee.calculate_associates = 'calculate_associates' in request.form
            evaluee.calculate_bachelors = 'calculate_bachelors' in request.form
            evaluee.parent1_education = request.form.get('parent1_education', 'Unknown')
            evaluee.parent2_education = request.form.get('parent2_education', 'Unknown')
        else:
            # Reset pediatric fields if not a pediatric case
            evaluee.calculate_hs_diploma = False
            evaluee.calculate_some_college = False
            evaluee.calculate_associates = False
            evaluee.calculate_bachelors = False
            evaluee.parent1_education = None
            evaluee.parent2_education = 'N/A'

        try:
            db.session.commit()
            flash(f"Evaluee '{evaluee.first_name} {evaluee.last_name}' updated successfully.", "success")
            return redirect(url_for('evaluee.view', evaluee_id=evaluee.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating evaluee: {str(e)}", "danger")

    return render_template('evaluee/edit.html', evaluee=evaluee)

@bp.route('/<int:evaluee_id>/delete', methods=['POST'])
@login_required
def delete(evaluee_id):
    """Delete an evaluee."""
    evaluee = Evaluee.query.get_or_404(evaluee_id)
    if evaluee.user_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('evaluee.index'))

    try:
        db.session.delete(evaluee)
        db.session.commit()
        flash('Evaluee deleted successfully.')
    except Exception as e:
        current_app.logger.error(f'Error deleting evaluee: {str(e)}')
        db.session.rollback()
        flash('An error occurred while deleting the evaluee.')

    return redirect(url_for('evaluee.index'))