"""
Enhanced Word Document Export for Forensic Economic Reports

Based on the professional document generation system from life-plan-genius,
this module provides sophisticated Word document export capabilities with:
- Professional template rendering
- Advanced table handling
- Proper page orientation and sections
- Complete economic data integration
"""

import base64
import io
import logging
import os
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from docxcompose.composer import Composer

logger = logging.getLogger(__name__)


class ForensicWordExporter:
    """Enhanced Word document exporter for forensic economic reports."""
    
    def __init__(self, template_path: Optional[str] = None):
        """Initialize the exporter with optional template path."""
        self.template_path = template_path or self._get_default_template_path()
        self.renderers = [
            HeaderRenderer(),
            TextRenderer(),
            TableRenderer(),
            EconomicDataRenderer(),
            CalculationsRenderer()
        ]
    
    def _get_default_template_path(self) -> str:
        """Get the default template path."""
        return os.path.join(os.path.dirname(__file__), "templates", "forensic_report_template.docx")
    
    def export_to_word(self, report_data: Dict[str, Any], save_to_disk: bool = False) -> str:
        """
        Export forensic report data to Word document.
        
        Args:
            report_data: Complete forensic report data
            save_to_disk: Whether to save file to disk
            
        Returns:
            Base64 encoded document bytes
        """
        logger.info("Starting forensic report Word export")
        
        # Load template or create new document
        doc = self._load_template()
        
        # Apply all renderers
        for renderer in self.renderers:
            logger.debug(f"Applying renderer: {type(renderer).__name__}")
            renderer.render(doc, report_data)
        
        # Handle multi-section documents
        if self._needs_appendix(report_data):
            appendix_doc = self._create_appendix(report_data)
            doc = self._combine_documents(doc, appendix_doc)
        
        # Save and return
        return self._save_document(doc, save_to_disk)
    
    def _load_template(self) -> Document:
        """Load Word template or create new document."""
        if os.path.exists(self.template_path):
            logger.info(f"Loading template: {self.template_path}")
            return Document(self.template_path)
        else:
            logger.info("Creating new document (no template found)")
            return self._create_default_document()
    
    def _create_default_document(self) -> Document:
        """Create a default forensic report document structure."""
        doc = Document()
        
        # Set document margins
        section = doc.sections[0]
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
        # Add default structure
        self._add_default_structure(doc)
        
        return doc
    
    def _add_default_structure(self, doc: Document):
        """Add default forensic report structure."""
        # Title
        title = doc.add_heading("FORENSIC ECONOMIC REPORT", 0)
        title.alignment = 1  # Center alignment
        
        # Evaluee information section
        doc.add_heading("EVALUEE INFORMATION", 1)
        doc.add_paragraph("{{evaluee_name}}")
        doc.add_paragraph("Date of Birth: {{date_of_birth}}")
        doc.add_paragraph("Date of Injury: {{date_of_injury}}")
        doc.add_paragraph("State: {{state}}")
        
        # Economic analysis sections
        doc.add_heading("ECONOMIC LOSS ANALYSIS", 1)
        
        # Earnings loss section
        doc.add_heading("EARNINGS LOSS", 2)
        doc.add_paragraph("{{earnings_analysis}}")
        
        # Add table placeholders
        doc.add_paragraph("{{earnings_table}}")
        
        # Healthcare costs section
        doc.add_heading("HEALTHCARE COSTS", 2)
        doc.add_paragraph("{{healthcare_analysis}}")
        doc.add_paragraph("{{healthcare_table}}")
        
        # Fringe benefits section
        doc.add_heading("FRINGE BENEFITS", 2)
        doc.add_paragraph("{{fringe_analysis}}")
        doc.add_paragraph("{{fringe_table}}")
        
        # Household services section
        doc.add_heading("HOUSEHOLD SERVICES", 2)
        doc.add_paragraph("{{household_analysis}}")
        doc.add_paragraph("{{household_table}}")
        
        # Present value calculations
        doc.add_heading("PRESENT VALUE CALCULATIONS", 1)
        doc.add_paragraph("{{present_value_analysis}}")
        doc.add_paragraph("{{present_value_table}}")
        
        # Summary
        doc.add_heading("SUMMARY", 1)
        doc.add_paragraph("{{summary_analysis}}")
        
        # Signature block
        doc.add_paragraph("\\n\\n")
        doc.add_paragraph("{{economist_name}}")
        doc.add_paragraph("{{economist_title}}")
        doc.add_paragraph("{{date}}")
    
    def _needs_appendix(self, report_data: Dict[str, Any]) -> bool:
        """Determine if report needs an appendix."""
        appendix_sections = [
            'detailed_calculations',
            'methodology_appendix',
            'data_sources',
            'economic_factors'
        ]
        return any(report_data.get(section) for section in appendix_sections)
    
    def _create_appendix(self, report_data: Dict[str, Any]) -> Document:
        """Create appendix document."""
        appendix_doc = Document()
        
        # Set landscape orientation for tables
        section = appendix_doc.sections[0]
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width = Inches(11)
        section.page_height = Inches(8.5)
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)
        
        # Add appendix content
        appendix_doc.add_heading("APPENDIX", 0)
        
        # Detailed calculations
        if report_data.get('detailed_calculations'):
            appendix_doc.add_heading("DETAILED CALCULATIONS", 1)
            # Add detailed calculation tables
        
        return appendix_doc
    
    def _combine_documents(self, main_doc: Document, appendix_doc: Document) -> Document:
        """Combine main document with appendix."""
        # Add page break before appendix
        main_doc.add_page_break()
        
        # Create new section for appendix
        new_section = main_doc.add_section(WD_SECTION.NEW_PAGE)
        new_section.orientation = WD_ORIENT.LANDSCAPE
        new_section.page_width = Inches(11)
        new_section.page_height = Inches(8.5)
        new_section.top_margin = Inches(0.5)
        new_section.bottom_margin = Inches(0.5)
        new_section.left_margin = Inches(0.5)
        new_section.right_margin = Inches(0.5)
        
        # Use composer to append appendix
        composer = Composer(main_doc)
        composer.append(appendix_doc)
        
        return composer
    
    def _save_document(self, doc: Document, save_to_disk: bool) -> str:
        """Save document and return base64 encoded bytes."""
        if save_to_disk:
            os.makedirs("reports", exist_ok=True)
            filename = f"forensic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            filepath = os.path.join("reports", filename)
            doc.save(filepath)
            logger.info(f"Saved report to {filepath}")
        
        # Return base64 encoded bytes
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")


