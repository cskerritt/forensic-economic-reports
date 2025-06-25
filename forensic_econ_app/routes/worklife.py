from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models.models import db, Evaluee
from ..utils.calculations import calculate_worklife_factor
from ..utils.csv_lookups import lookup_wle_median, lookup_yfs_median, lookup_worklife_values
from decimal import Decimal

bp = Blueprint('worklife', __name__)

@bp.route('/worklife/<int:evaluee_id>', methods=['GET', 'POST'])
def form(evaluee_id):
    evaluee = Evaluee.query.get_or_404(evaluee_id)

    # Calculate age at injury if both date of birth and date of injury are set
    age_at_injury = None
    if evaluee.date_of_birth and evaluee.date_of_injury:
        age_at_injury = (evaluee.date_of_injury - evaluee.date_of_birth).days / 365.25

    # Look up values from tables
    wle_median = None
    yfs_median = None
    if age_at_injury:
        wle_median, yfs_median = lookup_worklife_values(
            evaluee.gender,
            evaluee.education_level,
            age_at_injury
        )

    if request.method == 'POST':
        # Check if manual override is enabled
        manual_override = 'manual_override' in request.form

        # Get values from form
        work_life_expectancy = float(request.form.get('work_life_expectancy'))
        years_to_final_separation = float(request.form.get('years_to_final_separation'))

        worklife_factor = calculate_worklife_factor(work_life_expectancy, years_to_final_separation)
        if worklife_factor:
            evaluee.work_life_expectancy = work_life_expectancy
            evaluee.years_to_final_separation = years_to_final_separation
            evaluee.worklife_factor = worklife_factor
            evaluee.worklife_manual_override = manual_override
            db.session.commit()

            if manual_override:
                flash('Worklife factor calculated successfully with manual override.')
            else:
                flash('Worklife factor calculated successfully.')
        else:
            flash('Error calculating worklife factor. Please check your inputs.')

        return redirect(url_for('evaluee.view', evaluee_id=evaluee_id))

    return render_template(
        'worklife/form.html',
        evaluee=evaluee,
        evaluee_id=evaluee_id,
        age_at_injury=age_at_injury,
        wle_median=wle_median,
        yfs_median=yfs_median
    )

@bp.route('/worklife/<int:evaluee_id>/lookup', methods=['POST'])
def lookup(evaluee_id):
    evaluee = Evaluee.query.get_or_404(evaluee_id)

    # Calculate age at injury
    if not evaluee.date_of_birth or not evaluee.date_of_injury:
        flash('Date of birth and date of injury must be set to use table lookup.')
        return redirect(url_for('worklife.form', evaluee_id=evaluee_id))

    age_at_injury = (evaluee.date_of_injury - evaluee.date_of_birth).days / 365.25

    # Look up values from tables
    wle_median, yfs_median = lookup_worklife_values(
        evaluee.gender,
        evaluee.education_level,
        age_at_injury
    )

    if wle_median is None or yfs_median is None:
        flash('Could not find values in the tables for the given demographics.')
        return redirect(url_for('worklife.form', evaluee_id=evaluee_id))

    # Calculate worklife factor
    worklife_factor = calculate_worklife_factor(wle_median, yfs_median)
    if worklife_factor:
        evaluee.work_life_expectancy = wle_median
        evaluee.years_to_final_separation = yfs_median
        evaluee.worklife_factor = worklife_factor
        evaluee.worklife_manual_override = False  # Set to False when using table values
        db.session.commit()
        flash(f'Worklife factor calculated successfully using table values: WLE={wle_median:.2f}, YFS={yfs_median:.2f}', 'success')

        # Redirect to evaluee view to show the updated values in the dashboard
        return redirect(url_for('evaluee.view', evaluee_id=evaluee_id))
    else:
        flash('Error calculating worklife factor from table values.', 'danger')

    return redirect(url_for('worklife.form', evaluee_id=evaluee_id))