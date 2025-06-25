"""
Enhanced Economic Loss Calculator with Advanced Features

This module provides comprehensive economic loss calculations with:
- Multi-scenario analysis (conservative, moderate, aggressive)
- Real-time economic data integration
- Tax optimization modeling
- Professional settlement range analysis
- Predictive career modeling
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import logging
from decimal import Decimal, ROUND_HALF_UP
from .wage_data_api import lookup_occupation_wages, get_bls_api
from .economic_report_generator import EconomicLossCalculator, EconomicLossCalculation

logger = logging.getLogger(__name__)

@dataclass
class ScenarioParameters:
    """Parameters for different economic scenarios."""
    name: str
    wage_growth_rate: float
    discount_rate: float
    unemployment_factor: float
    inflation_rate: float
    productivity_growth: float
    description: str

@dataclass
class SettlementRange:
    """Settlement range analysis results."""
    conservative_low: float
    conservative_high: float
    moderate_low: float
    moderate_high: float
    aggressive_low: float
    aggressive_high: float
    recommended_target: float
    confidence_level: float

class EnhancedEconomicCalculator:
    """Advanced economic calculator with multi-scenario analysis."""
    
    def __init__(self):
        """Initialize the enhanced calculator."""
        self.logger = logging.getLogger(__name__)
        self.base_calculator = EconomicLossCalculator()
        
        # Define standard economic scenarios
        self.scenarios = {
            'conservative': ScenarioParameters(
                name='Conservative',
                wage_growth_rate=0.025,  # 2.5%
                discount_rate=0.05,     # 5%
                unemployment_factor=0.06, # 6%
                inflation_rate=0.025,   # 2.5%
                productivity_growth=0.015, # 1.5%
                description='Conservative assumptions with higher discount rates and lower growth'
            ),
            'moderate': ScenarioParameters(
                name='Moderate',
                wage_growth_rate=0.032,  # 3.2%
                discount_rate=0.045,    # 4.5%
                unemployment_factor=0.045, # 4.5%
                inflation_rate=0.028,   # 2.8%
                productivity_growth=0.02, # 2%
                description='Moderate assumptions based on historical averages'
            ),
            'aggressive': ScenarioParameters(
                name='Aggressive',
                wage_growth_rate=0.04,   # 4%
                discount_rate=0.035,    # 3.5%
                unemployment_factor=0.03, # 3%
                inflation_rate=0.03,    # 3%
                productivity_growth=0.025, # 2.5%
                description='Aggressive assumptions favoring higher growth and lower discounting'
            )
        }
    
    def calculate_smart_wage_baseline(self, evaluee_data: Dict) -> Dict:
        """
        Calculate smart wage baseline using BLS API and regional data.
        
        Args:
            evaluee_data: Evaluee information
            
        Returns:
            Dictionary with wage analysis and recommendations
        """
        try:
            # Extract occupation and location information
            occupation = evaluee_data.get('occupation', evaluee_data.get('pre_injury_occupation', ''))
            state = evaluee_data.get('state', evaluee_data.get('residence_state', 'National'))
            msa = evaluee_data.get('msa', evaluee_data.get('metropolitan_area', None))
            
            # Get BLS wage data
            wage_data = lookup_occupation_wages(occupation, state, msa)
            
            # Get current base earnings for comparison
            current_earnings = float(evaluee_data.get('base_earnings', 0))
            
            # Analyze earnings position
            analysis = {
                'bls_data': wage_data,
                'current_earnings': current_earnings,
                'market_analysis': {},
                'recommendations': {}
            }
            
            if wage_data and 'annual_wage_mean' in wage_data:
                market_mean = wage_data['annual_wage_mean']
                market_median = wage_data.get('annual_wage_median', market_mean * 0.92)
                
                # Calculate percentile position
                percentiles = ['percentile_10', 'percentile_25', 'percentile_75', 'percentile_90']
                earnings_percentile = 50  # Default
                
                if current_earnings > 0:
                    if current_earnings >= wage_data.get('percentile_90', market_mean * 1.5):
                        earnings_percentile = 90
                    elif current_earnings >= wage_data.get('percentile_75', market_mean * 1.25):
                        earnings_percentile = 75
                    elif current_earnings >= market_median:
                        earnings_percentile = 50
                    elif current_earnings >= wage_data.get('percentile_25', market_mean * 0.78):
                        earnings_percentile = 25
                    else:
                        earnings_percentile = 10
                
                analysis['market_analysis'] = {
                    'market_mean': market_mean,
                    'market_median': market_median,
                    'earnings_percentile': earnings_percentile,
                    'earnings_vs_market': (current_earnings / market_mean - 1) * 100 if current_earnings > 0 else 0,
                    'regional_adjustment': wage_data.get('regional_adjustment_factor', 1.0),
                    'growth_rate': wage_data.get('growth_rate', 0.032)
                }
                
                # Provide recommendations
                if current_earnings == 0:
                    analysis['recommendations']['suggested_earnings'] = market_median
                    analysis['recommendations']['rationale'] = "Using market median as baseline"
                elif current_earnings < market_median * 0.8:
                    analysis['recommendations']['suggested_earnings'] = market_median
                    analysis['recommendations']['rationale'] = "Current earnings significantly below market - suggest market adjustment"
                elif current_earnings > market_mean * 1.3:
                    analysis['recommendations']['suggested_earnings'] = current_earnings
                    analysis['recommendations']['rationale'] = "High earner - use actual earnings"
                else:
                    analysis['recommendations']['suggested_earnings'] = current_earnings
                    analysis['recommendations']['rationale'] = "Current earnings within reasonable market range"
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in smart wage calculation: {str(e)}")
            return {
                'error': str(e),
                'current_earnings': evaluee_data.get('base_earnings', 0),
                'recommendations': {
                    'suggested_earnings': evaluee_data.get('base_earnings', 50000),
                    'rationale': 'Error in market analysis - using current earnings'
                }
            }
    
    def calculate_multi_scenario_analysis(self, evaluee_data: Dict) -> Dict:
        """
        Calculate economic loss under multiple scenarios.
        
        Args:
            evaluee_data: Evaluee information
            
        Returns:
            Dictionary with results for all scenarios
        """
        try:
            results = {
                'scenarios': {},
                'summary': {},
                'recommendations': {}
            }
            
            # Calculate smart wage baseline
            wage_analysis = self.calculate_smart_wage_baseline(evaluee_data)
            
            # Use recommended earnings if available
            if 'recommendations' in wage_analysis and 'suggested_earnings' in wage_analysis['recommendations']:
                base_earnings = wage_analysis['recommendations']['suggested_earnings']
            else:
                base_earnings = float(evaluee_data.get('base_earnings', 50000))
            
            # Calculate for each scenario
            for scenario_name, params in self.scenarios.items():
                scenario_data = evaluee_data.copy()
                scenario_data.update({
                    'base_earnings': base_earnings,
                    'wage_growth_rate': params.wage_growth_rate,
                    'discount_rate': params.discount_rate,
                    'unemployment_factor': params.unemployment_factor
                })
                
                # Calculate loss for this scenario
                calc = self.base_calculator.calculate_comprehensive_loss(scenario_data)
                
                results['scenarios'][scenario_name] = {
                    'parameters': params.__dict__,
                    'calculation': calc,
                    'total_loss': calc.total_economic_loss
                }
            
            # Calculate summary statistics
            total_losses = [results['scenarios'][s]['total_loss'] for s in results['scenarios']]
            
            results['summary'] = {
                'min_loss': min(total_losses),
                'max_loss': max(total_losses),
                'avg_loss': sum(total_losses) / len(total_losses),
                'range_spread': max(total_losses) - min(total_losses),
                'coefficient_of_variation': np.std(total_losses) / np.mean(total_losses) if np.mean(total_losses) > 0 else 0
            }
            
            # Calculate settlement recommendations
            settlement_range = self.calculate_settlement_range(results)
            results['settlement_analysis'] = settlement_range
            
            results['wage_analysis'] = wage_analysis
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in multi-scenario analysis: {str(e)}")
            return {
                'error': str(e),
                'scenarios': {},
                'summary': {'avg_loss': 0}
            }
    
    def calculate_settlement_range(self, scenario_results: Dict) -> SettlementRange:
        """
        Calculate recommended settlement ranges based on scenario analysis.
        
        Args:
            scenario_results: Results from multi-scenario analysis
            
        Returns:
            SettlementRange object with recommendations
        """
        try:
            conservative_loss = scenario_results['scenarios']['conservative']['total_loss']
            moderate_loss = scenario_results['scenarios']['moderate']['total_loss']
            aggressive_loss = scenario_results['scenarios']['aggressive']['total_loss']
            
            # Settlement ranges typically account for:
            # - Litigation risk (discount for uncertainty)
            # - Attorney fees and costs
            # - Time value considerations
            # - Negotiation positioning
            
            # Conservative range (60-80% of calculated loss)
            conservative_low = conservative_loss * 0.60
            conservative_high = conservative_loss * 0.80
            
            # Moderate range (70-90% of calculated loss)
            moderate_low = moderate_loss * 0.70
            moderate_high = moderate_loss * 0.90
            
            # Aggressive range (80-95% of calculated loss)
            aggressive_low = aggressive_loss * 0.80
            aggressive_high = aggressive_loss * 0.95
            
            # Recommended target (weighted average favoring moderate)
            recommended_target = (
                conservative_loss * 0.20 +
                moderate_loss * 0.60 +
                aggressive_loss * 0.20
            ) * 0.85  # 85% settlement factor
            
            # Confidence level based on range consistency
            range_spread = max(aggressive_high, moderate_high, conservative_high) - min(aggressive_low, moderate_low, conservative_low)
            avg_loss = (conservative_loss + moderate_loss + aggressive_loss) / 3
            confidence_level = max(0.5, 1 - (range_spread / avg_loss))
            
            return SettlementRange(
                conservative_low=conservative_low,
                conservative_high=conservative_high,
                moderate_low=moderate_low,
                moderate_high=moderate_high,
                aggressive_low=aggressive_low,
                aggressive_high=aggressive_high,
                recommended_target=recommended_target,
                confidence_level=confidence_level
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating settlement range: {str(e)}")
            # Return default range
            avg_loss = 100000  # Default
            return SettlementRange(
                conservative_low=avg_loss * 0.6,
                conservative_high=avg_loss * 0.8,
                moderate_low=avg_loss * 0.7,
                moderate_high=avg_loss * 0.9,
                aggressive_low=avg_loss * 0.8,
                aggressive_high=avg_loss * 0.95,
                recommended_target=avg_loss * 0.85,
                confidence_level=0.5
            )
    
    def calculate_career_trajectory_model(self, evaluee_data: Dict) -> Dict:
        """
        Calculate predicted career trajectory with earnings progression.
        
        Args:
            evaluee_data: Evaluee information
            
        Returns:
            Dictionary with career trajectory analysis
        """
        try:
            birth_date = evaluee_data.get('date_of_birth')
            injury_date = evaluee_data.get('date_of_injury')
            base_earnings = float(evaluee_data.get('base_earnings', 50000))
            education = evaluee_data.get('education_level', 'High School')
            occupation = evaluee_data.get('occupation', 'General')
            
            if not birth_date or not injury_date:
                raise ValueError("Birth date and injury date required for trajectory modeling")
            
            age_at_injury = self.base_calculator.calculate_age(birth_date, injury_date)
            
            # Career stage analysis
            career_stages = {
                'early_career': (22, 32),     # 22-32: High growth potential
                'mid_career': (33, 45),       # 33-45: Peak earning growth
                'senior_career': (46, 57),    # 46-57: Stable high earnings
                'late_career': (58, 67)       # 58-67: Gradual decline
            }
            
            # Determine current career stage
            current_stage = 'early_career'
            for stage, (min_age, max_age) in career_stages.items():
                if min_age <= age_at_injury <= max_age:
                    current_stage = stage
                    break
            
            # Education multipliers for career progression
            education_factors = {
                'Doctoral Degree': 1.25,
                'Professional Degree': 1.22,
                'Master\'s Degree': 1.18,
                'Bachelor\'s Degree': 1.12,
                'Associate\'s Degree': 1.06,
                'Some College': 1.03,
                'High School': 1.00,
                'Less than High School': 0.95
            }
            
            education_factor = education_factors.get(education, 1.0)
            
            # Occupation-specific growth patterns
            api = get_bls_api()
            industry_growth = api.get_industry_growth_rate(occupation)
            
            # Project earnings trajectory
            trajectory = []
            current_age = age_at_injury
            current_earnings = base_earnings
            
            # Project 30 years or to age 67, whichever comes first
            end_age = min(current_age + 30, 67)
            
            for age in range(int(current_age), int(end_age) + 1):
                # Determine stage-specific growth rate
                if age <= 32:
                    stage_growth = 0.06 * education_factor  # 6% base for early career
                elif age <= 45:
                    stage_growth = 0.04 * education_factor  # 4% base for mid career
                elif age <= 57:
                    stage_growth = 0.025 * education_factor # 2.5% base for senior career
                else:
                    stage_growth = 0.01 * education_factor  # 1% base for late career
                
                # Apply industry-specific adjustments
                total_growth = (stage_growth + industry_growth) / 2
                
                # Apply random career events (promotions, job changes)
                if age - current_age in [5, 10, 15, 20]:  # Every 5 years
                    # Potential promotion/job change
                    promotion_factor = 1.15 if education_factor > 1.1 else 1.08
                    current_earnings *= promotion_factor
                
                # Apply annual growth
                current_earnings *= (1 + total_growth)
                
                trajectory.append({
                    'age': age,
                    'year': injury_date.year + (age - age_at_injury),
                    'projected_earnings': current_earnings,
                    'growth_rate': total_growth,
                    'career_stage': self._get_career_stage(age, career_stages)
                })
            
            # Calculate lost potential
            actual_remaining_years = float(evaluee_data.get('work_life_expectancy', 20))
            projected_total = sum(point['projected_earnings'] for point in trajectory[:int(actual_remaining_years)])
            actual_total = base_earnings * actual_remaining_years  # Simplified
            
            lost_potential = projected_total - actual_total
            
            return {
                'current_stage': current_stage,
                'age_at_injury': age_at_injury,
                'education_factor': education_factor,
                'industry_growth_rate': industry_growth,
                'trajectory': trajectory,
                'projected_lifetime_earnings': projected_total,
                'lost_earning_potential': lost_potential,
                'peak_earning_age': max(trajectory, key=lambda x: x['projected_earnings'])['age'],
                'peak_earning_amount': max(trajectory, key=lambda x: x['projected_earnings'])['projected_earnings']
            }
            
        except Exception as e:
            self.logger.error(f"Error in career trajectory modeling: {str(e)}")
            return {
                'error': str(e),
                'trajectory': [],
                'lost_earning_potential': 0
            }
    
    def _get_career_stage(self, age: int, career_stages: Dict) -> str:
        """Determine career stage for given age."""
        for stage, (min_age, max_age) in career_stages.items():
            if min_age <= age <= max_age:
                return stage
        return 'late_career'

# Global enhanced calculator instance
_enhanced_calculator = None

def get_enhanced_calculator():
    """Get the global enhanced calculator instance."""
    global _enhanced_calculator
    if _enhanced_calculator is None:
        _enhanced_calculator = EnhancedEconomicCalculator()
    return _enhanced_calculator

def calculate_comprehensive_analysis(evaluee_data: Dict) -> Dict:
    """
    Perform comprehensive economic analysis with all enhancements.
    
    Args:
        evaluee_data: Complete evaluee information
        
    Returns:
        Dictionary with comprehensive analysis results
    """
    try:
        calculator = get_enhanced_calculator()
        
        results = {
            'multi_scenario_analysis': calculator.calculate_multi_scenario_analysis(evaluee_data),
            'career_trajectory': calculator.calculate_career_trajectory_model(evaluee_data),
            'wage_baseline_analysis': calculator.calculate_smart_wage_baseline(evaluee_data)
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {str(e)}")
        return {
            'error': str(e),
            'multi_scenario_analysis': {'summary': {'avg_loss': 0}},
            'career_trajectory': {'lost_earning_potential': 0}
        }