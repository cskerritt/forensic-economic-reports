"""
Life Care Plan Export Functionality

Adapted from mcp_streamlit exporters.py for Flask integration.
Provides Excel and Word document export capabilities for life care plans.
"""

import os
import io
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import logging

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import LineChart, Reference
from openpyxl.utils import get_column_letter

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.shared import OxmlElement, qn

from ..models.life_care_plan import LifeCarePlan, LCPScenario
from .life_care_calculator import LifeCarePlanCalculator, ScenarioResults

logger = logging.getLogger(__name__)


class LifeCarePlanExcelExporter:
    """Export life care plan data to Excel format."""
    
    def __init__(self, plan: LifeCarePlan):
        self.plan = plan
        self.evaluee = plan.evaluee
        
    def export_plan(self, scenario_results: List[ScenarioResults], 
                   output_path: Optional[str] = None) -> bytes:
        """
        Export complete life care plan to Excel.
        
        Args:
            scenario_results: List of calculated scenario results
            output_path: Optional file path to save to
            
        Returns:
            Excel file content as bytes
        """
        wb = Workbook()
        
        # Remove default sheet
        default_sheet = wb.active
        wb.remove(default_sheet)
        
        # Create sheets
        self._create_summary_sheet(wb, scenario_results)
        
        for results in scenario_results:
            self._create_scenario_sheet(wb, results)
        
        self._create_plan_details_sheet(wb)
        self._create_evaluee_sheet(wb)
        
        # Save to bytes or file
        if output_path:
            wb.save(output_path)
            with open(output_path, 'rb') as f:
                return f.read()
        else:
            output = io.BytesIO()
            wb.save(output)
            return output.getvalue()
    
    def _create_summary_sheet(self, wb: Workbook, scenario_results: List[ScenarioResults]):
        """Create summary comparison sheet."""
        ws = wb.create_sheet("Summary", 0)
        
        # Title
        ws['A1'] = f"Life Care Plan Summary - {self.evaluee.full_name}"
        ws['A1'].font = Font(size=16, bold=True)
        ws.merge_cells('A1:G1')
        
        # Plan info
        ws['A3'] = "Plan:"
        ws['B3'] = self.plan.plan_name
        ws['A4'] = "Date:"
        ws['B4'] = datetime.now().strftime('%B %d, %Y')
        ws['A5'] = "Evaluee:"
        ws['B5'] = self.evaluee.full_name
        
        # Scenario comparison
        if scenario_results:
            ws['A7'] = "Scenario Comparison"
            ws['A7'].font = Font(size=14, bold=True)
            
            headers = ['Scenario', 'Present Value', 'Total Cost', 'Services', 'First Year Cost']
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=8, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            
            for row, results in enumerate(scenario_results, 9):
                ws.cell(row=row, column=1, value=results.scenario_name)
                ws.cell(row=row, column=2, value=float(results.present_value))
                ws.cell(row=row, column=3, value=float(results.total_cost))
                ws.cell(row=row, column=4, value=len(results.service_calculations))
                
                # Calculate first year cost
                first_year_cost = sum(
                    calc.first_year_cost for calc in results.service_calculations
                )
                ws.cell(row=row, column=5, value=float(first_year_cost))
            
            # Format currency columns
            for row in range(9, 9 + len(scenario_results)):
                for col in [2, 3, 5]:
                    ws.cell(row=row, column=col).number_format = '"$"#,##0.00'
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def _create_scenario_sheet(self, wb: Workbook, results: ScenarioResults):
        """Create detailed sheet for a scenario."""
        ws = wb.create_sheet(f"Scenario - {results.scenario_name}")
        
        # Title
        ws['A1'] = f"Scenario: {results.scenario_name}"
        ws['A1'].font = Font(size=14, bold=True)
        
        # Summary totals
        ws['A3'] = "Present Value:"
        ws['B3'] = float(results.present_value)
        ws['B3'].number_format = '"$"#,##0.00'
        ws['B3'].font = Font(bold=True)
        
        ws['A4'] = "Total Cost:"
        ws['B4'] = float(results.total_cost)
        ws['B4'].number_format = '"$"#,##0.00'
        
        ws['A5'] = "Number of Services:"
        ws['B5'] = len(results.service_calculations)
        
        # Service details
        ws['A7'] = "Service Details"
        ws['A7'].font = Font(size=12, bold=True)
        
        headers = ['Service Name', 'Present Value', 'Total Cost', 'First Year Cost', 'Category']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=8, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        for row, calc in enumerate(results.service_calculations, 9):
            ws.cell(row=row, column=1, value=calc.service_name)
            ws.cell(row=row, column=2, value=float(calc.present_value))
            ws.cell(row=row, column=3, value=float(calc.total_cost))
            ws.cell(row=row, column=4, value=float(calc.first_year_cost))
            # Note: We'd need to add category to ServiceCalculation if needed
            ws.cell(row=row, column=5, value="")
        
        # Format currency columns
        for row in range(9, 9 + len(results.service_calculations)):
            for col in [2, 3, 4]:
                ws.cell(row=row, column=col).number_format = '"$"#,##0.00'
        
        # Category breakdown
        if results.category_totals:
            start_row = 9 + len(results.service_calculations) + 3
            ws.cell(row=start_row, column=1, value="Category Breakdown")
            ws.cell(row=start_row, column=1).font = Font(size=12, bold=True)
            
            headers = ['Category', 'Present Value', 'Percentage']
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=start_row + 1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            
            for row, (category, amount) in enumerate(results.category_totals.items(), start_row + 2):
                ws.cell(row=row, column=1, value=category)
                ws.cell(row=row, column=2, value=float(amount))
                ws.cell(row=row, column=3, value=float(amount) / float(results.present_value) * 100)
            
            # Format currency and percentage
            for row in range(start_row + 2, start_row + 2 + len(results.category_totals)):
                ws.cell(row=row, column=2).number_format = '"$"#,##0.00'
                ws.cell(row=row, column=3).number_format = '0.0"%"'
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def _create_plan_details_sheet(self, wb: Workbook):
        """Create plan details sheet."""
        ws = wb.create_sheet("Plan Details")
        
        ws['A1'] = "Life Care Plan Details"
        ws['A1'].font = Font(size=14, bold=True)
        
        details = [
            ("Plan Name", self.plan.plan_name),
            ("Description", self.plan.plan_description or ""),
            ("Created", self.plan.created_at.strftime('%B %d, %Y')),
            ("Last Updated", self.plan.updated_at.strftime('%B %d, %Y')),
            ("Projection Start Age", f"{self.plan.projection_start_age} years"),
            ("Projection End Age", f"{self.plan.projection_end_age} years"),
            ("Discount Rate", f"{float(self.plan.discount_rate) * 100:.2f}%"),
            ("Inflation Rate", f"{float(self.plan.inflation_rate) * 100:.2f}%"),
            ("Use Present Value", "Yes" if self.plan.use_present_value else "No"),
            ("Include Attendant Care", "Yes" if self.plan.include_attendant_care else "No"),
            ("Include Equipment Replacement", "Yes" if self.plan.include_equipment_replacement else "No"),
        ]
        
        for row, (label, value) in enumerate(details, 3):
            ws.cell(row=row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=row, column=2, value=value)
        
        # Methodology and assumptions
        if self.plan.methodology_notes:
            ws.cell(row=len(details) + 5, column=1, value="Methodology").font = Font(bold=True)
            ws.cell(row=len(details) + 6, column=1, value=self.plan.methodology_notes)
        
        if self.plan.assumptions:
            start_row = len(details) + 8 if self.plan.methodology_notes else len(details) + 5
            ws.cell(row=start_row, column=1, value="Assumptions").font = Font(bold=True)
            ws.cell(row=start_row + 1, column=1, value=self.plan.assumptions)
        
        # Auto-adjust column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 50
    
    def _create_evaluee_sheet(self, wb: Workbook):
        """Create evaluee information sheet."""
        ws = wb.create_sheet("Evaluee Information")
        
        ws['A1'] = f"Evaluee: {self.evaluee.full_name}"
        ws['A1'].font = Font(size=14, bold=True)
        
        details = [
            ("First Name", self.evaluee.first_name),
            ("Last Name", self.evaluee.last_name),
            ("Date of Birth", self.evaluee.date_of_birth.strftime('%B %d, %Y') if self.evaluee.date_of_birth else ""),
            ("Current Age", f"{self.evaluee.current_age} years" if self.evaluee.current_age else ""),
            ("Date of Injury", self.evaluee.date_of_injury.strftime('%B %d, %Y') if self.evaluee.date_of_injury else ""),
            ("Age at Injury", f"{self.evaluee.age_at_injury} years" if self.evaluee.age_at_injury else ""),
            ("Gender", self.evaluee.gender or ""),
            ("Phone", self.evaluee.phone or ""),
            ("Email", self.evaluee.email or ""),
            ("Occupation", self.evaluee.occupation or ""),
            ("Education Level", self.evaluee.education_level or ""),
            ("Pre-Injury Income", f"${self.evaluee.pre_injury_income:,.2f}" if self.evaluee.pre_injury_income else ""),
            ("Life Expectancy", f"{self.evaluee.life_expectancy} years" if self.evaluee.life_expectancy else ""),
            ("Life Expectancy Source", self.evaluee.life_expectancy_source or ""),
        ]
        
        for row, (label, value) in enumerate(details, 3):
            ws.cell(row=row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=row, column=2, value=value)
        
        # Medical information
        medical_start = len(details) + 5
        ws.cell(row=medical_start, column=1, value="Medical Information").font = Font(size=12, bold=True)
        
        medical_info = [
            ("Primary Diagnosis", self.evaluee.primary_diagnosis or ""),
            ("Secondary Diagnoses", self.evaluee.secondary_diagnoses or ""),
            ("Injury Description", self.evaluee.injury_description or ""),
            ("Current Medical Status", self.evaluee.current_medical_status or ""),
        ]
        
        for row, (label, value) in enumerate(medical_info, medical_start + 2):
            ws.cell(row=row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=row, column=2, value=value)
        
        # Auto-adjust column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 50


