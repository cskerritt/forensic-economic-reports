"""
Life Care Plan Models

Adapted from mcp_streamlit for Flask SQLAlchemy integration.
Provides comprehensive life care planning with cost calculations and projections.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import json

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.types import Numeric as SQLDecimal
from sqlalchemy.orm import relationship
from .models import db


class ServiceType(Enum):
    """Types of medical services in a life care plan."""
    RECURRING = "recurring"
    ONE_TIME = "one_time"
    DISTRIBUTED = "distributed"


class ServiceCategory(Enum):
    """Categories for organizing medical services."""
    MEDICAL = "Medical"
    THERAPY = "Therapy"
    EQUIPMENT = "Equipment"
    MEDICATIONS = "Medications"
    ATTENDANT_CARE = "Attendant Care"
    TRANSPORTATION = "Transportation"
    HOME_MODIFICATIONS = "Home Modifications"
    VOCATIONAL = "Vocational"
    OTHER = "Other"


class LCPEvaluee(db.Model):
    """Life Care Plan evaluee/patient information."""
    __tablename__ = 'lcp_evaluees'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Basic Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    date_of_injury = Column(DateTime, nullable=True)
    gender = Column(String(10), nullable=True)
    
    # Contact Information
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    
    # Medical Information
    primary_diagnosis = Column(Text, nullable=True)
    secondary_diagnoses = Column(Text, nullable=True)
    injury_description = Column(Text, nullable=True)
    current_medical_status = Column(Text, nullable=True)
    
    # Life Expectancy
    life_expectancy = Column(SQLDecimal(5, 2), nullable=True)
    life_expectancy_source = Column(String(200), nullable=True)
    
    # Economic Information
    pre_injury_income = Column(SQLDecimal(10, 2), nullable=True)
    occupation = Column(String(200), nullable=True)
    education_level = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="lcp_evaluees")
    life_care_plans = relationship("LifeCarePlan", backref="evaluee", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<LCPEvaluee {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age_at_injury(self):
        if self.date_of_birth and self.date_of_injury:
            return (self.date_of_injury.date() - self.date_of_birth.date()).days // 365
        return None
    
    @property
    def current_age(self):
        if self.date_of_birth:
            return (date.today() - self.date_of_birth.date()).days // 365
        return None


class LifeCarePlan(db.Model):
    """Main life care plan container."""
    __tablename__ = 'life_care_plans'
    
    id = Column(Integer, primary_key=True)
    evaluee_id = Column(Integer, ForeignKey('lcp_evaluees.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Plan Information
    plan_name = Column(String(200), nullable=False)
    plan_description = Column(Text, nullable=True)
    plan_date = Column(DateTime, default=datetime.utcnow)
    
    # Projection Settings
    projection_start_age = Column(SQLDecimal(5, 2), nullable=False, default=0)
    projection_end_age = Column(SQLDecimal(5, 2), nullable=False, default=75)
    discount_rate = Column(SQLDecimal(5, 4), nullable=False, default=0.025)  # 2.5%
    inflation_rate = Column(SQLDecimal(5, 4), nullable=False, default=0.03)  # 3%
    
    # Additional Settings
    include_attendant_care = Column(Boolean, default=True)
    include_equipment_replacement = Column(Boolean, default=True)
    use_present_value = Column(Boolean, default=True)
    
    # Methodology and Assumptions
    methodology_notes = Column(Text, nullable=True)
    assumptions = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_template = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    scenarios = relationship("LCPScenario", backref="life_care_plan", cascade="all, delete-orphan")
    service_tables = relationship("LCPServiceTable", backref="life_care_plan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<LifeCarePlan {self.plan_name}>'
    
    @property
    def default_scenario(self):
        """Get the default/primary scenario."""
        return next((s for s in self.scenarios if s.is_default), None)
    
    @property
    def projection_years(self):
        """Calculate total projection years."""
        return float(self.projection_end_age - self.projection_start_age)


class LCPScenario(db.Model):
    """Life care plan scenario for different assumptions."""
    __tablename__ = 'lcp_scenarios'
    
    id = Column(Integer, primary_key=True)
    life_care_plan_id = Column(Integer, ForeignKey('life_care_plans.id'), nullable=False)
    
    # Scenario Information
    scenario_name = Column(String(200), nullable=False)
    scenario_description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    
    # Economic Settings
    discount_rate = Column(SQLDecimal(5, 4), nullable=True)  # Override plan default
    inflation_rate = Column(SQLDecimal(5, 4), nullable=True)  # Override plan default
    
    # Assumptions
    assumptions = Column(Text, nullable=True)
    methodology_notes = Column(Text, nullable=True)
    
    # Calculated Results (stored for performance)
    total_cost = Column(SQLDecimal(15, 2), nullable=True)
    present_value = Column(SQLDecimal(15, 2), nullable=True)
    calculation_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service_assignments = relationship("LCPServiceAssignment", backref="scenario", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<LCPScenario {self.scenario_name}>'
    
    @property
    def effective_discount_rate(self):
        """Get effective discount rate (scenario override or plan default)."""
        return self.discount_rate or self.life_care_plan.discount_rate
    
    @property
    def effective_inflation_rate(self):
        """Get effective inflation rate (scenario override or plan default)."""
        return self.inflation_rate or self.life_care_plan.inflation_rate


class LCPServiceTable(db.Model):
    """Collection of related services in a life care plan."""
    __tablename__ = 'lcp_service_tables'
    
    id = Column(Integer, primary_key=True)
    life_care_plan_id = Column(Integer, ForeignKey('life_care_plans.id'), nullable=False)
    
    # Table Information
    table_name = Column(String(200), nullable=False)
    table_description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # ServiceCategory enum
    
    # Display Settings
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    services = relationship("LCPService", backref="service_table", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<LCPServiceTable {self.table_name}>'


class LCPService(db.Model):
    """Individual medical service in a life care plan."""
    __tablename__ = 'lcp_services'
    
    id = Column(Integer, primary_key=True)
    service_table_id = Column(Integer, ForeignKey('lcp_service_tables.id'), nullable=False)
    
    # Service Information
    service_name = Column(String(300), nullable=False)
    service_description = Column(Text, nullable=True)
    service_type = Column(String(20), nullable=False)  # ServiceType enum
    category = Column(String(50), nullable=True)  # ServiceCategory enum
    
    # Cost Information
    unit_cost = Column(SQLDecimal(10, 2), nullable=False)
    cost_year = Column(Integer, nullable=False)  # Base year for cost
    
    # Frequency and Timing
    frequency_per_year = Column(SQLDecimal(8, 2), nullable=True)  # For recurring services
    start_age = Column(SQLDecimal(5, 2), nullable=False)
    end_age = Column(SQLDecimal(5, 2), nullable=True)
    
    # One-time Service Settings
    service_age = Column(SQLDecimal(5, 2), nullable=True)  # For one-time services
    
    # Distributed Service Settings
    total_instances = Column(Integer, nullable=True)  # For distributed services
    distribution_start_age = Column(SQLDecimal(5, 2), nullable=True)
    distribution_end_age = Column(SQLDecimal(5, 2), nullable=True)
    
    # Replacement Settings
    replacement_cycle_years = Column(Integer, nullable=True)
    include_replacement = Column(Boolean, default=False)
    
    # Notes and Assumptions
    notes = Column(Text, nullable=True)
    assumptions = Column(Text, nullable=True)
    source = Column(String(300), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service_assignments = relationship("LCPServiceAssignment", backref="service", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<LCPService {self.service_name}>'
    
    @property
    def service_type_enum(self):
        """Get ServiceType enum value."""
        return ServiceType(self.service_type)
    
    @property
    def category_enum(self):
        """Get ServiceCategory enum value."""
        return ServiceCategory(self.category) if self.category else None


class LCPServiceAssignment(db.Model):
    """Assignment of a service to a scenario with specific parameters."""
    __tablename__ = 'lcp_service_assignments'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('lcp_scenarios.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('lcp_services.id'), nullable=False)
    
    # Override Settings (if different from service defaults)
    unit_cost_override = Column(SQLDecimal(10, 2), nullable=True)
    frequency_override = Column(SQLDecimal(8, 2), nullable=True)
    start_age_override = Column(SQLDecimal(5, 2), nullable=True)
    end_age_override = Column(SQLDecimal(5, 2), nullable=True)
    
    # Calculated Results (for performance)
    total_cost = Column(SQLDecimal(15, 2), nullable=True)
    present_value = Column(SQLDecimal(15, 2), nullable=True)
    first_year_cost = Column(SQLDecimal(12, 2), nullable=True)
    
    # Status
    is_included = Column(Boolean, default=True)
    
    # Notes
    assignment_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LCPServiceAssignment {self.service.service_name} -> {self.scenario.scenario_name}>'
    
    @property
    def effective_unit_cost(self):
        """Get effective unit cost (override or service default)."""
        return self.unit_cost_override or self.service.unit_cost
    
    @property
    def effective_frequency(self):
        """Get effective frequency (override or service default)."""
        return self.frequency_override or self.service.frequency_per_year
    
    @property
    def effective_start_age(self):
        """Get effective start age (override or service default)."""
        return self.start_age_override or self.service.start_age
    
    @property
    def effective_end_age(self):
        """Get effective end age (override or service default)."""
        return self.end_age_override or self.service.end_age


# Dataclasses for calculations (adapted from original models)

@dataclass
class ProjectionSettings:
    """Settings for life care plan projections."""
    start_age: float = 0.0
    end_age: float = 75.0
    discount_rate: float = 0.025
    inflation_rate: float = 0.03
    calculation_date: Optional[datetime] = None


@dataclass 
class ServiceCalculation:
    """Results of service cost calculations."""
    service_id: int
    service_name: str
    total_cost: Decimal
    present_value: Decimal
    first_year_cost: Decimal
    annual_costs: Dict[int, Decimal] = field(default_factory=dict)
    cost_schedule: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ScenarioResults:
    """Complete results for a scenario calculation."""
    scenario_id: int
    scenario_name: str
    total_cost: Decimal
    present_value: Decimal
    service_calculations: List[ServiceCalculation] = field(default_factory=list)
    category_totals: Dict[str, Decimal] = field(default_factory=dict)
    annual_totals: Dict[int, Decimal] = field(default_factory=dict)
    calculation_date: datetime = field(default_factory=datetime.utcnow)