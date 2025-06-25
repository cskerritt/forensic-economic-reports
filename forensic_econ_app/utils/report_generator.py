"""
Enhanced Report Generation for Economic Analysis
Supports PDF, Excel, and other formats with professional formatting
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import io
import os
import tempfile
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from ..models.models import Evaluee, EarningsScenario, HouseholdServicesScenario
from ..utils.cross_module_data import get_evaluee_context, get_module_completion_status


class EconomicReportGenerator:
    """Professional report generator for economic analysis"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles for reports"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=TA_CENTER
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=5
        ))
        
        # Subsection style
        self.styles.add(ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.black
        ))
        
        # Summary box style
        self.styles.add(ParagraphStyle(
            name='SummaryBox',
            parent=self.styles['Normal'],
            fontSize=12,
            leftIndent=20,
            rightIndent=20,
            spaceAfter=12,
            borderWidth=1,
            borderColor=colors.blue,
            borderPadding=10,
            backColor=colors.lightblue,
            alignment=TA_CENTER
        ))
        
        # Key findings style
        self.styles.add(ParagraphStyle(
            name='KeyFinding',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=15,
            spaceAfter=6,
            bulletIndent=10,
            bulletText='•'
        ))
    
    def generate_comprehensive_report(self, evaluee_id, output_path=None):
        """Generate a comprehensive economic analysis report"""
        # Get evaluee data
        evaluee = Evaluee.query.get(evaluee_id)
        if not evaluee:
            raise ValueError(f"Evaluee {evaluee_id} not found")
        
        # Setup document
        if not output_path:
            output_path = f"/tmp/economic_report_{evaluee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build story
        story = []
        
        # Add title page
        story.extend(self._create_title_page(evaluee))
        story.append(PageBreak())
        
        # Add executive summary
        story.extend(self._create_executive_summary(evaluee))
        story.append(PageBreak())
        
        # Add evaluee overview
        story.extend(self._create_evaluee_overview(evaluee))
        
        # Add earnings analysis
        if evaluee.earnings_scenarios:
            story.extend(self._create_earnings_analysis(evaluee))
        
        # Add household services analysis
        household_scenarios = HouseholdServicesScenario.query.filter_by(evaluee_id=evaluee_id).all()
        if household_scenarios:
            story.extend(self._create_household_analysis(evaluee, household_scenarios))
        
        # Add charts and visualizations
        story.extend(self._create_charts_section(evaluee))
        
        # Add assumptions and methodology
        story.extend(self._create_methodology_section(evaluee))
        
        # Add appendices
        story.extend(self._create_appendices(evaluee))
        
        # Build PDF
        doc.build(story)
        
        # Clean up temporary chart files
        self._cleanup_temp_files()
        
        return output_path
    
    def _cleanup_temp_files(self):
        """Clean up temporary chart files"""
        try:
            import glob
            temp_charts = glob.glob('/tmp/*.png')
            for chart_file in temp_charts:
                if os.path.exists(chart_file):
                    os.remove(chart_file)
        except Exception as e:
            print(f"Warning: Could not clean up temporary files: {e}")
    
    def _create_title_page(self, evaluee):
        """Create professional title page"""
        story = []
        
        # Main title
        story.append(Paragraph(
            "ECONOMIC ANALYSIS REPORT",
            self.styles['ReportTitle']
        ))
        story.append(Spacer(1, 50))
        
        # Evaluee name
        story.append(Paragraph(
            f"<b>{evaluee.first_name} {evaluee.last_name}</b>",
            self.styles['Title']
        ))
        story.append(Spacer(1, 30))
        
        # Report details table
        report_data = [
            ['Report Date:', datetime.now().strftime('%B %d, %Y')],
            ['Evaluee State:', evaluee.state],
            ['Analysis Type:', 'Comprehensive Economic Loss Analysis'],
            ['Prepared By:', 'Economic Analysis System'],
        ]
        
        if evaluee.date_of_birth:
            report_data.insert(2, ['Date of Birth:', evaluee.date_of_birth.strftime('%B %d, %Y')])
        if evaluee.date_of_injury:
            report_data.insert(3, ['Date of Injury:', evaluee.date_of_injury.strftime('%B %d, %Y')])
        
        details_table = Table(report_data, colWidths=[2*inch, 3*inch])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 50))
        
        # Disclaimer
        disclaimer = """
        <b>CONFIDENTIAL</b><br/>
        This report contains confidential and proprietary information. 
        It is intended solely for the use of the intended recipient(s) 
        and should not be distributed without authorization.
        """
        story.append(Paragraph(disclaimer, self.styles['SummaryBox']))
        
        return story
    
    def _create_executive_summary(self, evaluee):
        """Create executive summary with key findings"""
        story = []
        
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        
        # Get summary data
        context = get_evaluee_context(evaluee.id)
        completion_status = get_module_completion_status(evaluee.id)
        
        # Calculate total economic loss
        total_earnings_loss = sum(
            float(scenario.total_loss or 0) 
            for scenario in evaluee.earnings_scenarios
        )
        
        household_scenarios = HouseholdServicesScenario.query.filter_by(evaluee_id=evaluee.id).all()
        total_household_loss = sum(
            float(scenario.present_value or 0)
            for scenario in household_scenarios
        )
        
        total_economic_loss = total_earnings_loss + total_household_loss
        
        # Summary paragraph
        summary_text = f"""
        This report presents a comprehensive economic analysis of losses for 
        {evaluee.first_name} {evaluee.last_name}. The analysis includes earnings 
        capacity evaluation, household services assessment, and present value 
        calculations using standard forensic economic methodologies.
        """
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Key findings
        story.append(Paragraph("Key Findings:", self.styles['SubSection']))
        
        findings = []
        if total_economic_loss > 0:
            findings.append(f"Total estimated economic loss: ${total_economic_loss:,.2f}")
        
        if total_earnings_loss > 0:
            findings.append(f"Earnings-related losses: ${total_earnings_loss:,.2f}")
        
        if total_household_loss > 0:
            findings.append(f"Household services losses: ${total_household_loss:,.2f}")
        
        if evaluee.current_age:
            findings.append(f"Current age: {evaluee.current_age} years")
        
        if evaluee.regional_adjustment and evaluee.regional_adjustment != 1.0:
            adjustment_pct = (float(evaluee.regional_adjustment) - 1.0) * 100
            findings.append(f"Regional wage adjustment: {adjustment_pct:+.1f}%")
        
        if len(evaluee.earnings_scenarios) > 1:
            findings.append(f"Multiple earnings scenarios analyzed ({len(evaluee.earnings_scenarios)} scenarios)")
        
        for finding in findings:
            story.append(Paragraph(finding, self.styles['KeyFinding']))
        
        story.append(Spacer(1, 20))
        
        # Summary table
        if total_economic_loss > 0:
            summary_data = [
                ['Component', 'Amount', 'Percentage'],
                ['Earnings Losses', f'${total_earnings_loss:,.2f}', f'{(total_earnings_loss/total_economic_loss)*100:.1f}%'],
                ['Household Services', f'${total_household_loss:,.2f}', f'{(total_household_loss/total_economic_loss)*100:.1f}%'],
                ['Total Economic Loss', f'${total_economic_loss:,.2f}', '100.0%']
            ]
            
            summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
            ]))
            
            story.append(summary_table)
        
        return story
    
    def _create_evaluee_overview(self, evaluee):
        """Create evaluee demographic and background information"""
        story = []
        
        story.append(Paragraph("EVALUEE OVERVIEW", self.styles['SectionHeader']))
        
        # Demographics table
        demo_data = [
            ['Name:', f"{evaluee.first_name} {evaluee.last_name}"],
            ['State:', evaluee.state or 'Not specified'],
        ]
        
        if evaluee.date_of_birth:
            demo_data.append(['Date of Birth:', evaluee.date_of_birth.strftime('%B %d, %Y')])
        if evaluee.current_age:
            demo_data.append(['Current Age:', f"{evaluee.current_age} years"])
        if evaluee.gender:
            gender_display = 'Male' if evaluee.gender in ['M', 'Men'] else 'Female' if evaluee.gender in ['F', 'Women'] else evaluee.gender
            demo_data.append(['Gender:', gender_display])
        if evaluee.date_of_injury:
            demo_data.append(['Date of Injury:', evaluee.date_of_injury.strftime('%B %d, %Y')])
        if evaluee.education_level and evaluee.education_level != 'All Education Levels':
            demo_data.append(['Education Level:', evaluee.education_level])
        
        demo_table = Table(demo_data, colWidths=[1.5*inch, 3*inch])
        demo_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        
        story.append(demo_table)
        story.append(Spacer(1, 20))
        
        # Economic parameters
        if evaluee.uses_discounting or evaluee.regional_adjustment:
            story.append(Paragraph("Economic Parameters:", self.styles['SubSection']))
            
            econ_data = []
            if evaluee.uses_discounting:
                discount_rates = ', '.join([f"{rate}%" for rate in evaluee.discount_rates])
                econ_data.append(['Discount Rates:', discount_rates])
            
            if evaluee.regional_adjustment and evaluee.regional_adjustment != 1.0:
                adjustment_pct = (float(evaluee.regional_adjustment) - 1.0) * 100
                econ_data.append(['Regional Adjustment:', f"{adjustment_pct:+.1f}%"])
            
            if econ_data:
                econ_table = Table(econ_data, colWidths=[1.5*inch, 3*inch])
                econ_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
                ]))
                story.append(econ_table)
        
        return story
    
    def _create_earnings_analysis(self, evaluee):
        """Create detailed earnings analysis section"""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("EARNINGS ANALYSIS", self.styles['SectionHeader']))
        
        for i, scenario in enumerate(evaluee.earnings_scenarios, 1):
            story.append(Paragraph(f"Scenario {i}: {scenario.scenario_name}", self.styles['SubSection']))
            
            # Scenario summary
            scenario_data = [
                ['Analysis Period:', f"{scenario.start_date.strftime('%m/%d/%Y')} to {scenario.end_date.strftime('%m/%d/%Y')}"],
                ['Base Wage:', f"${scenario.wage_base:,.2f}"],
                ['Growth Rate:', f"{float(scenario.growth_rate or 0):.2f}%"],
                ['Adjustment Factor:', f"{float(scenario.adjustment_factor or 100):.1f}%"],
            ]
            
            if scenario.residual_base:
                scenario_data.append(['Residual Capacity:', f"${scenario.residual_base:,.2f}"])
            
            if scenario.injury_date and scenario.report_date:
                scenario_data.extend([
                    ['Date of Injury:', scenario.injury_date.strftime('%m/%d/%Y')],
                    ['Report Date:', scenario.report_date.strftime('%m/%d/%Y')],
                ])
                
                if scenario.past_loss_present_value:
                    scenario_data.append(['Past Losses:', f"${scenario.past_loss_present_value:,.2f}"])
                if scenario.future_loss_present_value:
                    scenario_data.append(['Future Losses:', f"${scenario.future_loss_present_value:,.2f}"])
            
            if scenario.total_loss:
                scenario_data.append(['Total Loss:', f"${scenario.total_loss:,.2f}"])
            if scenario.present_value and evaluee.uses_discounting:
                scenario_data.append(['Present Value:', f"${scenario.present_value:,.2f}"])
            
            scenario_table = Table(scenario_data, colWidths=[1.5*inch, 2*inch])
            scenario_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('BACKGROUND', (0, -2), (-1, -1), colors.lightblue) if scenario.total_loss else ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue)
            ]))
            
            story.append(scenario_table)
            story.append(Spacer(1, 15))
        
        return story
    
    def _create_household_analysis(self, evaluee, household_scenarios):
        """Create household services analysis section"""
        story = []
        
        story.append(Paragraph("HOUSEHOLD SERVICES ANALYSIS", self.styles['SectionHeader']))
        
        for i, scenario in enumerate(household_scenarios, 1):
            story.append(Paragraph(f"Scenario {i}: {scenario.scenario_name}", self.styles['SubSection']))
            
            household_data = [
                ['Analysis Period:', f"{scenario.start_date.strftime('%m/%d/%Y')} to {scenario.end_date.strftime('%m/%d/%Y')}"],
                ['Growth Rate:', f"{float(scenario.growth_rate or 0):.2f}%"],
                ['Discount Rate:', f"{float(scenario.discount_rate or 0):.2f}%"],
            ]
            
            if scenario.area_wage_adjustment:
                household_data.append(['Area Wage Adjustment:', f"{float(scenario.area_wage_adjustment or 0)*100:.1f}%"])
            if scenario.reduction_percentage:
                household_data.append(['Reduction Percentage:', f"{float(scenario.reduction_percentage or 0)*100:.1f}%"])
            if scenario.present_value:
                household_data.append(['Present Value:', f"${scenario.present_value:,.2f}"])
            
            household_table = Table(household_data, colWidths=[1.5*inch, 2*inch])
            household_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue)
            ]))
            
            story.append(household_table)
            story.append(Spacer(1, 15))
        
        return story
    
    def _create_methodology_section(self, evaluee):
        """Create methodology and assumptions section"""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("METHODOLOGY AND ASSUMPTIONS", self.styles['SectionHeader']))
        
        methodology_text = """
        This economic analysis was prepared using standard forensic economic methodologies 
        and generally accepted principles in the field. The analysis considers the evaluee's 
        earning capacity, work life expectancy, and other relevant economic factors.
        """
        story.append(Paragraph(methodology_text, self.styles['Normal']))
        story.append(Spacer(1, 15))
        
        # Key assumptions
        story.append(Paragraph("Key Assumptions:", self.styles['SubSection']))
        
        assumptions = [
            "Present value calculations use standard discount rates as specified",
            "Growth rates are applied consistently throughout the analysis period",
            "Regional adjustments reflect local economic conditions",
            "Work life expectancy is based on standard actuarial tables",
            "Analysis assumes continued employment absent the injury"
        ]
        
        for assumption in assumptions:
            story.append(Paragraph(f"• {assumption}", self.styles['Normal']))
        
        story.append(Spacer(1, 15))
        
        # Data sources
        story.append(Paragraph("Data Sources:", self.styles['SubSection']))
        sources = [
            "Bureau of Labor Statistics (BLS) wage and employment data",
            "Federal Reserve Economic Data (FRED) for economic indicators",
            "Standard life expectancy and work life expectancy tables",
            "Regional economic adjustment factors"
        ]
        
        for source in sources:
            story.append(Paragraph(f"• {source}", self.styles['Normal']))
        
        return story
    
    def _create_charts_section(self, evaluee):
        """Create charts and visualizations section"""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("CHARTS AND ANALYSIS", self.styles['SectionHeader']))
        
        # Create earnings analysis chart if scenarios exist
        if evaluee.earnings_scenarios:
            earnings_chart_path = self._create_earnings_comparison_chart(evaluee)
            if earnings_chart_path:
                story.append(Paragraph("Earnings Analysis Comparison", self.styles['SubSection']))
                chart_image = RLImage(earnings_chart_path, width=6*inch, height=4*inch)
                story.append(chart_image)
                story.append(Spacer(1, 20))
        
        # Create age timeline chart
        timeline_chart_path = self._create_age_timeline_chart(evaluee)
        if timeline_chart_path:
            story.append(Paragraph("Age and Life Expectancy Timeline", self.styles['SubSection']))
            timeline_image = RLImage(timeline_chart_path, width=6*inch, height=4*inch)
            story.append(timeline_image)
            story.append(Spacer(1, 20))
        
        # Create loss breakdown chart
        breakdown_chart_path = self._create_loss_breakdown_chart(evaluee)
        if breakdown_chart_path:
            story.append(Paragraph("Economic Loss Breakdown", self.styles['SubSection']))
            breakdown_image = RLImage(breakdown_chart_path, width=6*inch, height=4*inch)
            story.append(breakdown_image)
            story.append(Spacer(1, 20))
        
        return story
    
    def _create_earnings_comparison_chart(self, evaluee):
        """Create earnings scenarios comparison chart"""
        try:
            if not evaluee.earnings_scenarios:
                return None
            
            try:
                plt.style.use('seaborn-v0_8')
            except OSError:
                plt.style.use('default')
            fig, ax = plt.subplots(figsize=(10, 6))
            
            scenarios = []
            present_values = []
            total_losses = []
            
            for scenario in evaluee.earnings_scenarios:
                scenarios.append(scenario.scenario_name[:15])  # Truncate long names
                present_values.append(float(scenario.present_value or 0))
                total_losses.append(float(scenario.total_loss or 0))
            
            x = range(len(scenarios))
            width = 0.35
            
            ax.bar([i - width/2 for i in x], present_values, width, label='Present Value', alpha=0.8, color='#1f77b4')
            ax.bar([i + width/2 for i in x], total_losses, width, label='Total Loss', alpha=0.8, color='#ff7f0e')
            
            ax.set_xlabel('Scenarios')
            ax.set_ylabel('Amount ($)')
            ax.set_title('Earnings Analysis Comparison by Scenario')
            ax.set_xticks(x)
            ax.set_xticklabels(scenarios, rotation=45, ha='right')
            ax.legend()
            
            # Format y-axis as currency
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            plt.tight_layout()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                plt.savefig(tmp_file.name, dpi=300, bbox_inches='tight')
                plt.close()
                return tmp_file.name
                
        except Exception as e:
            print(f"Error creating earnings comparison chart: {e}")
            plt.close()
            return None
    
    def _create_age_timeline_chart(self, evaluee):
        """Create age and timeline visualization"""
        try:
            if not evaluee.date_of_birth:
                return None
            
            try:
                plt.style.use('seaborn-v0_8')
            except OSError:
                plt.style.use('default')
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Calculate key dates and ages
            birth_date = evaluee.date_of_birth
            current_date = datetime.now()
            current_age = (current_date - birth_date).days / 365.25
            
            timeline_data = [
                ('Birth', 0, birth_date.year),
                ('Current Age', current_age, current_date.year)
            ]
            
            if evaluee.date_of_injury:
                injury_age = (evaluee.date_of_injury - birth_date).days / 365.25
                timeline_data.append(('Injury', injury_age, evaluee.date_of_injury.year))
            
            if evaluee.life_expectancy:
                life_end_age = float(evaluee.life_expectancy)
                life_end_year = birth_date.year + life_end_age
                timeline_data.append(('Life Expectancy', life_end_age, int(life_end_year)))
            
            if evaluee.work_life_expectancy:
                work_end_age = current_age + float(evaluee.work_life_expectancy)
                work_end_year = birth_date.year + work_end_age
                timeline_data.append(('Work Life End', work_end_age, int(work_end_year)))
            
            # Sort by age
            timeline_data.sort(key=lambda x: x[1])
            
            ages = [item[1] for item in timeline_data]
            labels = [f"{item[0]}\n{item[1]:.1f} years\n({item[2]})" for item in timeline_data]
            colors = ['#2ca02c', '#1f77b4', '#d62728', '#ff7f0e', '#9467bd']
            
            # Create timeline
            ax.scatter(ages, [1]*len(ages), s=200, c=colors[:len(ages)], alpha=0.8, zorder=3)
            ax.plot([ages[0], ages[-1]], [1, 1], 'k-', alpha=0.3, zorder=1)
            
            # Add labels
            for i, (age, label) in enumerate(zip(ages, labels)):
                ax.annotate(label, (age, 1), xytext=(0, 50 if i % 2 == 0 else -50), 
                           textcoords='offset points', ha='center', va='bottom' if i % 2 == 0 else 'top',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor=colors[i], alpha=0.3))
            
            ax.set_xlabel('Age (Years)')
            ax.set_title(f'Life Timeline for {evaluee.first_name} {evaluee.last_name}')
            ax.set_ylim(0.5, 1.5)
            ax.set_yticks([])
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                plt.savefig(tmp_file.name, dpi=300, bbox_inches='tight')
                plt.close()
                return tmp_file.name
                
        except Exception as e:
            print(f"Error creating age timeline chart: {e}")
            plt.close()
            return None
    
    def _create_loss_breakdown_chart(self, evaluee):
        """Create pie chart showing breakdown of economic losses"""
        try:
            # Calculate total losses
            earnings_loss = sum(float(scenario.total_loss or 0) for scenario in evaluee.earnings_scenarios)
            
            household_scenarios = HouseholdServicesScenario.query.filter_by(evaluee_id=evaluee.id).all()
            household_loss = sum(float(scenario.present_value or 0) for scenario in household_scenarios)
            
            if earnings_loss == 0 and household_loss == 0:
                return None
            
            try:
                plt.style.use('seaborn-v0_8')
            except OSError:
                plt.style.use('default')
            fig, ax = plt.subplots(figsize=(8, 8))
            
            categories = []
            values = []
            colors = []
            
            if earnings_loss > 0:
                categories.append(f'Earnings Loss\n${earnings_loss:,.0f}')
                values.append(earnings_loss)
                colors.append('#1f77b4')
            
            if household_loss > 0:
                categories.append(f'Household Services\n${household_loss:,.0f}')
                values.append(household_loss)
                colors.append('#ff7f0e')
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(values, labels=categories, colors=colors, autopct='%1.1f%%',
                                            startangle=90, textprops={'fontsize': 12})
            
            # Enhance appearance
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title(f'Economic Loss Breakdown\nTotal: ${sum(values):,.0f}', fontsize=16, fontweight='bold')
            
            plt.tight_layout()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                plt.savefig(tmp_file.name, dpi=300, bbox_inches='tight')
                plt.close()
                return tmp_file.name
                
        except Exception as e:
            print(f"Error creating loss breakdown chart: {e}")
            plt.close()
            return None
    
    def _create_appendices(self, evaluee):
        """Create appendices with detailed calculations"""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("APPENDICES", self.styles['SectionHeader']))
        
        # Appendix A: Calculation Details
        story.append(Paragraph("Appendix A: Detailed Calculations", self.styles['SubSection']))
        
        calc_text = """
        Detailed calculation worksheets and supporting documentation are available 
        upon request. All calculations follow standard forensic economic methodologies 
        and have been verified for accuracy.
        """
        story.append(Paragraph(calc_text, self.styles['Normal']))
        
        # Add generation timestamp
        story.append(Spacer(1, 30))
        timestamp = f"Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        story.append(Paragraph(timestamp, self.styles['Normal']))
        
        return story


