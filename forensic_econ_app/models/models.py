from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json
import numpy as np
from decimal import Decimal
from typing import List, Dict, Optional, Tuple, Any
import math
import logging
from sqlalchemy import JSON
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy with custom session options
db = SQLAlchemy(session_options={
    'expire_on_commit': False,
    'autoflush': False
})

class User(UserMixin, db.Model):
    """Model for user accounts."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)

    # Relationship with evaluees
    evaluees = db.relationship('Evaluee', backref='user', lazy=True)

    def set_password(self, password):
        """Set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Evaluee(db.Model):
    """Model for storing evaluee information."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    uses_discounting = db.Column(db.Boolean, default=True)
    _discount_rates = db.Column('discount_rates', db.Text, default='[3.0, 5.0, 7.0]')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Demographics data
    date_of_birth = db.Column(db.DateTime)
    date_of_injury = db.Column(db.DateTime)
    life_expectancy = db.Column(db.Numeric(10, 2))
    work_life_expectancy = db.Column(db.Numeric(10, 2))
    years_to_final_separation = db.Column(db.Numeric(10, 2))
    gender = db.Column(db.String(50), default='Men')  # 'Men' or 'Women'
    education_level = db.Column(db.String(100), default='All Education Levels')
    worklife_manual_override = db.Column(db.Boolean, default=False)  # Flag to indicate manual override

    # Worklife factor data
    worklife_factor = db.Column(db.Numeric(10, 4))

    # AEF data
    gross_earnings_base = db.Column(db.Numeric(10, 2))
    worklife_adjustment = db.Column(db.Numeric(10, 4))
    unemployment_factor = db.Column(db.Numeric(10, 4))
    fringe_benefit = db.Column(db.Numeric(10, 4))
    tax_liability = db.Column(db.Numeric(10, 4))
    wrongful_death = db.Column(db.Boolean, default=False)
    personal_type = db.Column(db.String(50))
    personal_percentage = db.Column(db.Numeric(10, 4))

    # New fields for pediatric cases
    is_pediatric_case = db.Column(db.Boolean, default=False,
        info={'label': 'Pediatric Case'})

    # Educational scenario flags (for pediatric cases)
    calculate_hs_diploma = db.Column(db.Boolean, default=True,
        info={'label': 'High School Diploma Scenario'})
    calculate_some_college = db.Column(db.Boolean, default=True,
        info={'label': 'Some College Scenario'})
    calculate_associates = db.Column(db.Boolean, default=True,
        info={'label': 'Associate\'s Degree Scenario'})
    calculate_bachelors = db.Column(db.Boolean, default=True,
        info={'label': 'Bachelor\'s Degree Scenario'})

    # Parental information (for pediatric cases)
    parent1_education = db.Column(db.String(100), default='N/A')
    parent2_education = db.Column(db.String(100), default='N/A')
    
    # Automation fields
    regional_adjustment = db.Column(db.Numeric(5, 3), default=1.000)  # Regional wage multiplier
    current_age = db.Column(db.Integer)  # Auto-calculated from date_of_birth
    retirement_date = db.Column(db.DateTime)  # Auto-calculated retirement date

    # Relationships
    earnings_scenarios = db.relationship('EarningsScenario', backref='evaluee', lazy=True)

    @property
    def discount_rates(self):
        return json.loads(self._discount_rates)

    @discount_rates.setter
    def discount_rates(self, value):
        self._discount_rates = json.dumps(value)

class EarningsScenario(db.Model):
    """Model for storing earnings calculation scenarios."""
    id = db.Column(db.Integer, primary_key=True)
    evaluee_id = db.Column(db.Integer, db.ForeignKey('evaluee.id'), nullable=False)
    scenario_name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    wage_base = db.Column(db.Numeric(10, 2), nullable=False)
    residual_base = db.Column(db.Numeric(10, 2))
    growth_rate = db.Column(db.Numeric(10, 4))
    adjustment_factor = db.Column(db.Numeric(10, 4))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Store calculation results
    present_value = db.Column(db.Numeric(15, 2))
    total_loss = db.Column(db.Numeric(15, 2))
    
    # Pre- and Post-injury period support
    injury_date = db.Column(db.DateTime)  # Date when injury occurred
    report_date = db.Column(db.DateTime)  # Date of economic analysis/report
    pre_injury_wage = db.Column(db.Numeric(10, 2))  # Pre-injury wage rate
    post_injury_wage = db.Column(db.Numeric(10, 2))  # Post-injury wage rate (residual earning capacity)
    pre_injury_growth_rate = db.Column(db.Numeric(10, 4))  # Growth rate for pre-injury period
    post_injury_growth_rate = db.Column(db.Numeric(10, 4))  # Growth rate for post-injury period
    
    # Calculation results by period
    pre_injury_present_value = db.Column(db.Numeric(15, 2))  # Pre-injury earnings
    past_loss_present_value = db.Column(db.Numeric(15, 2))   # Past losses (injury to report date)
    future_loss_present_value = db.Column(db.Numeric(15, 2)) # Future losses (report date forward)
    pre_injury_total_loss = db.Column(db.Numeric(15, 2))
    post_injury_total_loss = db.Column(db.Numeric(15, 2))

    # Seasonal Employment Support
    is_seasonal = db.Column(db.Boolean, default=False)
    season_start_month = db.Column(db.Integer)  # 1-12 for Jan-Dec
    season_end_month = db.Column(db.Integer)  # 1-12 for Jan-Dec
    off_season_income_factor = db.Column(db.Numeric(5, 4))  # Percentage of regular income during off-season

    # Education Impact Analysis
    education_level = db.Column(db.String(50))  # high_school, associate, bachelor, master, doctorate
    education_impact_factor = db.Column(db.Numeric(5, 4))  # Percentage increase due to education
    education_completion_year = db.Column(db.Integer)  # Year when education is completed

    # Add relationship to offset wages
    offset_wages = db.relationship('OffsetWage', backref='scenario', lazy=True, cascade='all, delete-orphan')

    # Add relationship to career progression events
    career_progressions = db.relationship('CareerProgression', backref='scenario', lazy=True, cascade='all, delete-orphan')

    def calculate_education_impact(self, base_wage: Decimal, year: int) -> Decimal:
        """Calculate the impact of education on earnings for a given year."""
        if not self.education_level or not self.education_impact_factor or not self.education_completion_year:
            return base_wage

        if year >= self.education_completion_year:
            # Apply education impact after completion
            return base_wage * (1 + Decimal(str(self.education_impact_factor)))

        return base_wage
    
    def calculate_pre_post_injury_values(self, discount_rate: float = 0.03):
        """Calculate separate present values for pre-injury, past loss, and future loss periods."""
        if not self.injury_date or not self.report_date:
            # If critical dates are missing, use traditional calculation
            return
        
        # Ensure dates are in proper order
        if self.injury_date > self.report_date:
            raise ValueError("Injury date cannot be after report date")
        
        # Period 1: Pre-injury earnings (start_date to injury_date)
        if self.start_date <= self.injury_date:
            pre_injury_end = min(self.injury_date, self.end_date)
            self.pre_injury_present_value, self.pre_injury_total_loss = self._calculate_period_values(
                self.start_date, 
                pre_injury_end,
                self.pre_injury_wage or self.wage_base,
                self.pre_injury_growth_rate or self.growth_rate or 0,
                discount_rate,
                is_past_period=True
            )
        
        # Period 2: Past losses (injury_date to report_date)
        if self.injury_date < self.report_date:
            past_loss_per_year = (self.pre_injury_wage or self.wage_base) - (self.post_injury_wage or 0)
            
            self.past_loss_present_value, _ = self._calculate_period_values(
                self.injury_date,
                self.report_date,
                past_loss_per_year,
                self.post_injury_growth_rate or self.growth_rate or 0,
                discount_rate,
                is_past_period=True
            )
        
        # Period 3: Future losses (report_date to end_date)
        if self.report_date < self.end_date:
            future_loss_per_year = (self.pre_injury_wage or self.wage_base) - (self.post_injury_wage or 0)
            
            self.future_loss_present_value, self.post_injury_total_loss = self._calculate_period_values(
                self.report_date,
                self.end_date,
                future_loss_per_year,
                self.post_injury_growth_rate or self.growth_rate or 0,
                discount_rate,
                is_past_period=False
            )
        
        # Update total values (past losses + future losses)
        past_total = (self.past_loss_present_value or 0)
        future_total = (self.future_loss_present_value or 0)
        self.present_value = past_total + future_total
        self.total_loss = past_total + future_total
    
    def _calculate_period_values(self, start_date, end_date, annual_amount, growth_rate, discount_rate, is_past_period=False):
        """Calculate present value and total loss for a specific period."""
        from decimal import Decimal
        from datetime import datetime
        
        if start_date >= end_date or annual_amount <= 0:
            return Decimal('0'), Decimal('0')
        
        total_loss = Decimal('0')
        present_value = Decimal('0')
        current_date = start_date
        base_amount = Decimal(str(annual_amount))
        growth_rate_decimal = Decimal(str(growth_rate))
        discount_rate_decimal = Decimal(str(discount_rate))
        
        # Calculate year by year
        year = 0
        while current_date < end_date:
            # Calculate the portion of the year covered
            year_end = min(
                datetime(current_date.year + 1, 1, 1),
                end_date
            )
            days_in_period = (year_end - current_date).days
            days_in_year = 366 if current_date.year % 4 == 0 else 365
            year_fraction = Decimal(str(days_in_period / days_in_year))
            
            # Calculate wage for this year with growth
            annual_wage = base_amount * ((1 + growth_rate_decimal) ** year)
            period_amount = annual_wage * year_fraction
            
            # Add to total loss
            total_loss += period_amount
            
            # Calculate present value
            if is_past_period:
                # For past periods, compound forward to injury date then discount back to today
                years_from_injury = (datetime.now() - current_date).days / 365.25
                pv_amount = period_amount * ((1 + discount_rate_decimal) ** Decimal(str(years_from_injury)))
            else:
                # For future periods, discount back to today
                years_to_discount = (current_date - datetime.now()).days / 365.25
                pv_amount = period_amount / ((1 + discount_rate_decimal) ** Decimal(str(years_to_discount)))
            
            present_value += pv_amount
            
            # Move to next year
            current_date = year_end
            year += 1
        
        return present_value, total_loss

    def calculate_seasonal_adjustment(self, annual_wage: Decimal, month: int) -> Decimal:
        """Calculate seasonal adjustment for a given month."""
        if not self.is_seasonal or not self.season_start_month or not self.season_end_month:
            return annual_wage / 12  # Regular monthly income

        # Check if current month is in season
        in_season = False
        if self.season_start_month <= self.season_end_month:
            # Normal season (e.g., April to October)
            in_season = self.season_start_month <= month <= self.season_end_month
        else:
            # Season spans year boundary (e.g., November to March)
            in_season = month >= self.season_start_month or month <= self.season_end_month

        if in_season:
            # Calculate in-season monthly income
            in_season_months = self._count_season_months()
            off_season_months = 12 - in_season_months
            off_season_factor = Decimal(str(self.off_season_income_factor or '0'))

            # Adjust for total annual income to match base wage
            total_off_season_portion = off_season_months * off_season_factor
            total_in_season_portion = in_season_months
            total_portions = total_in_season_portion + total_off_season_portion

            in_season_monthly = (annual_wage / total_portions) * (12 / in_season_months)
            return in_season_monthly
        else:
            # Off-season income
            off_season_factor = Decimal(str(self.off_season_income_factor or '0'))
            in_season_monthly = self.calculate_seasonal_adjustment(annual_wage, self.season_start_month)
            return in_season_monthly * off_season_factor

    def _count_season_months(self) -> int:
        """Count the number of months in the season."""
        if not self.season_start_month or not self.season_end_month:
            return 12

        if self.season_start_month <= self.season_end_month:
            # Normal season (e.g., April to October)
            return self.season_end_month - self.season_start_month + 1
        else:
            # Season spans year boundary (e.g., November to March)
            return (12 - self.season_start_month + 1) + self.season_end_month

class OffsetWage(db.Model):
    """Model for storing offset wages for specific years in a scenario."""
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('earnings_scenario.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HealthcareScenario(db.Model):
    """Model for storing healthcare expense scenarios."""
    id = db.Column(db.Integer, primary_key=True)
    evaluee_id = db.Column(db.Integer, db.ForeignKey('evaluee.id'), nullable=False)
    scenario_name = db.Column(db.String(100), nullable=False)
    growth_method = db.Column(db.String(20), default='CPI')  # CPI, PCE, or custom
    growth_rate_custom = db.Column(db.Numeric(10, 4))
    discount_method = db.Column(db.String(20), default='nominal')  # nominal, real, or net
    discount_rate = db.Column(db.Numeric(10, 4))
    partial_offset = db.Column(db.Boolean, default=False)
    total_offset = db.Column(db.Boolean, default=False)
    projection_years = db.Column(db.Numeric(10, 2), default=20)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Advanced Medical Inflation Modeling
    inflation_model = db.Column(db.String(50), default='linear')  # linear, dual_rate, or custom
    inflation_transition_year = db.Column(db.Integer)  # Year to transition to long-term rate
    inflation_long_term_rate = db.Column(db.Numeric(5, 4))  # Long-term inflation rate

    # Relationships
    evaluee = db.relationship('Evaluee', backref='healthcare_scenarios', lazy=True)

    def compute_future_medical_costs(self, base_year: int, projection_years: int, inflation_rate: Decimal) -> List[Decimal]:
        """
        Compute future medical costs for each year in the projection period.

        Args:
            base_year: The starting year for calculations (e.g., 2023)
            projection_years: Number of years to project into the future
            inflation_rate: Annual inflation rate as a decimal (e.g., 0.03 for 3%)

        Returns:
            List of projected costs for each year
        """
        # Return empty list as medical items have been removed
        return [Decimal('0')] * projection_years

    def _calculate_inflation_factor(self, year_index: int, base_inflation_rate: Decimal) -> Decimal:
        """
        Calculate inflation factor based on the selected inflation model.

        Args:
            year_index: Year index (0-based)
            base_inflation_rate: Base inflation rate

        Returns:
            Inflation factor for the given year
        """
        if self.inflation_model == 'linear' or not self.inflation_model:
            # Simple compound inflation
            return (1 + base_inflation_rate) ** year_index

        elif self.inflation_model == 'dual_rate' and self.inflation_transition_year and self.inflation_long_term_rate:
            # Dual-rate model: use base rate until transition year, then long-term rate
            transition_year_idx = self.inflation_transition_year - 1

            if year_index <= transition_year_idx:
                # Before transition: use base rate
                return (1 + base_inflation_rate) ** year_index
            else:
                # After transition: use base rate until transition, then long-term rate
                pre_transition_factor = (1 + base_inflation_rate) ** transition_year_idx
                post_transition_years = year_index - transition_year_idx
                long_term_rate = Decimal(str(self.inflation_long_term_rate))
                post_transition_factor = (1 + long_term_rate) ** post_transition_years
                return pre_transition_factor * post_transition_factor

        # Default to simple compound inflation
        return (1 + base_inflation_rate) ** year_index



class CPIRate(db.Model):
    """Model for storing universal CPI rates."""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False, unique=True)
    rate = db.Column(db.Numeric(10, 4), nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_rate(category):
        """Get the rate for a specific CPI category."""
        rate = CPIRate.query.filter_by(category=category).first()
        return float(rate.rate) if rate else None

    def __repr__(self):
        return f'<CPIRate {self.category}: {self.rate}%>'

class ECECWorkerType(db.Model):
    """Model for storing ECEC worker type data."""
    id = db.Column(db.Integer, primary_key=True)
    worker_type = db.Column(db.String(100), nullable=False, unique=True)
    wages_and_salaries = db.Column(db.Numeric(10, 2), nullable=False)
    total_benefits = db.Column(db.Numeric(10, 2), nullable=False)
    legally_required_benefits = db.Column(db.Numeric(10, 4), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_all_types():
        """Get all worker types."""
        return [(wt.worker_type, wt.worker_type) for wt in ECECWorkerType.query.all()]

    @staticmethod
    def get_data(worker_type):
        """Get data for a specific worker type."""
        data = ECECWorkerType.query.filter_by(worker_type=worker_type).first()
        if data:
            return {
                'wages_and_salaries': float(data.wages_and_salaries),
                'total_benefits': float(data.total_benefits),
                'legally_required_benefits': float(data.legally_required_benefits)
            }
        return None

class ECECGeographicRegion(db.Model):
    """Model for storing ECEC geographic region data."""
    id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.String(100), nullable=False, unique=True)
    wages_and_salaries = db.Column(db.Numeric(10, 2), nullable=False)
    total_benefits = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_all_regions():
        """Get all geographic regions."""
        return [(r.region, r.region) for r in ECECGeographicRegion.query.all()]

    @staticmethod
    def get_data(region):
        """Get data for a specific region."""
        data = ECECGeographicRegion.query.filter_by(region=region).first()
        if data:
            return {
                'wages_and_salaries': float(data.wages_and_salaries),
                'total_benefits': float(data.total_benefits)
            }
        return None

class FringeBenefitScenario(db.Model):
    """Model for storing fringe benefit calculation scenarios."""
    id = db.Column(db.Integer, primary_key=True)
    evaluee_id = db.Column(db.Integer, db.ForeignKey('evaluee.id'), nullable=False)
    scenario_name = db.Column(db.String(100), nullable=False)
    worker_type = db.Column(db.String(100), nullable=False)
    annual_salary = db.Column(db.Numeric(10, 2), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    inflation_rate = db.Column(db.Numeric(10, 4), nullable=False)
    years_since_update = db.Column(db.Integer, default=0)
    adjusted_fringe_percentage = db.Column(db.Numeric(10, 4))
    fringe_value = db.Column(db.Numeric(15, 2))
    total_compensation = db.Column(db.Numeric(15, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with Evaluee
    evaluee = db.relationship('Evaluee', backref='fringe_benefit_scenarios', lazy=True)

class HouseholdServicesScenario(db.Model):
    """Model for storing household services calculation scenarios."""
    id = db.Column(db.Integer, primary_key=True)
    evaluee_id = db.Column(db.Integer, db.ForeignKey('evaluee.id'), nullable=False)
    scenario_name = db.Column(db.String(100), nullable=False)
    area_wage_adjustment = db.Column(db.Numeric(10, 4), nullable=False)
    reduction_percentage = db.Column(db.Numeric(10, 4), nullable=False)
    growth_rate = db.Column(db.Numeric(10, 4), nullable=False)
    discount_rate = db.Column(db.Numeric(10, 4), nullable=False)
    present_value = db.Column(db.Numeric(15, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with Evaluee and Stages
    evaluee = db.relationship('Evaluee', backref='household_services_scenarios', lazy=True)
    stages = db.relationship('HouseholdServiceStage', backref='scenario', lazy=True, cascade='all, delete-orphan')

    def calculate_present_value(self):
        """Calculate the present value of household services using the staged valuation model."""
        if not self.stages:
            self.present_value = Decimal('0.00')
            return Decimal('0.00')

        total_pv = Decimal('0.0')
        global_year = 1  # Track the overall year across all stages

        # Sort stages by stage_number
        for stage in sorted(self.stages, key=lambda x: x.stage_number):
            for local_year in range(1, stage.years + 1):
                # Growth is based on local year within the stage
                grown_value = stage.annual_value * (
                    (Decimal('1.0') + self.growth_rate) ** (local_year - 1)
                )
                adjusted_value = grown_value * self.area_wage_adjustment * self.reduction_percentage
                
                # Discounting is based on global year from start of all stages
                present_value = adjusted_value / (
                    (Decimal('1.0') + self.discount_rate) ** global_year
                )
                total_pv += present_value
                global_year += 1  # Increment global year

        # Store the calculated value in the model
        result = total_pv.quantize(Decimal('0.01'))
        self.present_value = result

        return result

class HouseholdServiceStage(db.Model):
    """Model for storing stages within a household services scenario."""
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('household_services_scenario.id'), nullable=False)
    stage_number = db.Column(db.Integer, nullable=False)
    years = db.Column(db.Integer, nullable=False)
    annual_value = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PensionScenario(db.Model):
    """Model for pension scenarios."""
    __tablename__ = 'pension_scenarios'

    id = db.Column(db.Integer, primary_key=True)
    evaluee_id = db.Column(db.Integer, db.ForeignKey('evaluee.id'), nullable=False)
    scenario_name = db.Column(db.String(100), nullable=False)
    calculation_method = db.Column(db.String(20), nullable=False)  # 'contributions' or 'payments'
    growth_rate = db.Column(db.Float, nullable=False)
    discount_rate = db.Column(db.Float, nullable=False)
    present_value = db.Column(db.Float)

    # Fields for 'contributions' calculation method
    years_to_retirement = db.Column(db.Integer)
    annual_contribution = db.Column(db.Float)

    # Fields for 'payments' calculation method
    retirement_age = db.Column(db.Integer)
    life_expectancy = db.Column(db.Integer)
    annual_pension_benefit = db.Column(db.Float)

    # New fields for pension types
    pension_type = db.Column(db.String(30), default='defined_benefit')  # 'defined_benefit', 'defined_contribution', or 'hybrid'
    employer_match_percentage = db.Column(db.Float)
    vesting_period = db.Column(db.Integer)
    vesting_percentage = db.Column(db.Float)

    # New fields for social security integration
    include_social_security = db.Column(db.Boolean, default=False)
    social_security_start_age = db.Column(db.Integer)
    social_security_benefit = db.Column(db.Float)

    # New fields for early retirement analysis
    early_retirement_age = db.Column(db.Integer)
    early_retirement_penalty = db.Column(db.Float)

    # Relationships
    evaluee = db.relationship('Evaluee', backref=db.backref('pension_scenarios', lazy=True))

    def calculate_present_value(self):
        """Calculate the present value of the pension scenario."""
        if self.calculation_method == 'contributions':
            # Calculate future value of contributions
            fv = self._calculate_future_value_of_contributions()
            # Calculate present value of future value
            self.present_value = fv / ((1 + self.discount_rate) ** self.years_to_retirement)
        else:  # payments
            # Calculate present value of pension payments
            self.present_value = self._calculate_present_value_of_payments()

            # Add social security benefits if included
            if self.include_social_security and self.social_security_benefit and self.social_security_start_age:
                ss_present_value = self._calculate_social_security_present_value()
                self.present_value += ss_present_value

        return self.present_value

    def _calculate_future_value_of_contributions(self):
        """Calculate the future value of contributions."""
        if not self.annual_contribution or not self.years_to_retirement:
            return 0

        # Basic future value calculation
        fv = 0
        for year in range(self.years_to_retirement):
            contribution = self.annual_contribution

            # Add employer match if applicable
            if self.pension_type in ['defined_contribution', 'hybrid'] and self.employer_match_percentage:
                # Apply vesting if applicable
                vesting_factor = 1.0
                if self.vesting_period and self.vesting_percentage:
                    years_vested = max(0, year - self.vesting_period + 1)
                    if years_vested <= 0:
                        vesting_factor = 0.0
                    else:
                        vesting_factor = min(1.0, years_vested * (self.vesting_percentage / 100))

                employer_match = contribution * (self.employer_match_percentage / 100) * vesting_factor
                contribution += employer_match

            fv += contribution * ((1 + self.growth_rate) ** (self.years_to_retirement - year - 1))

        return fv

    def _calculate_present_value_of_payments(self):
        """Calculate the present value of pension payments."""
        if not self.retirement_age or not self.life_expectancy or not self.annual_pension_benefit:
            return 0

        # Calculate years of payments
        payment_years = self.life_expectancy - self.retirement_age
        if payment_years <= 0:
            return 0

        # Calculate present value
        pv = 0
        for year in range(payment_years):
            pv += self.annual_pension_benefit / ((1 + self.discount_rate) ** (year + 1))

        return pv

    def _calculate_social_security_present_value(self):
        """Calculate the present value of social security benefits."""
        if not self.include_social_security or not self.social_security_benefit or not self.social_security_start_age:
            return 0

        # Calculate years of social security payments
        payment_years = self.life_expectancy - self.social_security_start_age
        if payment_years <= 0:
            return 0

        # Calculate present value
        pv = 0
        for year in range(payment_years):
            pv += self.social_security_benefit / ((1 + self.discount_rate) ** (year + 1))

        return pv

    def calculate_retirement_options(self):
        """Calculate different retirement options for comparison."""
        if self.calculation_method != 'payments' or not self.retirement_age or not self.life_expectancy:
            return []

        options = []

        # Standard retirement option (already calculated)
        standard_option = {
            'age': self.retirement_age,
            'annual_benefit': self.annual_pension_benefit,
            'present_value': self.present_value - (self._calculate_social_security_present_value() if self.include_social_security else 0),
            'difference': 0  # No difference from standard
        }
        options.append(standard_option)

        # Early retirement options
        if self.early_retirement_age and self.early_retirement_penalty:
            for age in range(self.early_retirement_age, self.retirement_age):
                years_early = self.retirement_age - age
                penalty_factor = years_early * self.early_retirement_penalty
                reduced_benefit = self.annual_pension_benefit * (1 - penalty_factor)

                # Calculate present value for this option
                payment_years = self.life_expectancy - age
                if payment_years <= 0:
                    continue

                pv = 0
                for year in range(payment_years):
                    pv += reduced_benefit / ((1 + self.discount_rate) ** (year + 1))

                options.append({
                    'age': age,
                    'annual_benefit': reduced_benefit,
                    'present_value': pv,
                    'difference': pv - standard_option['present_value']
                })

        # Later retirement options (up to 5 years later)
        for age in range(self.retirement_age + 1, min(self.retirement_age + 6, self.life_expectancy)):
            # Assume benefit increases by 5% per year of delayed retirement
            increased_benefit = self.annual_pension_benefit * (1 + 0.05 * (age - self.retirement_age))

            # Calculate present value for this option
            payment_years = self.life_expectancy - age
            if payment_years <= 0:
                continue

            pv = 0
            for year in range(payment_years):
                pv += increased_benefit / ((1 + self.discount_rate) ** (year + 1))

            options.append({
                'age': age,
                'annual_benefit': increased_benefit,
                'present_value': pv,
                'difference': pv - standard_option['present_value']
            })

        # Sort options by age
        options.sort(key=lambda x: x['age'])

        return options

class CareerProgression(db.Model):
    """Model for storing career progression events."""
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('earnings_scenario.id', ondelete='CASCADE'), nullable=False)
    progression_type = db.Column(db.String(50), nullable=False)  # promotion, job_change, etc.
    year = db.Column(db.Integer)  # Year of progression event
    age = db.Column(db.Integer)  # Age at progression event
    salary_increase = db.Column(db.Numeric(10, 4), nullable=False)  # Percentage increase
    description = db.Column(db.String(200))  # Description of the progression event

class IndustryGrowthRate(db.Model):
    """Model for storing industry-specific growth rates."""
    id = db.Column(db.Integer, primary_key=True)
    industry_name = db.Column(db.String(100), nullable=False)
    growth_rate = db.Column(db.Numeric(10, 4), nullable=False)
    description = db.Column(db.String(200))

    @staticmethod
    def get_rate(industry_name):
        """Get the growth rate for a specific industry."""
        rate = IndustryGrowthRate.query.filter_by(industry_name=industry_name).first()
        return float(rate.growth_rate) if rate else None

class MedicalCareCategory(db.Model):
    """Model for storing medical care categories and their growth rates."""
    id = db.Column(db.Integer, primary_key=True)
    lcp_category = db.Column(db.String(100), nullable=False, unique=True)  # Life Care Plan Category
    definition_category = db.Column(db.String(200), nullable=False)  # Corresponding Definition Category
    growth_rate = db.Column(db.Numeric(10, 4))  # Growth rate for this category
    description = db.Column(db.Text)  # Additional description or notes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_all_categories():
        """Get all medical care categories."""
        return [(cat.lcp_category, cat.lcp_category) for cat in MedicalCareCategory.query.all()]

    @staticmethod
    def get_rate(category):
        """Get the growth rate for a specific medical care category."""
        cat = MedicalCareCategory.query.filter_by(lcp_category=category).first()
        return float(cat.growth_rate) if cat and cat.growth_rate is not None else None

    def __repr__(self):
        return f'<MedicalCareCategory {self.lcp_category}: {self.growth_rate}%>'

class Analysis(db.Model):
    """Generic analysis model for storing different types of analyses."""
    __tablename__ = 'analyses'

    id = db.Column(db.Integer, primary_key=True)
    evaluee_id = db.Column(db.Integer, db.ForeignKey('evaluee.id', ondelete='CASCADE'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)  # 'pediatric', 'income', 'benefits', etc.
    title = db.Column(db.String(255))
    parameters = db.Column(JSON, nullable=True)  # Store analysis parameters as JSON
    results = db.Column(JSON, nullable=True)     # Store analysis results as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    evaluee = db.relationship('Evaluee', backref=db.backref('analyses', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Analysis {self.id}: {self.analysis_type} for Evaluee {self.evaluee_id}>'