class BaseRenderer:
    """Base class for all document renderers."""
    
    def render(self, doc: Document, data: Dict[str, Any]) -> None:
        """Render data into document. Must be implemented by subclasses."""
        raise NotImplementedError


class HeaderRenderer(BaseRenderer):
    """Renderer for document headers and metadata."""
    
    def render(self, doc: Document, data: Dict[str, Any]) -> None:
        """Render header information."""
        # Add header with case information
        section = doc.sections[0]
        header = section.header
        
        if data.get('case_number'):
            header_para = header.paragraphs[0]
            header_para.text = f"Case: {data.get('case_number', '')} | {data.get('evaluee_name', '')}"
        
        # Add footer with page numbers
        footer = section.footer
        footer_para = footer.paragraphs[0]
        footer_para.text = "Page "
        # Add page number field
        run = footer_para.runs[0]
        fldChar1 = OxmlElement('w:fldChar')
        fldChar1.set(qn('w:fldCharType'), 'begin')
        run._r.append(fldChar1)
        
        instrText = OxmlElement('w:instrText')
        instrText.text = "PAGE"
        run._r.append(instrText)
        
        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'end')
        run._r.append(fldChar2)


class TextRenderer(BaseRenderer):
    """Renderer for text placeholders."""
    
    def render(self, doc: Document, data: Dict[str, Any]) -> None:
        """Replace text placeholders throughout the document."""
        # Define default values for common placeholders
        defaults = {
            '{{evaluee_name}}': data.get('evaluee_name', 'N/A'),
            '{{date_of_birth}}': self._format_date(data.get('date_of_birth')),
            '{{date_of_injury}}': self._format_date(data.get('date_of_injury')),
            '{{state}}': data.get('state', 'N/A'),
            '{{economist_name}}': data.get('economist_name', 'Economic Consultant'),
            '{{economist_title}}': data.get('economist_title', 'Forensic Economist'),
            '{{date}}': datetime.now().strftime('%B %d, %Y'),
            '{{case_number}}': data.get('case_number', ''),
        }
        
        # Add analysis text from data
        if data.get('earnings_analysis'):
            defaults['{{earnings_analysis}}'] = data['earnings_analysis']
        if data.get('healthcare_analysis'):
            defaults['{{healthcare_analysis}}'] = data['healthcare_analysis']
        if data.get('summary_analysis'):
            defaults['{{summary_analysis}}'] = data['summary_analysis']
        
        # Replace all placeholders
        for placeholder, value in defaults.items():
            if value is not None:
                self._replace_placeholder(doc, placeholder, str(value))
    
    def _format_date(self, date_value) -> str:
        """Format date value for display."""
        if not date_value:
            return 'N/A'
        if isinstance(date_value, str):
            return date_value
        try:
            return date_value.strftime('%B %d, %Y')
        except:
            return str(date_value)
    
    def _replace_placeholder(self, doc: Document, placeholder: str, replacement: str) -> None:
        """Replace placeholder text in document."""
        for paragraph in self._iter_all_paragraphs(doc):
            if placeholder in paragraph.text:
                self._replace_in_paragraph(paragraph, placeholder, replacement)
    
    def _iter_all_paragraphs(self, doc: Document):
        """Iterator for all paragraphs in document."""
        for paragraph in doc.paragraphs:
            yield paragraph
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        yield paragraph
    
    def _replace_in_paragraph(self, paragraph, placeholder: str, replacement: str):
        """Replace text in a paragraph while preserving formatting."""
        full_text = paragraph.text
        if placeholder not in full_text:
            return
        
        # Store run formatting
        run_formats = []
        for run in paragraph.runs:
            run_formats.append({
                'bold': run.bold,
                'italic': run.italic,
                'underline': run.underline,
                'font_name': run.font.name,
                'font_size': run.font.size,
            })
        
        # Replace text
        new_text = full_text.replace(placeholder, replacement)
        
        # Clear paragraph and add new text with first run's formatting
        paragraph.clear()
        run = paragraph.add_run(new_text)
        
        if run_formats:
            fmt = run_formats[0]
            run.bold = fmt['bold']
            run.italic = fmt['italic']
            run.underline = fmt['underline']
            if fmt['font_name']:
                run.font.name = fmt['font_name']
            if fmt['font_size']:
                run.font.size = fmt['font_size']