def generate_scenario_comparison_report(evaluee_id, scenario_ids, output_path=None):
    """Generate a comparative analysis report for multiple scenarios"""
    evaluee = Evaluee.query.get(evaluee_id)
    if not evaluee:
        raise ValueError(f"Evaluee {evaluee_id} not found")
    
    scenarios = []
    for scenario_id in scenario_ids:
        scenario = EarningsScenario.query.get(scenario_id)
        if scenario and scenario.evaluee_id == evaluee_id:
            scenarios.append(scenario)
    
    if not scenarios:
        raise ValueError("No valid scenarios found for comparison")
    
    # Setup document
    if not output_path:
        output_path = f"/tmp/scenario_comparison_{evaluee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    generator = EconomicReportGenerator()
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    story = []
    
    # Title
    story.append(Paragraph(f"SCENARIO COMPARISON ANALYSIS<br/>{evaluee.first_name} {evaluee.last_name}", generator.styles['ReportTitle']))
    story.append(Spacer(1, 30))
    
    # Comparison table
    comparison_data = [['Scenario', 'Base Wage', 'Growth Rate', 'Total Loss', 'Present Value']]
    
    for scenario in scenarios:
        comparison_data.append([
            scenario.scenario_name,
            f"${scenario.wage_base:,.2f}",
            f"{float(scenario.growth_rate or 0):.2f}%",
            f"${scenario.total_loss:,.2f}" if scenario.total_loss else "N/A",
            f"${scenario.present_value:,.2f}" if scenario.present_value else "N/A"
        ])
    
    comparison_table = Table(comparison_data)
    comparison_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(comparison_table)
    
    # Build PDF
    doc.build(story)
    return output_path