class LifeCarePlanWordExporter:
    """Export life care plan data to Word document format."""
    
    def __init__(self, plan: LifeCarePlan):
        self.plan = plan
        self.evaluee = plan.evaluee
        
    def export_plan(self, scenario_results: List[ScenarioResults],
                   output_path: Optional[str] = None) -> bytes:
        """
        Export complete life care plan to Word document.
        
        Args:
            scenario_results: List of calculated scenario results
            output_path: Optional file path to save to
            
        Returns:
            Word document content as bytes
        """
        doc = Document()
        
        # Set document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)
        
        # Title page
        self._add_title_page(doc)
        
        # Executive summary
        if scenario_results:
            self._add_executive_summary(doc, scenario_results)
        
        # Evaluee information
        self._add_evaluee_section(doc)
        
        # Plan methodology
        self._add_methodology_section(doc)
        
        # Scenario details
        for results in scenario_results:
            self._add_scenario_section(doc, results)
        
        # Appendices
        self._add_appendices(doc)
        
        # Save to bytes or file
        if output_path:
            doc.save(output_path)
            with open(output_path, 'rb') as f:
                return f.read()
        else:
            output = io.BytesIO()
            doc.save(output)
            return output.getvalue()
    
    def _add_title_page(self, doc: Document):
        """Add title page."""
        # Title
        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title.add_run("LIFE CARE PLAN")
        title_run.font.size = Pt(24)
        title_run.font.bold = True
        
        # Subtitle
        subtitle = doc.add_paragraph()
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle_run = subtitle.add_run(f"For {self.evaluee.full_name}")
        subtitle_run.font.size = Pt(16)
        
        # Plan info
        doc.add_paragraph()
        plan_info = doc.add_paragraph()
        plan_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        plan_run = plan_info.add_run(f"Plan: {self.plan.plan_name}")
        plan_run.font.size = Pt(14)
        
        # Date
        date_para = doc.add_paragraph()
        date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        date_run = date_para.add_run(f"Prepared: {datetime.now().strftime('%B %d, %Y')}")
        date_run.font.size = Pt(12)
        
        # Page break
        doc.add_page_break()
    
    def _add_executive_summary(self, doc: Document, scenario_results: List[ScenarioResults]):
        """Add executive summary section."""
        heading = doc.add_heading('EXECUTIVE SUMMARY', level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Overview paragraph
        overview = doc.add_paragraph()
        overview.add_run(
            f"This life care plan has been prepared for {self.evaluee.full_name}, "
            f"who was {self.evaluee.age_at_injury} years old at the time of injury "
            f"on {self.evaluee.date_of_injury.strftime('%B %d, %Y') if self.evaluee.date_of_injury else 'an undetermined date'}. "
            f"The plan projects future medical and care needs over {self.plan.projection_years} years, "
            f"from age {self.plan.projection_start_age} to {self.plan.projection_end_age}."
        )
        
        if scenario_results:
            # Cost summary table
            doc.add_paragraph()
            cost_heading = doc.add_paragraph()
            cost_run = cost_heading.add_run("COST SUMMARY")
            cost_run.font.bold = True
            cost_run.font.size = Pt(12)
            
            # Create summary table
            table = doc.add_table(rows=1, cols=4)
            table.style = 'Table Grid'
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            # Header row
            header_cells = table.rows[0].cells
            header_cells[0].text = "Scenario"
            header_cells[1].text = "Present Value"
            header_cells[2].text = "Total Cost"
            header_cells[3].text = "Services"
            
            # Make header bold
            for cell in header_cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
            
            # Data rows
            for results in scenario_results:
                row_cells = table.add_row().cells
                row_cells[0].text = results.scenario_name
                row_cells[1].text = f"${results.present_value:,.0f}"
                row_cells[2].text = f"${results.total_cost:,.0f}"
                row_cells[3].text = str(len(results.service_calculations))
        
        doc.add_page_break()
    
    def _add_evaluee_section(self, doc: Document):
        """Add evaluee information section."""
        heading = doc.add_heading('EVALUEE INFORMATION', level=1)
        
        # Personal information
        doc.add_heading('Personal Information', level=2)
        
        personal_info = [
            f"Name: {self.evaluee.full_name}",
            f"Date of Birth: {self.evaluee.date_of_birth.strftime('%B %d, %Y') if self.evaluee.date_of_birth else 'Not specified'}",
            f"Current Age: {self.evaluee.current_age} years" if self.evaluee.current_age else "Current Age: Not specified",
            f"Date of Injury: {self.evaluee.date_of_injury.strftime('%B %d, %Y') if self.evaluee.date_of_injury else 'Not specified'}",
            f"Age at Injury: {self.evaluee.age_at_injury} years" if self.evaluee.age_at_injury else "Age at Injury: Not specified",
            f"Gender: {self.evaluee.gender or 'Not specified'}",
            f"Occupation: {self.evaluee.occupation or 'Not specified'}",
            f"Education Level: {self.evaluee.education_level or 'Not specified'}",
        ]
        
        for info in personal_info:
            doc.add_paragraph(info, style='List Bullet')
        
        # Medical information
        if any([self.evaluee.primary_diagnosis, self.evaluee.secondary_diagnoses, 
                self.evaluee.injury_description, self.evaluee.current_medical_status]):
            doc.add_heading('Medical Information', level=2)
            
            if self.evaluee.primary_diagnosis:
                doc.add_paragraph().add_run("Primary Diagnosis: ").font.bold = True
                doc.paragraphs[-1].add_run(self.evaluee.primary_diagnosis)
            
            if self.evaluee.secondary_diagnoses:
                doc.add_paragraph().add_run("Secondary Diagnoses: ").font.bold = True
                doc.paragraphs[-1].add_run(self.evaluee.secondary_diagnoses)
            
            if self.evaluee.injury_description:
                doc.add_paragraph().add_run("Injury Description: ").font.bold = True
                doc.paragraphs[-1].add_run(self.evaluee.injury_description)
            
            if self.evaluee.current_medical_status:
                doc.add_paragraph().add_run("Current Medical Status: ").font.bold = True
                doc.paragraphs[-1].add_run(self.evaluee.current_medical_status)
        
        doc.add_page_break()
    
    def _add_methodology_section(self, doc: Document):
        """Add methodology section."""
        heading = doc.add_heading('METHODOLOGY', level=1)
        
        # Standard methodology paragraph
        methodology_para = doc.add_paragraph()
        methodology_para.add_run(
            "This life care plan has been developed using established methodologies for "
            "projecting future care costs. The plan considers the evaluee's current medical "
            "condition, anticipated future needs, and reasonable cost projections based on "
            "current market rates adjusted for inflation."
        )
        
        # Economic assumptions
        doc.add_heading('Economic Assumptions', level=2)
        
        assumptions = [
            f"Discount Rate: {float(self.plan.discount_rate) * 100:.2f}% (used for present value calculations)",
            f"Inflation Rate: {float(self.plan.inflation_rate) * 100:.2f}% (applied to future costs)",
            f"Projection Period: Age {self.plan.projection_start_age} to {self.plan.projection_end_age} ({self.plan.projection_years} years)",
            f"Present Value Analysis: {'Included' if self.plan.use_present_value else 'Not included'}",
        ]
        
        for assumption in assumptions:
            doc.add_paragraph(assumption, style='List Bullet')
        
        # Custom methodology notes
        if self.plan.methodology_notes:
            doc.add_heading('Additional Methodology Notes', level=2)
            doc.add_paragraph(self.plan.methodology_notes)
        
        # Assumptions
        if self.plan.assumptions:
            doc.add_heading('Plan Assumptions', level=2)
            doc.add_paragraph(self.plan.assumptions)
        
        doc.add_page_break()
    
    def _add_scenario_section(self, doc: Document, results: ScenarioResults):
        """Add detailed scenario section."""
        heading = doc.add_heading(f'SCENARIO: {results.scenario_name.upper()}', level=1)
        
        # Scenario summary
        summary_para = doc.add_paragraph()
        summary_para.add_run("Present Value: ").font.bold = True
        summary_para.add_run(f"${results.present_value:,.2f}")
        summary_para.add_run(" | ")
        summary_para.add_run("Total Cost: ").font.bold = True
        summary_para.add_run(f"${results.total_cost:,.2f}")
        summary_para.add_run(" | ")
        summary_para.add_run("Services: ").font.bold = True
        summary_para.add_run(str(len(results.service_calculations)))
        
        # Category breakdown
        if results.category_totals:
            doc.add_heading('Cost by Category', level=2)
            
            # Create category table
            cat_table = doc.add_table(rows=1, cols=3)
            cat_table.style = 'Table Grid'
            
            # Header
            header_cells = cat_table.rows[0].cells
            header_cells[0].text = "Category"
            header_cells[1].text = "Present Value"
            header_cells[2].text = "Percentage"
            
            for cell in header_cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
            
            # Data rows
            for category, amount in sorted(results.category_totals.items()):
                row_cells = cat_table.add_row().cells
                row_cells[0].text = category
                row_cells[1].text = f"${amount:,.2f}"
                row_cells[2].text = f"{(amount / results.present_value * 100):.1f}%"
        
        # Service details
        if results.service_calculations:
            doc.add_heading('Service Details', level=2)
            
            # Create services table
            svc_table = doc.add_table(rows=1, cols=4)
            svc_table.style = 'Table Grid'
            
            # Header
            header_cells = svc_table.rows[0].cells
            header_cells[0].text = "Service"
            header_cells[1].text = "Present Value"
            header_cells[2].text = "Total Cost"
            header_cells[3].text = "First Year Cost"
            
            for cell in header_cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
            
            # Sort services by present value (descending)
            sorted_services = sorted(
                results.service_calculations,
                key=lambda x: x.present_value,
                reverse=True
            )
            
            # Data rows
            for calc in sorted_services:
                row_cells = svc_table.add_row().cells
                row_cells[0].text = calc.service_name
                row_cells[1].text = f"${calc.present_value:,.2f}"
                row_cells[2].text = f"${calc.total_cost:,.2f}"
                row_cells[3].text = f"${calc.first_year_cost:,.2f}"
        
        doc.add_page_break()
    
    def _add_appendices(self, doc: Document):
        """Add appendices section."""
        heading = doc.add_heading('APPENDICES', level=1)
        
        # Appendix A: Plan Details
        doc.add_heading('Appendix A: Plan Details', level=2)
        
        plan_details = [
            f"Plan Name: {self.plan.plan_name}",
            f"Created: {self.plan.created_at.strftime('%B %d, %Y')}",
            f"Last Updated: {self.plan.updated_at.strftime('%B %d, %Y')}",
            f"Projection Period: Age {self.plan.projection_start_age} to {self.plan.projection_end_age}",
            f"Economic Assumptions:",
            f"  • Discount Rate: {float(self.plan.discount_rate) * 100:.2f}%",
            f"  • Inflation Rate: {float(self.plan.inflation_rate) * 100:.2f}%",
            f"Special Considerations:",
            f"  • Attendant Care: {'Included' if self.plan.include_attendant_care else 'Not included'}",
            f"  • Equipment Replacement: {'Included' if self.plan.include_equipment_replacement else 'Not included'}",
        ]
        
        for detail in plan_details:
            if detail.startswith('  •'):
                doc.add_paragraph(detail[4:], style='List Bullet 2')
            elif detail.endswith(':'):
                para = doc.add_paragraph()
                para.add_run(detail).font.bold = True
            else:
                doc.add_paragraph(detail, style='List Bullet')
        
        # Appendix B: Limitations
        if self.plan.limitations:
            doc.add_heading('Appendix B: Limitations', level=2)
            doc.add_paragraph(self.plan.limitations)
        else:
            doc.add_heading('Appendix B: Standard Limitations', level=2)
            standard_limitations = [
                "This life care plan is based on information available at the time of preparation.",
                "Future medical developments may affect the recommendations and costs contained herein.",
                "Actual costs may vary based on geographic location, provider selection, and individual circumstances.",
                "This plan should be reviewed periodically and updated as the evaluee's condition changes.",
                "The economic projections are based on current economic assumptions and may be affected by future economic conditions."
            ]
            
            for limitation in standard_limitations:
                doc.add_paragraph(limitation, style='List Bullet')


def create_life_care_plan_export(plan: LifeCarePlan, scenario_results: List[ScenarioResults],
                                export_format: str = 'excel') -> bytes:
    """
    Convenience function to create life care plan exports.
    
    Args:
        plan: The life care plan to export
        scenario_results: Calculated scenario results
        export_format: 'excel' or 'word'
        
    Returns:
        File content as bytes
    """
    if export_format.lower() == 'excel':
        exporter = LifeCarePlanExcelExporter(plan)
        return exporter.export_plan(scenario_results)
    elif export_format.lower() == 'word':
        exporter = LifeCarePlanWordExporter(plan)
        return exporter.export_plan(scenario_results)
    else:
        raise ValueError(f"Unsupported export format: {export_format}")