class TableRenderer(BaseRenderer):
    """Renderer for economic data tables."""
    
    def render(self, doc: Document, data: Dict[str, Any]) -> None:
        """Render economic data tables."""
        table_configs = {
            '{{earnings_table}}': {
                'data_key': 'earnings_table_data',
                'headers': ['Year', 'Pre-Injury Earnings', 'Post-Injury Earnings', 'Loss', 'Present Value']
            },
            '{{healthcare_table}}': {
                'data_key': 'healthcare_table_data', 
                'headers': ['Category', 'Annual Cost', 'Duration', 'Total Cost', 'Present Value']
            },
            '{{fringe_table}}': {
                'data_key': 'fringe_table_data',
                'headers': ['Benefit Type', 'Rate', 'Annual Value', 'Present Value']
            },
            '{{household_table}}': {
                'data_key': 'household_table_data',
                'headers': ['Service', 'Hours/Week', 'Rate', 'Annual Cost', 'Present Value']
            },
            '{{present_value_table}}': {
                'data_key': 'present_value_summary',
                'headers': ['Category', 'Discount Rate', 'Present Value']
            }
        }
        
        for placeholder, config in table_configs.items():
            table_data = data.get(config['data_key'])
            if table_data:
                self._replace_table_placeholder(doc, placeholder, table_data, config['headers'])
    
    def _replace_table_placeholder(self, doc: Document, placeholder: str, table_data: List[List], headers: List[str]):
        """Replace table placeholder with actual table."""
        for paragraph in doc.paragraphs:
            if placeholder in paragraph.text:
                # Remove placeholder paragraph
                p = paragraph._element
                p.getparent().remove(p)
                
                # Create table
                table = doc.add_table(rows=1, cols=len(headers))
                table.style = 'Table Grid'
                
                # Add headers
                header_row = table.rows[0]
                for i, header in enumerate(headers):
                    cell = header_row.cells[i]
                    cell.text = header
                    # Make header bold
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.bold = True
                
                # Add data rows
                for row_data in table_data:
                    row = table.add_row()
                    for i, value in enumerate(row_data):
                        if i < len(row.cells):
                            row.cells[i].text = str(value)
                
                break


