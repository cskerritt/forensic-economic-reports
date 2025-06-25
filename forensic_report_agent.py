#!/usr/bin/env python3
"""
Forensic Economic Report Writing Agent

This AI agent automatically generates comprehensive forensic economic reports
by integrating with existing economic analysis tools and applying professional
forensic writing standards.
"""

import os
import json
import sqlite3
import argparse
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, date
import openai
from anthropic import Anthropic
from dataclasses import dataclass, asdict


@dataclass
class EvalueeData:
    """Data structure for evaluee information."""
    name: str
    date_of_birth: str
    date_of_injury: str
    gender: str
    age_at_injury: float
    current_age: float
    education_level: str
    occupation: str
    pre_injury_earnings: float
    post_injury_capacity: str
    life_expectancy: float
    work_life_expectancy: float


@dataclass
class EconomicCalculations:
    """Data structure for economic loss calculations."""
    present_value_lost_earnings: float
    present_value_fringe_benefits: float
    present_value_household_services: float
    present_value_medical_costs: float
    total_economic_loss: float
    discount_rate: float
    growth_rate: float
    scenarios: List[Dict]


class DatabaseConnector:
    """Connects to existing economic analysis database to extract data."""
    
    def __init__(self, db_path: str = "/Users/chrisskerritt/EconomicAnalysis/instance/app.db"):
        self.db_path = db_path
    
    def get_evaluee_data(self, evaluee_id: int) -> Optional[EvalueeData]:
        """Extract evaluee data from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get evaluee basic info
            cursor.execute("""
                SELECT name, date_of_birth, date_of_injury, gender, 
                       age_at_injury, education_level, occupation, 
                       pre_injury_earnings, post_injury_capacity
                FROM evaluees WHERE id = ?
            """, (evaluee_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Calculate current age and life expectancies (simplified)
            today = date.today()
            birth_date = datetime.strptime(row[1], '%Y-%m-%d').date()
            current_age = (today - birth_date).days / 365.25
            
            # These would come from your worklife/demographics calculations
            life_expectancy = 78.0  # Default - would pull from calculations
            work_life_expectancy = 65.0  # Default - would pull from calculations
            
            return EvalueeData(
                name=row[0],
                date_of_birth=row[1],
                date_of_injury=row[2],
                gender=row[3],
                age_at_injury=row[4],
                current_age=current_age,
                education_level=row[5],
                occupation=row[6],
                pre_injury_earnings=row[7],
                post_injury_capacity=row[8],
                life_expectancy=life_expectancy,
                work_life_expectancy=work_life_expectancy
            )
            
        except Exception as e:
            print(f"Database error: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_economic_calculations(self, evaluee_id: int) -> Optional[EconomicCalculations]:
        """Extract economic calculations from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get earnings scenarios
            cursor.execute("""
                SELECT scenario_name, annual_earnings, growth_rate, 
                       present_value, discount_rate
                FROM earnings_scenarios WHERE evaluee_id = ?
            """, (evaluee_id,))
            
            scenarios = []
            total_earnings_pv = 0
            discount_rate = 3.0  # Default
            growth_rate = 2.5   # Default
            
            for row in cursor.fetchall():
                scenario = {
                    'name': row[0],
                    'annual_earnings': row[1],
                    'growth_rate': row[2],
                    'present_value': row[3],
                    'discount_rate': row[4]
                }
                scenarios.append(scenario)
                total_earnings_pv += row[3] if row[3] else 0
                if row[4]:
                    discount_rate = row[4]
                if row[2]:
                    growth_rate = row[2]
            
            # Get fringe benefits, household services, medical costs
            # (These would be pulled from respective tables in your system)
            fringe_benefits_pv = total_earnings_pv * 0.25  # Estimate
            household_services_pv = 150000  # Estimate
            medical_costs_pv = 500000      # Estimate
            
            total_loss = total_earnings_pv + fringe_benefits_pv + household_services_pv + medical_costs_pv
            
            return EconomicCalculations(
                present_value_lost_earnings=total_earnings_pv,
                present_value_fringe_benefits=fringe_benefits_pv,
                present_value_household_services=household_services_pv,
                present_value_medical_costs=medical_costs_pv,
                total_economic_loss=total_loss,
                discount_rate=discount_rate,
                growth_rate=growth_rate,
                scenarios=scenarios
            )
            
        except Exception as e:
            print(f"Economic calculations error: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()


class ForensicReportAgent:
    """Main AI agent for generating forensic economic reports."""
    
    def __init__(self, api_provider: str = "openai", model: str = None):
        self.api_provider = api_provider.lower()
        self.db = DatabaseConnector()
        
        # Set default models
        if model is None:
            self.model = "gpt-4-turbo" if api_provider == "openai" else "claude-3-5-sonnet-20241022"
        else:
            self.model = model
            
        # Initialize API client
        self._initialize_api_client()
        
        # Load forensic writing style guide
        self.style_guide = self._load_forensic_style_guide()
    
    def _initialize_api_client(self):
        """Initialize the appropriate API client."""
        if self.api_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
            self.client = openai.OpenAI(api_key=api_key)
        
        elif self.api_provider == "claude":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable.")
            self.client = Anthropic(api_key=api_key)
        
        else:
            raise ValueError("Supported providers: 'openai' or 'claude'")
    
    def _load_forensic_style_guide(self) -> str:
        """Load comprehensive style guide for forensic economic reports."""
        return """
FORENSIC ECONOMIC REPORT WRITING STYLE GUIDE:

PROFESSIONAL STANDARDS:
- Objective, analytical tone with clear methodology
- Third-person perspective maintaining professional distance
- Precise financial and economic terminology
- Comprehensive documentation of assumptions and sources
- Clear presentation of calculations and reasoning

REPORT STRUCTURE:
1. Executive Summary
2. Background and Assignment
3. Evaluee Profile and Injury Impact
4. Economic Methodology and Assumptions
5. Earnings Loss Analysis
6. Fringe Benefits Analysis
7. Household Services Analysis
8. Medical Cost Projections
9. Summary of Economic Losses
10. Conclusions and Limitations

LANGUAGE PATTERNS:
- "Based on the available information..."
- "Economic analysis indicates..."
- "Using established methodology..."
- "Present value calculations show..."
- "Conservative estimates suggest..."
- "Industry standards indicate..."

CALCULATION PRESENTATION:
- Present value calculations with clear discount rates
- Multiple scenarios (conservative, moderate, aggressive)
- Detailed assumption explanations
- Source citations for all data points
- Sensitivity analysis where appropriate

PROFESSIONAL QUALIFIERS:
- "Based on available documentation"
- "Using industry-standard methodologies"
- "Conservative estimates indicate"
- "Analysis suggests"
- "Professional judgment indicates"
"""
    
    def generate_report_section(self, section_type: str, data: Dict, context: str = "") -> str:
        """Generate a specific section of the forensic economic report."""
        
        system_prompt = f"""You are an expert forensic economist writing a professional economic loss report. 
Generate a {section_type} section that is thorough, analytical, and follows forensic economic standards.

{self.style_guide}

CRITICAL REQUIREMENTS:
1. Use professional, objective language appropriate for legal proceedings
2. Include specific calculations and methodologies
3. Cite assumptions and sources
4. Present multiple scenarios where appropriate
5. Maintain conservative, defensible positions
6. Include present value calculations with clear discount rates

Section Type: {section_type}
Context: {context}

Data provided:"""

        user_prompt = f"""Generate the {section_type} section using this data:

{json.dumps(data, indent=2, default=str)}

Provide a comprehensive, professional analysis appropriate for a forensic economic report."""

        if self.api_provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )
            return response.choices[0].message.content.strip()
        
        elif self.api_provider == "claude":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.2,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text.strip()
    
    def generate_complete_report(self, evaluee_id: int, case_details: Dict = None) -> str:
        """Generate a complete forensic economic report."""
        
        # Extract data from database
        evaluee_data = self.db.get_evaluee_data(evaluee_id)
        economic_data = self.db.get_economic_calculations(evaluee_id)
        
        if not evaluee_data or not economic_data:
            raise ValueError(f"Could not retrieve complete data for evaluee ID {evaluee_id}")
        
        # Prepare data for report generation
        report_data = {
            'evaluee': asdict(evaluee_data),
            'economics': asdict(economic_data),
            'case_details': case_details or {},
            'report_date': datetime.now().strftime('%B %d, %Y'),
            'economist_name': 'Christopher Skerritt, Ph.D.'  # Default - make configurable
        }
        
        # Generate each section
        sections = {}
        
        print("Generating Executive Summary...")
        sections['executive_summary'] = self.generate_report_section(
            'Executive Summary', report_data, 
            'Brief overview of case and total economic loss'
        )
        
        print("Generating Background and Assignment...")
        sections['background'] = self.generate_report_section(
            'Background and Assignment', report_data,
            'Case background and scope of economic analysis'
        )
        
        print("Generating Evaluee Profile...")
        sections['evaluee_profile'] = self.generate_report_section(
            'Evaluee Profile and Injury Impact', report_data,
            'Demographics, education, work history, and injury impact'
        )
        
        print("Generating Methodology...")
        sections['methodology'] = self.generate_report_section(
            'Economic Methodology and Assumptions', report_data,
            'Explanation of economic principles and calculation methods'
        )
        
        print("Generating Earnings Analysis...")
        sections['earnings_analysis'] = self.generate_report_section(
            'Earnings Loss Analysis', report_data,
            'Detailed analysis of lost earnings with present value calculations'
        )
        
        print("Generating Fringe Benefits Analysis...")
        sections['fringe_analysis'] = self.generate_report_section(
            'Fringe Benefits Analysis', report_data,
            'Analysis of lost employment benefits and their value'
        )
        
        print("Generating Household Services Analysis...")
        sections['household_analysis'] = self.generate_report_section(
            'Household Services Analysis', report_data,
            'Value of lost household and personal services'
        )
        
        print("Generating Medical Cost Analysis...")
        sections['medical_analysis'] = self.generate_report_section(
            'Medical Cost Projections', report_data,
            'Present value of future medical and care costs'
        )
        
        print("Generating Summary...")
        sections['summary'] = self.generate_report_section(
            'Summary of Economic Losses', report_data,
            'Comprehensive summary of all economic loss components'
        )
        
        print("Generating Conclusions...")
        sections['conclusions'] = self.generate_report_section(
            'Conclusions and Limitations', report_data,
            'Professional conclusions and methodological limitations'
        )
        
        # Compile complete report
        complete_report = self._compile_complete_report(sections, report_data)
        
        return complete_report
    
    def _compile_complete_report(self, sections: Dict[str, str], data: Dict) -> str:
        """Compile all sections into a complete formatted report."""
        
        report_header = f"""
FORENSIC ECONOMIC ANALYSIS REPORT

Evaluee: {data['evaluee']['name']}
Date of Birth: {data['evaluee']['date_of_birth']}
Date of Injury: {data['evaluee']['date_of_injury']}
Report Date: {data['report_date']}
Economist: {data['economist_name']}

{'='*80}
"""
        
        complete_report = report_header
        
        section_order = [
            ('EXECUTIVE SUMMARY', 'executive_summary'),
            ('BACKGROUND AND ASSIGNMENT', 'background'),
            ('EVALUEE PROFILE AND INJURY IMPACT', 'evaluee_profile'),
            ('ECONOMIC METHODOLOGY AND ASSUMPTIONS', 'methodology'),
            ('EARNINGS LOSS ANALYSIS', 'earnings_analysis'),
            ('FRINGE BENEFITS ANALYSIS', 'fringe_analysis'),
            ('HOUSEHOLD SERVICES ANALYSIS', 'household_analysis'),
            ('MEDICAL COST PROJECTIONS', 'medical_analysis'),
            ('SUMMARY OF ECONOMIC LOSSES', 'summary'),
            ('CONCLUSIONS AND LIMITATIONS', 'conclusions')
        ]
        
        for title, key in section_order:
            complete_report += f"\n\n{title}\n{'-' * len(title)}\n\n"
            complete_report += sections[key]
        
        return complete_report
    
    def save_report(self, report_content: str, evaluee_name: str, output_dir: str = "reports") -> str:
        """Save the generated report to a file."""
        
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(exist_ok=True)
        
        # Generate filename
        safe_name = "".join(c for c in evaluee_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_name}_Economic_Report_{timestamp}.txt"
        filepath = Path(output_dir) / filename
        
        # Save report
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(filepath)


