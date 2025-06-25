"""
Life Care Plan Cost Calculator

Adapted from mcp_streamlit calculator.py for Flask integration.
Provides comprehensive cost calculations with inflation and present value analysis.
"""

from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass, field
import math

from ..models.life_care_plan import (
    LifeCarePlan, LCPScenario, LCPService, LCPServiceAssignment,
    ServiceType, ServiceCalculation, ScenarioResults, ProjectionSettings
)

logger = logging.getLogger(__name__)


class LifeCarePlanCalculator:
    """
    Comprehensive calculator for life care plan cost projections.
    
    Handles inflation adjustments, present value calculations, and detailed
    cost scheduling for various service types.
    """
    
    def __init__(self, plan: LifeCarePlan):
        """Initialize calculator with a life care plan."""
        self.plan = plan
        self.evaluee = plan.evaluee
        
    def calculate_scenario(self, scenario: LCPScenario) -> ScenarioResults:
        """
        Calculate complete costs for a scenario.
        
        Args:
            scenario: The scenario to calculate
            
        Returns:
            ScenarioResults with comprehensive cost analysis
        """
        logger.info(f"Calculating scenario: {scenario.scenario_name}")
        
        # Get projection settings
        settings = self._get_projection_settings(scenario)
        
        # Calculate each service
        service_calculations = []
        total_cost = Decimal('0')
        total_present_value = Decimal('0')
        category_totals = {}
        annual_totals = {}
        
        for assignment in scenario.service_assignments:
            if not assignment.is_included:
                continue
                
            service_calc = self._calculate_service(assignment, settings)
            service_calculations.append(service_calc)
            
            total_cost += service_calc.total_cost
            total_present_value += service_calc.present_value
            
            # Add to category totals
            category = assignment.service.category or 'Other'
            if category not in category_totals:
                category_totals[category] = Decimal('0')
            category_totals[category] += service_calc.present_value
            
            # Add to annual totals
            for year, cost in service_calc.annual_costs.items():
                if year not in annual_totals:
                    annual_totals[year] = Decimal('0')
                annual_totals[year] += cost
        
        return ScenarioResults(
            scenario_id=scenario.id,
            scenario_name=scenario.scenario_name,
            total_cost=total_cost,
            present_value=total_present_value,
            service_calculations=service_calculations,
            category_totals=category_totals,
            annual_totals=annual_totals,
            calculation_date=datetime.utcnow()
        )
    
    def _calculate_service(self, assignment: LCPServiceAssignment, settings: ProjectionSettings) -> ServiceCalculation:
        """
        Calculate costs for a single service assignment.
        
        Args:
            assignment: Service assignment with parameters
            settings: Projection settings
            
        Returns:
            ServiceCalculation with detailed cost breakdown
        """
        service = assignment.service
        service_type = ServiceType(service.service_type)
        
        # Get effective parameters
        unit_cost = float(assignment.effective_unit_cost)
        start_age = float(assignment.effective_start_age)
        end_age = float(assignment.effective_end_age) if assignment.effective_end_age else settings.end_age
        
        # Calculate based on service type
        if service_type == ServiceType.RECURRING:
            return self._calculate_recurring_service(assignment, settings)
        elif service_type == ServiceType.ONE_TIME:
            return self._calculate_one_time_service(assignment, settings)
        elif service_type == ServiceType.DISTRIBUTED:
            return self._calculate_distributed_service(assignment, settings)
        else:
            raise ValueError(f"Unknown service type: {service_type}")
    
    def _calculate_recurring_service(self, assignment: LCPServiceAssignment, settings: ProjectionSettings) -> ServiceCalculation:
        """Calculate costs for recurring services."""
        service = assignment.service
        
        # Get parameters
        unit_cost = float(assignment.effective_unit_cost)
        frequency = float(assignment.effective_frequency)
        start_age = float(assignment.effective_start_age)
        end_age = float(assignment.effective_end_age) if assignment.effective_end_age else settings.end_age
        
        # Calculate cost schedule
        annual_costs = {}
        cost_schedule = []
        total_cost = Decimal('0')
        present_value = Decimal('0')
        
        current_age = start_age
        year = 0
        
        while current_age < end_age and current_age < settings.end_age:
            # Calculate years from cost base year
            years_from_base = year + (settings.calculation_date.year if settings.calculation_date else datetime.now().year) - service.cost_year
            
            # Apply inflation
            inflated_cost = unit_cost * ((1 + settings.inflation_rate) ** years_from_base)
            annual_cost = Decimal(str(inflated_cost * frequency)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Calculate present value
            pv_factor = 1 / ((1 + settings.discount_rate) ** year)
            pv_cost = annual_cost * Decimal(str(pv_factor))
            
            annual_costs[year] = annual_cost
            total_cost += annual_cost
            present_value += pv_cost
            
            cost_schedule.append({
                'year': year,
                'age': current_age,
                'nominal_cost': annual_cost,
                'present_value': pv_cost,
                'frequency': frequency,
                'unit_cost': Decimal(str(inflated_cost)).quantize(Decimal('0.01'))
            })
            
            current_age += 1
            year += 1
        
        # Handle replacement cycles
        if service.include_replacement and service.replacement_cycle_years:
            replacement_costs = self._calculate_replacement_costs(
                assignment, settings, start_age, end_age
            )
            for year, cost in replacement_costs.items():
                if year in annual_costs:
                    annual_costs[year] += cost
                else:
                    annual_costs[year] = cost
                total_cost += cost
                # Add replacement PV
                pv_factor = 1 / ((1 + settings.discount_rate) ** year)
                present_value += cost * Decimal(str(pv_factor))
        
        first_year_cost = annual_costs.get(0, Decimal('0'))
        
        return ServiceCalculation(
            service_id=service.id,
            service_name=service.service_name,
            total_cost=total_cost,
            present_value=present_value,
            first_year_cost=first_year_cost,
            annual_costs=annual_costs,
            cost_schedule=cost_schedule
        )
    
    def _calculate_one_time_service(self, assignment: LCPServiceAssignment, settings: ProjectionSettings) -> ServiceCalculation:
        """Calculate costs for one-time services."""
        service = assignment.service
        
        unit_cost = float(assignment.effective_unit_cost)
        service_age = float(service.service_age) if service.service_age else float(assignment.effective_start_age)
        
        # Calculate year of service
        year = int(service_age - settings.start_age)
        
        if year < 0 or service_age > settings.end_age:
            # Service is outside projection period
            return ServiceCalculation(
                service_id=service.id,
                service_name=service.service_name,
                total_cost=Decimal('0'),
                present_value=Decimal('0'),
                first_year_cost=Decimal('0'),
                annual_costs={},
                cost_schedule=[]
            )
        
        # Apply inflation
        years_from_base = year + (settings.calculation_date.year if settings.calculation_date else datetime.now().year) - service.cost_year
        inflated_cost = unit_cost * ((1 + settings.inflation_rate) ** years_from_base)
        total_cost = Decimal(str(inflated_cost)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Calculate present value
        pv_factor = 1 / ((1 + settings.discount_rate) ** year)
        present_value = total_cost * Decimal(str(pv_factor))
        
        annual_costs = {year: total_cost}
        cost_schedule = [{
            'year': year,
            'age': service_age,
            'nominal_cost': total_cost,
            'present_value': present_value,
            'frequency': 1,
            'unit_cost': total_cost
        }]
        
        first_year_cost = total_cost if year == 0 else Decimal('0')
        
        return ServiceCalculation(
            service_id=service.id,
            service_name=service.service_name,
            total_cost=total_cost,
            present_value=present_value,
            first_year_cost=first_year_cost,
            annual_costs=annual_costs,
            cost_schedule=cost_schedule
        )
    
    def _calculate_distributed_service(self, assignment: LCPServiceAssignment, settings: ProjectionSettings) -> ServiceCalculation:
        """Calculate costs for distributed services."""
        service = assignment.service
        
        unit_cost = float(assignment.effective_unit_cost)
        total_instances = service.total_instances or 1
        start_age = float(service.distribution_start_age or assignment.effective_start_age)
        end_age = float(service.distribution_end_age or assignment.effective_end_age or settings.end_age)
        
        # Calculate distribution
        distribution_years = end_age - start_age
        if distribution_years <= 0:
            return ServiceCalculation(
                service_id=service.id,
                service_name=service.service_name,
                total_cost=Decimal('0'),
                present_value=Decimal('0'),
                first_year_cost=Decimal('0'),
                annual_costs={},
                cost_schedule=[]
            )
        
        instances_per_year = total_instances / distribution_years
        
        annual_costs = {}
        cost_schedule = []
        total_cost = Decimal('0')
        present_value = Decimal('0')
        
        current_age = start_age
        year = int(start_age - settings.start_age)
        
        while current_age < end_age and current_age < settings.end_age:
            # Calculate instances for this year
            remaining_instances = total_instances - sum(
                schedule['instances'] for schedule in cost_schedule
            )
            year_instances = min(instances_per_year, remaining_instances)
            
            if year_instances <= 0:
                break
            
            # Apply inflation
            years_from_base = year + (settings.calculation_date.year if settings.calculation_date else datetime.now().year) - service.cost_year
            inflated_cost = unit_cost * ((1 + settings.inflation_rate) ** years_from_base)
            annual_cost = Decimal(str(inflated_cost * year_instances)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Calculate present value
            pv_factor = 1 / ((1 + settings.discount_rate) ** year)
            pv_cost = annual_cost * Decimal(str(pv_factor))
            
            annual_costs[year] = annual_cost
            total_cost += annual_cost
            present_value += pv_cost
            
            cost_schedule.append({
                'year': year,
                'age': current_age,
                'nominal_cost': annual_cost,
                'present_value': pv_cost,
                'instances': year_instances,
                'unit_cost': Decimal(str(inflated_cost)).quantize(Decimal('0.01'))
            })
            
            current_age += 1
            year += 1
        
        first_year_cost = annual_costs.get(int(start_age - settings.start_age), Decimal('0'))
        
        return ServiceCalculation(
            service_id=service.id,
            service_name=service.service_name,
            total_cost=total_cost,
            present_value=present_value,
            first_year_cost=first_year_cost,
            annual_costs=annual_costs,
            cost_schedule=cost_schedule
        )
    
    def _calculate_replacement_costs(self, assignment: LCPServiceAssignment, settings: ProjectionSettings, 
                                   start_age: float, end_age: float) -> Dict[int, Decimal]:
        """Calculate replacement costs for equipment."""
        service = assignment.service
        replacement_costs = {}
        
        if not service.replacement_cycle_years:
            return replacement_costs
        
        unit_cost = float(assignment.effective_unit_cost)
        replacement_cycle = service.replacement_cycle_years
        
        # Calculate replacement years
        current_age = start_age + replacement_cycle
        
        while current_age < end_age and current_age < settings.end_age:
            year = int(current_age - settings.start_age)
            
            # Apply inflation
            years_from_base = year + (settings.calculation_date.year if settings.calculation_date else datetime.now().year) - service.cost_year
            inflated_cost = unit_cost * ((1 + settings.inflation_rate) ** years_from_base)
            replacement_cost = Decimal(str(inflated_cost)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            replacement_costs[year] = replacement_cost
            current_age += replacement_cycle
        
        return replacement_costs
    
    def _get_projection_settings(self, scenario: LCPScenario) -> ProjectionSettings:
        """Get projection settings for a scenario."""
        return ProjectionSettings(
            start_age=float(self.plan.projection_start_age),
            end_age=float(self.plan.projection_end_age),
            discount_rate=float(scenario.effective_discount_rate),
            inflation_rate=float(scenario.effective_inflation_rate),
            calculation_date=datetime.utcnow()
        )
    
    def generate_cost_summary(self, results: ScenarioResults) -> Dict[str, Any]:
        """
        Generate a comprehensive cost summary.
        
        Args:
            results: Scenario calculation results
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'scenario_name': results.scenario_name,
            'total_cost': results.total_cost,
            'present_value': results.present_value,
            'category_breakdown': results.category_totals,
            'number_of_services': len(results.service_calculations),
            'projection_years': self.plan.projection_years,
            'average_annual_cost': results.total_cost / Decimal(str(self.plan.projection_years)) if self.plan.projection_years > 0 else Decimal('0'),
            'calculation_date': results.calculation_date
        }
        
        # Add top services by cost
        service_costs = [(calc.service_name, calc.present_value) for calc in results.service_calculations]
        service_costs.sort(key=lambda x: x[1], reverse=True)
        summary['top_services'] = service_costs[:10]
        
        # Add annual cost trend
        if results.annual_totals:
            years = sorted(results.annual_totals.keys())
            summary['first_year_total'] = results.annual_totals.get(years[0], Decimal('0'))
            summary['last_year_total'] = results.annual_totals.get(years[-1], Decimal('0'))
            summary['peak_year_cost'] = max(results.annual_totals.values())
            summary['peak_year'] = max(results.annual_totals.keys(), key=lambda k: results.annual_totals[k])
        
        return summary
    
    def compare_scenarios(self, scenarios: List[LCPScenario]) -> Dict[str, Any]:
        """
        Compare multiple scenarios.
        
        Args:
            scenarios: List of scenarios to compare
            
        Returns:
            Dictionary with comparison analysis
        """
        if not scenarios:
            return {}
        
        scenario_results = []
        for scenario in scenarios:
            results = self.calculate_scenario(scenario)
            scenario_results.append(results)
        
        # Calculate comparison metrics
        present_values = [r.present_value for r in scenario_results]
        total_costs = [r.total_cost for r in scenario_results]
        
        comparison = {
            'scenarios': [
                {
                    'name': r.scenario_name,
                    'present_value': r.present_value,
                    'total_cost': r.total_cost,
                    'number_of_services': len(r.service_calculations)
                } for r in scenario_results
            ],
            'present_value_range': {
                'min': min(present_values),
                'max': max(present_values),
                'difference': max(present_values) - min(present_values)
            },
            'total_cost_range': {
                'min': min(total_costs),
                'max': max(total_costs),
                'difference': max(total_costs) - min(total_costs)
            },
            'average_present_value': sum(present_values) / len(present_values),
            'average_total_cost': sum(total_costs) / len(total_costs)
        }
        
        return comparison
    
    def validate_plan(self) -> List[str]:
        """
        Validate the life care plan for calculation readiness.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check evaluee information
        if not self.evaluee:
            errors.append("No evaluee associated with plan")
        elif not self.evaluee.date_of_birth:
            errors.append("Evaluee date of birth is required")
        
        # Check plan settings
        if self.plan.projection_start_age >= self.plan.projection_end_age:
            errors.append("Projection start age must be less than end age")
        
        if self.plan.discount_rate <= 0 or self.plan.discount_rate > 1:
            errors.append("Discount rate must be between 0 and 1")
        
        if self.plan.inflation_rate < 0 or self.plan.inflation_rate > 1:
            errors.append("Inflation rate must be between 0 and 1")
        
        # Check scenarios
        if not self.plan.scenarios:
            errors.append("Plan must have at least one scenario")
        
        for scenario in self.plan.scenarios:
            if not scenario.service_assignments:
                errors.append(f"Scenario '{scenario.scenario_name}' has no services assigned")
            
            for assignment in scenario.service_assignments:
                service = assignment.service
                
                # Validate service parameters
                if assignment.effective_unit_cost <= 0:
                    errors.append(f"Service '{service.service_name}' has invalid unit cost")
                
                if assignment.effective_start_age < 0:
                    errors.append(f"Service '{service.service_name}' has invalid start age")
                
                if service.service_type == ServiceType.RECURRING.value:
                    if not assignment.effective_frequency or assignment.effective_frequency <= 0:
                        errors.append(f"Recurring service '{service.service_name}' has invalid frequency")
                
                elif service.service_type == ServiceType.DISTRIBUTED.value:
                    if not service.total_instances or service.total_instances <= 0:
                        errors.append(f"Distributed service '{service.service_name}' has invalid total instances")
        
        return errors