class EconomicDataRenderer(BaseRenderer):
    """Renderer for economic analysis data."""
    
    def render(self, doc: Document, data: Dict[str, Any]) -> None:
        """Render economic analysis data."""
        # This renderer handles complex economic data integration
        # from all the calculation scenarios
        
        if data.get('earnings_scenarios'):
            self._render_earnings_scenarios(doc, data['earnings_scenarios'])
        
        if data.get('healthcare_scenarios'):
            self._render_healthcare_scenarios(doc, data['healthcare_scenarios'])
        
        if data.get('fringe_scenarios'):
            self._render_fringe_scenarios(doc, data['fringe_scenarios'])
    
    def _render_earnings_scenarios(self, doc: Document, scenarios):
        """Render earnings scenario analysis."""
        # Add detailed earnings analysis
        for scenario in scenarios:
            # Create sections for pre/post injury analysis
            pass
    
    def _render_healthcare_scenarios(self, doc: Document, scenarios):
        """Render healthcare cost scenarios."""
        pass
    
    def _render_fringe_scenarios(self, doc: Document, scenarios):
        """Render fringe benefit scenarios."""
        pass


class CalculationsRenderer(BaseRenderer):
    """Renderer for detailed calculations and methodology."""
    
    def render(self, doc: Document, data: Dict[str, Any]) -> None:
        """Render calculation methodology and formulas."""
        # Add methodology section
        if data.get('methodology'):
            self._add_methodology_section(doc, data['methodology'])
        
        # Add calculation details
        if data.get('calculation_details'):
            self._add_calculation_details(doc, data['calculation_details'])
    
    def _add_methodology_section(self, doc: Document, methodology):
        """Add methodology section to document."""
        # Find methodology placeholder or add new section
        found_placeholder = False
        for paragraph in doc.paragraphs:
            if '{{methodology}}' in paragraph.text:
                paragraph.text = paragraph.text.replace('{{methodology}}', methodology)
                found_placeholder = True
                break
        
        if not found_placeholder:
            doc.add_heading("METHODOLOGY", 1)
            doc.add_paragraph(methodology)
    
    def _add_calculation_details(self, doc: Document, details):
        """Add detailed calculations to document."""
        pass


# Utility function for easy usage
def create_forensic_word_report(report_data: Dict[str, Any], template_path: Optional[str] = None, save_to_disk: bool = False) -> str:
    """
    Create a professional forensic economic report in Word format.
    
    Args:
        report_data: Complete report data including all economic analysis
        template_path: Optional path to Word template
        save_to_disk: Whether to save file to disk
        
    Returns:
        Base64 encoded Word document
    """
    exporter = ForensicWordExporter(template_path)
    return exporter.export_to_word(report_data, save_to_disk)


# Example usage and data structure
EXAMPLE_REPORT_DATA = {
    'evaluee_name': 'John Doe',
    'date_of_birth': '1980-01-15',
    'date_of_injury': '2023-06-15',
    'state': 'California',
    'case_number': 'CV-2023-001',
    'economist_name': 'Dr. Jane Smith',
    'economist_title': 'Forensic Economist, Ph.D.',
    
    # Analysis text
    'earnings_analysis': 'Based on the evaluee\'s work history and education...',
    'healthcare_analysis': 'The medical evidence indicates ongoing treatment needs...',
    'summary_analysis': 'The total economic loss is estimated at...',
    
    # Table data
    'earnings_table_data': [
        ['2024', '$50,000', '$0', '$50,000', '$48,077'],
        ['2025', '$52,000', '$0', '$52,000', '$47,885'],
        # ... more years
    ],
    
    'healthcare_table_data': [
        ['Physical Therapy', '$150/visit', '52 visits/year', '$7,800', '$7,500'],
        ['Medications', '$200/month', 'Lifetime', '$2,400/year', '$48,000'],
        # ... more categories
    ],
    
    # Detailed scenarios from economic analysis system
    'earnings_scenarios': [
        {
            'type': 'pre_injury',
            'annual_earnings': 50000,
            'growth_rate': 0.04,
            'work_life_expectancy': 25.5
        }
    ],
    
    'healthcare_scenarios': [
        {
            'category': 'ongoing_treatment',
            'annual_cost': 7800,
            'inflation_rate': 0.035,
            'duration': 'lifetime'
        }
    ]
}