def main():
    parser = argparse.ArgumentParser(description="Generate forensic economic reports using AI")
    parser.add_argument("--evaluee-id", type=int, required=True,
                      help="Database ID of the evaluee")
    parser.add_argument("--provider", choices=["openai", "claude"], default="openai",
                      help="AI provider to use")
    parser.add_argument("--model", help="Specific model to use")
    parser.add_argument("--output-dir", default="reports",
                      help="Output directory for generated reports")
    parser.add_argument("--case-details", 
                      help="JSON file with additional case details")
    
    args = parser.parse_args()
    
    try:
        # Load case details if provided
        case_details = None
        if args.case_details:
            with open(args.case_details, 'r') as f:
                case_details = json.load(f)
        
        # Initialize agent
        agent = ForensicReportAgent(args.provider, args.model)
        
        # Generate report
        print(f"Generating forensic economic report for evaluee ID {args.evaluee_id}...")
        report = agent.generate_complete_report(args.evaluee_id, case_details)
        
        # Get evaluee name for filename
        evaluee_data = agent.db.get_evaluee_data(args.evaluee_id)
        evaluee_name = evaluee_data.name if evaluee_data else f"Evaluee_{args.evaluee_id}"
        
        # Save report
        filepath = agent.save_report(report, evaluee_name, args.output_dir)
        
        print(f"\nReport generated successfully!")
        print(f"Saved to: {filepath}")
        print(f"Report length: {len(report)} characters")
        
        # Display preview
        print(f"\nReport Preview (first 500 characters):")
        print("-" * 50)
        print(report[:500] + "..." if len(report) > 500 else report)
        
    except Exception as e:
        print(f"Error generating report: {e}")


if __name__ == "__main__":
    main()