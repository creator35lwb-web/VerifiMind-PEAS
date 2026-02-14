"""
DEPRECATED: Use markdown_reporter.py instead.

VerifiMind PEAS - PDF Report Generator v2.0.1
Corrected Version - December 2025

DEPRECATION NOTICE (February 2026):
    This module is deprecated as of the Markdown-first strategic pivot.
    Markdown is now the canonical output format for all VerifiMind reports.
    PDF export is retained only for academic/compliance use cases where
    PDF is explicitly required (e.g., Zenodo submissions).

    Primary reporter: src.core.markdown_reporter.ValidationReportGenerator
    To use PDF explicitly: pass --format pdf to verifimind_complete.py

Generates publication-ready PDF reports synthesizing
Agent insights and Socratic Scrutiny results.
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional

# PDF library
from fpdf import FPDF

from src.core.logging_config import get_logger

logger = get_logger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class PDFConfig:
    """Configuration constants for PDF generation."""
    
    # Page settings
    PAGE_WIDTH = 210  # A4 width in mm
    PAGE_HEIGHT = 297  # A4 height in mm
    MARGIN = 15
    
    # Colors (RGB tuples)
    COLOR_PRIMARY = (0, 51, 102)       # Dark blue
    COLOR_SECONDARY = (100, 100, 100)  # Grey
    COLOR_SUCCESS = (0, 128, 0)        # Green
    COLOR_WARNING = (200, 150, 0)      # Amber
    COLOR_DANGER = (150, 0, 0)         # Dark red
    COLOR_BLACK = (0, 0, 0)
    COLOR_MUTED = (128, 128, 128)
    
    # Font paths (common locations)
    DEJAVU_PATHS = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/TTF/DejaVuSans.ttf',
        '/Library/Fonts/DejaVuSans.ttf',
        'C:/Windows/Fonts/DejaVuSans.ttf',
        './fonts/DejaVuSans.ttf',
    ]
    DEJAVU_BOLD_PATHS = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
        '/Library/Fonts/DejaVuSans-Bold.ttf',
        'C:/Windows/Fonts/DejaVuSans-Bold.ttf',
        './fonts/DejaVuSans-Bold.ttf',
    ]


# =============================================================================
# Custom PDF Class
# =============================================================================

class VerifiMindPDF(FPDF):
    """
    Custom PDF class for VerifiMind branding and layout.
    
    Features:
    - Unicode font support (attempts DejaVu, falls back to Helvetica)
    - Branded header and footer
    - Consistent styling throughout
    """
    
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.unicode_enabled = False
        self._setup_fonts()
        self.set_auto_page_break(auto=True, margin=15)
    
    def _setup_fonts(self):
        """Attempt to load Unicode fonts, fall back to built-in if unavailable."""
        # Try to find and load DejaVu fonts
        dejavu_regular = None
        dejavu_bold = None
        
        for path in PDFConfig.DEJAVU_PATHS:
            if os.path.exists(path):
                dejavu_regular = path
                break
        
        for path in PDFConfig.DEJAVU_BOLD_PATHS:
            if os.path.exists(path):
                dejavu_bold = path
                break
        
        if dejavu_regular:
            try:
                self.add_font('DejaVu', '', dejavu_regular, uni=True)
                if dejavu_bold:
                    self.add_font('DejaVu', 'B', dejavu_bold, uni=True)
                else:
                    # Use regular for bold if bold not found
                    self.add_font('DejaVu', 'B', dejavu_regular, uni=True)
                self.unicode_enabled = True
                logger.info("Unicode fonts loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load Unicode fonts: {e}")
                self.unicode_enabled = False
        else:
            logger.warning("DejaVu fonts not found, using Helvetica (limited Unicode support)")
    
    def _get_font(self, style: str = '') -> str:
        """Get the appropriate font name."""
        return 'DejaVu' if self.unicode_enabled else 'Helvetica'
    
    def _safe_text(self, text: str) -> str:
        """
        Safely encode text for PDF output.
        Removes or replaces problematic characters if Unicode is not available.
        """
        if self.unicode_enabled:
            return str(text)
        
        # Replace common Unicode characters with ASCII equivalents
        replacements = {
            '™': '(TM)',
            '©': '(C)',
            '®': '(R)',
            '—': '-',
            '–': '-',
            '\u201c': '"',  # LEFT DOUBLE QUOTATION MARK
            '\u201d': '"',  # RIGHT DOUBLE QUOTATION MARK
            '\u2018': "'",  # LEFT SINGLE QUOTATION MARK
            '\u2019': "'",  # RIGHT SINGLE QUOTATION MARK
            '…': '...',
            '•': '*',
            '→': '->',
            '←': '<-',
            '↑': '^',
            '↓': 'v',
            '✓': '[OK]',
            '✗': '[X]',
            '★': '*',
            '☆': '*',
        }
        
        result = str(text)
        for unicode_char, ascii_equiv in replacements.items():
            result = result.replace(unicode_char, ascii_equiv)
        
        # Remove any remaining non-ASCII characters
        try:
            result.encode('latin-1')
        except UnicodeEncodeError:
            result = result.encode('latin-1', errors='replace').decode('latin-1')
        
        return result

    def header(self):
        """Custom header with branding."""
        self.set_font(self._get_font(), 'B', 10)
        self.set_text_color(*PDFConfig.COLOR_SECONDARY)
        self.cell(0, 10, self._safe_text('VerifiMind™ PEAS - Genesis Validation Report'), 0, 1, 'R')
        self.ln(5)

    def footer(self):
        """Custom footer with page numbers."""
        self.set_y(-15)
        self.set_font(self._get_font(), '', 8)
        self.set_text_color(*PDFConfig.COLOR_MUTED)
        footer_text = f'Page {self.page_no()} | Generated by VerifiMind X-Z-CS Trinity'
        self.cell(0, 10, self._safe_text(footer_text), 0, 0, 'C')


# =============================================================================
# Main Generator Class
# =============================================================================

class ValidationReportGenerator:
    """
    Generates 'publication-ready' PDF reports synthesizing 
    Agent insights and Socratic Scrutiny.
    
    Features:
    - Safe attribute access with fallbacks
    - Unicode text support
    - Comprehensive error handling
    - Structured sections with consistent styling
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.pdf: Optional[VerifiMindPDF] = None

    def generate(
        self, 
        app_spec: Any, 
        agent_results: Dict[str, Any], 
        socratic_data: Dict[str, Any]
    ) -> str:
        """
        Main driver to build the full PDF report.
        
        Args:
            app_spec: Application specification object or dict
            agent_results: Dictionary of agent results keyed by agent type
            socratic_data: Deep Socratic analysis data from CS agent
            
        Returns:
            Path to generated PDF file
        """
        # Extract app info safely
        app_name = self._safe_get(app_spec, 'app_name', 'Untitled Application')
        logger.info(f"Generating PDF report for {app_name}...")
        
        # Initialize fresh PDF
        self.pdf = VerifiMindPDF()
        
        try:
            self.pdf.add_page()
            
            # 1. Title Page
            self._create_title_page(app_spec)
            
            # 2. Executive Summary (The Trinity Verdict)
            self._add_section_title("1. Executive Summary: The Trinity Verdict")
            self._add_trinity_matrix(agent_results)
            
            # 3. Socratic Concept Scrutiny (The Deep Dive)
            self._add_section_title("2. Socratic Concept Scrutiny")
            self._add_socratic_deep_dive(socratic_data)
            
            # 4. Security Analysis
            self._add_section_title("3. Security Analysis")
            self._add_security_section(socratic_data)
            
            # 5. Strategic Roadmap
            self._add_section_title("4. Strategic Roadmap")
            self._add_roadmap(socratic_data.get('strategy', {}))

            # 6. IP & Blockchain Proof
            self._add_section_title("5. IP & Attribution Proof")
            self._add_ip_proof(app_spec)

            # Save
            filepath = self._save_pdf(app_name)
            logger.info(f"PDF Report saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}", exc_info=True)
            raise

    # =========================================================================
    # Section Builders
    # =========================================================================

    def _create_title_page(self, app_spec: Any):
        """Create the title/cover page."""
        app_name = self._safe_get(app_spec, 'app_name', 'Untitled Application')
        category = self._safe_get(app_spec, 'category', 'General')
        description = self._safe_get(app_spec, 'description', 'No description provided.')
        
        self.pdf.ln(40)
        
        # Main title
        self.pdf.set_font(self.pdf._get_font(), 'B', 24)
        self.pdf.set_text_color(*PDFConfig.COLOR_PRIMARY)
        self.pdf.multi_cell(0, 12, self.pdf._safe_text(app_name), 0, 'C')
        
        # Subtitle
        self.pdf.ln(10)
        self.pdf.set_font(self.pdf._get_font(), '', 14)
        self.pdf.set_text_color(*PDFConfig.COLOR_BLACK)
        self.pdf.cell(0, 10, "Genesis Validation Report", 0, 1, 'C')
        
        # Category
        self.pdf.ln(5)
        self.pdf.set_font(self.pdf._get_font(), '', 12)
        self.pdf.set_text_color(*PDFConfig.COLOR_SECONDARY)
        self.pdf.cell(0, 10, self.pdf._safe_text(f"Category: {category}"), 0, 1, 'C')
        
        # Description box
        self.pdf.ln(20)
        self.pdf.set_font(self.pdf._get_font(), '', 10)
        self.pdf.set_text_color(*PDFConfig.COLOR_BLACK)
        
        # Truncate description if too long
        desc_truncated = description[:500] + ('...' if len(description) > 500 else '')
        self.pdf.multi_cell(0, 6, self.pdf._safe_text(f"Description:\n{desc_truncated}"), 0, 'C')
        
        # Date
        self.pdf.ln(30)
        self.pdf.set_font(self.pdf._get_font(), 'B', 12)
        date_str = datetime.now().strftime('%B %d, %Y')
        self.pdf.cell(0, 10, f"Date: {date_str}", 0, 1, 'C')
        
        # Start new page for content
        self.pdf.add_page()

    def _add_section_title(self, title: str):
        """Add a styled section title with underline."""
        self.pdf.set_font(self.pdf._get_font(), 'B', 16)
        self.pdf.set_text_color(*PDFConfig.COLOR_PRIMARY)
        self.pdf.cell(0, 12, self.pdf._safe_text(title), 0, 1, 'L')
        
        # Underline
        y = self.pdf.get_y()
        self.pdf.line(PDFConfig.MARGIN, y, PDFConfig.PAGE_WIDTH - PDFConfig.MARGIN, y)
        self.pdf.ln(8)

    def _add_trinity_matrix(self, results: Dict[str, Any]):
        """Add the X-Z-CS Trinity results matrix."""
        self.pdf.set_text_color(*PDFConfig.COLOR_BLACK)
        
        # Agent definitions with display info
        agents = [
            ('X', 'X Intelligent', 'Innovation Engine', 'risk_score'),
            ('Z', 'Z Guardian', 'Ethics & Compliance', 'risk_score'),
            ('CS', 'CS Security', 'Vulnerability Scan', 'validation_score'),
        ]
        
        for key, name, role, score_field in agents:
            agent = results.get(key)
            
            if agent is None:
                self._add_agent_error(name, role, "Agent did not return results")
                continue
            
            # Extract data safely
            status = self._safe_get(agent, 'status', 'unknown').upper()
            score = self._safe_get(agent, score_field, 
                                   self._safe_get(agent, 'risk_score',
                                                  self._safe_get(agent, 'validation_score', 'N/A')))
            analysis = self._safe_get(agent, 'analysis', 'No analysis available')
            verdict = self._safe_get(agent, 'verdict', '')
            
            # Agent header
            self.pdf.set_font(self.pdf._get_font(), 'B', 12)
            self.pdf.set_text_color(*PDFConfig.COLOR_PRIMARY)
            self.pdf.cell(0, 8, self.pdf._safe_text(f"{name} ({role})"), 0, 1)
            
            # Status with color coding
            self.pdf.set_font(self.pdf._get_font(), '', 11)
            status_color = self._get_status_color(status)
            self.pdf.set_text_color(*status_color)
            
            status_line = f"Status: {status}"
            if score != 'N/A':
                status_line += f" | Score: {score}/100"
            if verdict:
                status_line += f" | Verdict: {verdict}"
            
            self.pdf.cell(0, 6, self.pdf._safe_text(status_line), 0, 1)
            
            # Analysis text
            self.pdf.set_text_color(*PDFConfig.COLOR_BLACK)
            self.pdf.set_font(self.pdf._get_font(), '', 10)
            analysis_truncated = str(analysis)[:400] + ('...' if len(str(analysis)) > 400 else '')
            self.pdf.multi_cell(0, 5, self.pdf._safe_text(f"Analysis: {analysis_truncated}"))
            self.pdf.ln(6)

    def _add_agent_error(self, name: str, role: str, error_msg: str):
        """Add an error entry for a failed agent."""
        self.pdf.set_font(self.pdf._get_font(), 'B', 12)
        self.pdf.set_text_color(*PDFConfig.COLOR_DANGER)
        self.pdf.cell(0, 8, self.pdf._safe_text(f"{name} ({role})"), 0, 1)
        
        self.pdf.set_font(self.pdf._get_font(), '', 11)
        self.pdf.cell(0, 6, self.pdf._safe_text(f"ERROR: {error_msg}"), 0, 1)
        self.pdf.ln(6)

    def _add_socratic_deep_dive(self, data: Dict[str, Any]):
        """Add the Socratic analysis section."""
        if not data:
            self._add_no_data_message("Socratic analysis data not available")
            return
        
        self.pdf.set_text_color(*PDFConfig.COLOR_BLACK)
        
        # Step 1: Clarification
        self.pdf.set_font(self.pdf._get_font(), 'B', 11)
        self.pdf.cell(0, 8, "Step 1: Clarification & Assumptions", 0, 1)
        self.pdf.set_font(self.pdf._get_font(), '', 10)
        clarification = data.get('clarification', data.get('step_1_clarification', 'Not available'))
        self.pdf.multi_cell(0, 5, self.pdf._safe_text(str(clarification)[:600]))
        self.pdf.ln(5)

        # Step 2: Feasibility
        self.pdf.set_font(self.pdf._get_font(), 'B', 11)
        self.pdf.cell(0, 8, "Step 2: Feasibility Analysis Scores", 0, 1)
        self.pdf.set_font(self.pdf._get_font(), '', 10)
        
        feasibility = data.get('feasibility', data.get('step_2_feasibility', {}))
        if isinstance(feasibility, dict):
            score_fields = [
                ('innovation_score', 'Innovation'),
                ('tech_feasibility_score', 'Technical Feasibility'),
                ('market_score', 'Market Potential'),
                ('risk_score', 'Risk Level'),
            ]
            for field, label in score_fields:
                score = feasibility.get(field, 'N/A')
                self.pdf.cell(0, 5, self.pdf._safe_text(f"  - {label}: {score}/100"), 0, 1)
        self.pdf.ln(5)

        # Step 3: Challenges
        self.pdf.set_font(self.pdf._get_font(), 'B', 11)
        self.pdf.set_text_color(*PDFConfig.COLOR_DANGER)
        self.pdf.cell(0, 8, "Step 3: Socratic Challenges (Devil's Advocate)", 0, 1)
        self.pdf.set_text_color(*PDFConfig.COLOR_BLACK)
        self.pdf.set_font(self.pdf._get_font(), '', 10)
        
        challenges = data.get('challenges', data.get('step_3_challenges', []))
        challenges = challenges or []  # Handle None
        
        if challenges:
            for i, challenge in enumerate(challenges[:5], 1):
                challenge_text = f"Q{i}: {str(challenge)[:200]}"
                self.pdf.multi_cell(0, 5, self.pdf._safe_text(challenge_text))
                self.pdf.ln(2)
        else:
            self.pdf.cell(0, 5, "No challenges recorded", 0, 1)
        
        self.pdf.ln(5)

    def _add_security_section(self, data: Dict[str, Any]):
        """Add the security scan results section."""
        security = data.get('security_scan', {})
        
        if not security:
            self._add_no_data_message("Security scan data not available")
            return
        
        self.pdf.set_text_color(*PDFConfig.COLOR_BLACK)
        
        # Threats
        self.pdf.set_font(self.pdf._get_font(), 'B', 11)
        self.pdf.set_text_color(*PDFConfig.COLOR_DANGER)
        self.pdf.cell(0, 8, "Identified Threats", 0, 1)
        self.pdf.set_text_color(*PDFConfig.COLOR_BLACK)
        self.pdf.set_font(self.pdf._get_font(), '', 10)
        
        threats = security.get('threats', [])
        for threat in (threats or [])[:5]:
            self.pdf.multi_cell(0, 5, self.pdf._safe_text(f"  - {threat}"))
        self.pdf.ln(3)
        
        # Mitigations
        self.pdf.set_font(self.pdf._get_font(), 'B', 11)
        self.pdf.set_text_color(*PDFConfig.COLOR_SUCCESS)
        self.pdf.cell(0, 8, "Recommended Mitigations", 0, 1)
        self.pdf.set_text_color(*PDFConfig.COLOR_BLACK)
        self.pdf.set_font(self.pdf._get_font(), '', 10)
        
        mitigations = security.get('mitigations', [])
        for mitigation in (mitigations or [])[:5]:
            self.pdf.multi_cell(0, 5, self.pdf._safe_text(f"  - {mitigation}"))
        self.pdf.ln(3)
        
        # Compliance Gaps
        compliance_gaps = security.get('compliance_gaps', [])
        if compliance_gaps:
            self.pdf.set_font(self.pdf._get_font(), 'B', 11)
            self.pdf.set_text_color(*PDFConfig.COLOR_WARNING)
            self.pdf.cell(0, 8, "Compliance Gaps", 0, 1)
            self.pdf.set_text_color(*PDFConfig.COLOR_BLACK)
            self.pdf.set_font(self.pdf._get_font(), '', 10)
            
            for gap in compliance_gaps[:5]:
                self.pdf.multi_cell(0, 5, self.pdf._safe_text(f"  - {gap}"))
        
        self.pdf.ln(5)

    def _add_roadmap(self, strategy: Dict[str, Any]):
        """Add the strategic roadmap section."""
        self.pdf.set_font(self.pdf._get_font(), '', 11)
        self.pdf.set_text_color(*PDFConfig.COLOR_BLACK)
        
        # Verdict
        verdict = strategy.get('verdict', 'N/A')
        verdict_reason = strategy.get('verdict_reason', '')
        
        self.pdf.set_font(self.pdf._get_font(), 'B', 11)
        self.pdf.cell(0, 8, self.pdf._safe_text(f"Strategic Verdict: {verdict}"), 0, 1)
        
        if verdict_reason:
            self.pdf.set_font(self.pdf._get_font(), '', 10)
            self.pdf.multi_cell(0, 5, self.pdf._safe_text(verdict_reason))
        self.pdf.ln(5)
        
        # Strategic Options
        options = strategy.get('strategic_options', [])
        if options:
            self.pdf.set_font(self.pdf._get_font(), 'B', 11)
            self.pdf.cell(0, 8, "Strategic Options", 0, 1)
            self.pdf.set_font(self.pdf._get_font(), '', 10)
            for i, option in enumerate(options[:3], 1):
                self.pdf.multi_cell(0, 5, self.pdf._safe_text(f"  {i}. {option}"))
            self.pdf.ln(3)
        
        # Milestones
        milestones = strategy.get('roadmap_milestones', [])
        if milestones:
            self.pdf.set_font(self.pdf._get_font(), 'B', 11)
            self.pdf.cell(0, 8, "Roadmap Milestones", 0, 1)
            self.pdf.set_font(self.pdf._get_font(), '', 10)
            for ms in milestones[:5]:
                self.pdf.cell(0, 5, self.pdf._safe_text(f"  [ ] {ms}"), 0, 1)
        
        self.pdf.ln(5)

    def _add_ip_proof(self, app_spec: Any):
        """Add IP attribution and proof section."""
        self.pdf.set_font(self.pdf._get_font(), '', 10)
        self.pdf.set_text_color(*PDFConfig.COLOR_BLACK)
        
        app_id = self._safe_get(app_spec, 'app_id', 'N/A')
        
        proof_text = f"""
App ID: {app_id}
Timestamp: {datetime.utcnow().isoformat()}
Methodology: Genesis Prompt Engineering v2.0
Framework: VerifiMind PEAS X-Z-CS Trinity
License: Proprietary / Creator Owned
Defensive Publication: DOI 10.5281/zenodo.17645665
Blockchain Status: Pending Minting (Polygon)
        """.strip()
        
        self.pdf.multi_cell(0, 5, self.pdf._safe_text(proof_text))

    def _add_no_data_message(self, message: str):
        """Add a 'no data available' message."""
        self.pdf.set_font(self.pdf._get_font(), '', 10)
        self.pdf.set_text_color(*PDFConfig.COLOR_MUTED)
        self.pdf.cell(0, 8, self.pdf._safe_text(message), 0, 1)
        self.pdf.ln(5)

    # =========================================================================
    # Helpers
    # =========================================================================

    def _safe_get(self, obj: Any, attr: str, default: Any = None) -> Any:
        """
        Safely get an attribute from an object or dict.
        
        Works with:
        - Dictionaries (uses .get())
        - Objects with attributes (uses getattr())
        - Nested paths like 'foo.bar' (not implemented, use separate calls)
        """
        if obj is None:
            return default
        
        if isinstance(obj, dict):
            return obj.get(attr, default)
        
        return getattr(obj, attr, default)

    def _get_status_color(self, status: str) -> tuple:
        """Get color tuple for status string."""
        status_upper = str(status).upper()
        
        if status_upper in ('SUCCESS', 'OK', 'PASS', 'GO'):
            return PDFConfig.COLOR_SUCCESS
        elif status_upper in ('WARNING', 'CAUTION', 'PIVOT'):
            return PDFConfig.COLOR_WARNING
        elif status_upper in ('ERROR', 'CRITICAL', 'FAIL', 'NO-GO', 'REJECT'):
            return PDFConfig.COLOR_DANGER
        else:
            return PDFConfig.COLOR_BLACK

    def _save_pdf(self, app_name: str) -> str:
        """Save PDF to output directory with timestamped filename."""
        # Sanitize app name for filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in app_name)
        safe_name = safe_name.replace(' ', '_')[:50]  # Limit length
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_Validation_Report_{timestamp}.pdf"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        filepath = os.path.join(self.output_dir, filename)
        self.pdf.output(filepath)
        
        return filepath


# =============================================================================
# Convenience Function
# =============================================================================

def generate_report(
    app_spec: Any,
    agent_results: Dict[str, Any],
    socratic_data: Dict[str, Any],
    output_dir: str = "output"
) -> str:
    """
    Convenience function to generate a report without class instantiation.
    
    Usage:
        path = generate_report(spec, results, socratic_data)
    """
    generator = ValidationReportGenerator(output_dir)
    return generator.generate(app_spec, agent_results, socratic_data)
