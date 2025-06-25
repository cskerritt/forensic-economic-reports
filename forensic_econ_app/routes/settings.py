from flask import Blueprint, render_template, redirect, url_for, flash, request
from forensic_econ_app.models.models import db, CPIRate, MedicalCareCategory
from decimal import Decimal

settings = Blueprint('settings', __name__)

@settings.route('/settings/cpi-rates')
def manage_cpi_rates():
    """Manage universal CPI rates."""
    rates = CPIRate.query.all()
    return render_template('settings/cpi_rates.html', rates=rates)

@settings.route('/settings/cpi-rates/update', methods=['POST'])
def update_cpi_rates():
    """Update CPI rates."""
    try:
        for category in ['CPI', 'PCE', 'Medical_CPI']:
            rate_value = Decimal(request.form.get(f'{category}_rate', '0')) / 100
            rate = CPIRate.query.filter_by(category=category).first()
            
            if rate:
                rate.rate = rate_value
            else:
                rate = CPIRate(
                    category=category,
                    rate=rate_value,
                    description=request.form.get(f'{category}_description', '')
                )
                db.session.add(rate)
        
        db.session.commit()
        flash('CPI rates updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating CPI rates: {str(e)}', 'error')
    
    return redirect(url_for('settings.manage_cpi_rates'))

@settings.route('/settings/medical-categories')
def manage_medical_categories():
    """Manage medical care categories and associated growth rates."""
    categories = MedicalCareCategory.query.order_by(MedicalCareCategory.lcp_category).all()
    return render_template('settings/medical_categories.html', categories=categories)

@settings.route('/settings/medical-categories/update', methods=['POST'])
def update_medical_categories():
    """Update medical care categories."""
    try:
        # Get all category IDs from the form
        category_ids = request.form.getlist('category_id')
        
        for cat_id in category_ids:
            category = MedicalCareCategory.query.get(cat_id)
            if category:
                # Convert percentage to decimal for storage
                growth_rate_str = request.form.get(f'growth_rate_{cat_id}')
                growth_rate = Decimal(growth_rate_str) / 100 if growth_rate_str else None
                
                # Update category fields
                category.growth_rate = growth_rate
                category.description = request.form.get(f'description_{cat_id}', '')
        
        db.session.commit()
        flash('Medical care categories updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating medical care categories: {str(e)}', 'error')
    
    return redirect(url_for('settings.manage_medical_categories')) 