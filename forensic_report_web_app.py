#!/usr/bin/env python3
"""
Forensic Economic Report Generator - Web Application

Professional web-based interface for generating Kincaid Wolstein 
forensic economic reports with download capabilities.
"""

from flask import Flask, render_template, request, jsonify, send_file, session
import os
import json
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import secrets
import webbrowser
from werkzeug.serving import make_server
import time

# Import the template-based agent class
from forensic_report_agent_template import ForensicReportAgent, DatabaseConnector


class ReportWebApp:
    """Web application for professional forensic report generation."""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = secrets.token_hex(16)
        self.db = DatabaseConnector()
        self.current_reports = {}  # Store reports by session
        
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main application page."""
            return render_template('report_generator.html')
        
        @self.app.route('/api/evaluees')
        def get_evaluees():
            """API endpoint to get all evaluees."""
            try:
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, date_of_injury, occupation, 
                           date_of_birth, gender, pre_injury_earnings, post_injury_capacity
                    FROM evaluees ORDER BY name
                """)
                
                evaluees = []
                for row in cursor.fetchall():
                    evaluees.append({
                        'id': row[0],
                        'name': row[1],
                        'date_of_injury': row[2],
                        'occupation': row[3],
                        'date_of_birth': row[4],
                        'gender': row[5],
                        'pre_injury_earnings': row[6],
                        'post_injury_capacity': row[7]
                    })
                
                return jsonify({'success': True, 'evaluees': evaluees})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
            finally:
                if 'conn' in locals():
                    conn.close()
        
        @self.app.route('/api/evaluee/<int:evaluee_id>')
        def get_evaluee_details(evaluee_id):
            """API endpoint to get detailed evaluee information."""
            try:
                evaluee_data = self.db.get_evaluee_data(evaluee_id)
                if evaluee_data:
                    return jsonify({
                        'success': True,
                        'evaluee': {
                            'name': evaluee_data.name,
                            'date_of_birth': evaluee_data.date_of_birth,
                            'date_of_injury': evaluee_data.date_of_injury,
                            'gender': evaluee_data.gender,
                            'age_at_injury': evaluee_data.age_at_injury,
                            'current_age': evaluee_data.current_age,
                            'education_level': evaluee_data.education_level,
                            'occupation': evaluee_data.occupation,
                            'pre_injury_earnings': evaluee_data.pre_injury_earnings,
                            'post_injury_capacity': evaluee_data.post_injury_capacity,
                            'life_expectancy': evaluee_data.life_expectancy,
                            'work_life_expectancy': evaluee_data.work_life_expectancy
                        }
                    })
                else:
                    return jsonify({'success': False, 'error': 'Evaluee not found'})
                    
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/generate-report', methods=['POST'])
        def generate_report():
            """API endpoint to generate a forensic economic report."""
            try:
                data = request.get_json()
                evaluee_id = data.get('evaluee_id')
                
                if not evaluee_id:
                    return jsonify({'success': False, 'error': 'Evaluee ID required'})
                
                # Check API keys
                if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
                    return jsonify({
                        'success': False, 
                        'error': 'No AI API keys configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.'
                    })
                
                # Generate report in background thread
                session_id = session.get('session_id', secrets.token_hex(8))
                session['session_id'] = session_id
                
                def generate_in_background():
                    try:
                        agent = ForensicReportAgent("openai")
                        report = agent.generate_complete_report(evaluee_id)
                        
                        # Save report
                        evaluee_data = self.db.get_evaluee_data(evaluee_id)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        
                        # Store in session
                        self.current_reports[session_id] = {
                            'report': report,
                            'evaluee_name': evaluee_data.name if evaluee_data else f"Evaluee_{evaluee_id}",
                            'timestamp': timestamp,
                            'status': 'completed'
                        }
                        
                        # Auto-save to reports folder
                        reports_dir = Path("reports")
                        reports_dir.mkdir(exist_ok=True)
                        
                        filename = f"{evaluee_data.name}_Economic_Loss_Report_{timestamp}.txt"
                        safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                        
                        filepath = reports_dir / safe_filename
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(report)
                        
                        self.current_reports[session_id]['filepath'] = str(filepath)
                        
                    except Exception as e:
                        self.current_reports[session_id] = {
                            'status': 'error',
                            'error': str(e)
                        }
                
                # Mark as generating
                self.current_reports[session_id] = {'status': 'generating'}
                
                thread = threading.Thread(target=generate_in_background)
                thread.daemon = True
                thread.start()
                
                return jsonify({'success': True, 'session_id': session_id})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/report-status/<session_id>')
        def get_report_status(session_id):
            """API endpoint to check report generation status."""
            if session_id in self.current_reports:
                report_data = self.current_reports[session_id]
                
                if report_data['status'] == 'completed':
                    return jsonify({
                        'success': True,
                        'status': 'completed',
                        'report': report_data['report'],
                        'evaluee_name': report_data['evaluee_name'],
                        'timestamp': report_data['timestamp'],
                        'length': len(report_data['report'])
                    })
                elif report_data['status'] == 'error':
                    return jsonify({
                        'success': False,
                        'status': 'error',
                        'error': report_data['error']
                    })
                else:
                    return jsonify({
                        'success': True,
                        'status': 'generating'
                    })
            else:
                return jsonify({'success': False, 'error': 'Session not found'})
        
        @self.app.route('/api/download-report/<session_id>')
        def download_report(session_id):
            """API endpoint to download a generated report."""
            if session_id in self.current_reports:
                report_data = self.current_reports[session_id]
                
                if report_data['status'] == 'completed':
                    # Create temporary file for download
                    reports_dir = Path("reports")
                    reports_dir.mkdir(exist_ok=True)
                    
                    filename = f"{report_data['evaluee_name']}_Economic_Loss_Report_{report_data['timestamp']}.txt"
                    safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                    
                    filepath = reports_dir / safe_filename
                    
                    # Ensure file exists
                    if not filepath.exists():
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(report_data['report'])
                    
                    return send_file(
                        str(filepath),
                        as_attachment=True,
                        download_name=safe_filename,
                        mimetype='text/plain'
                    )
            
            return jsonify({'success': False, 'error': 'Report not found'})
    
    def run(self, host='127.0.0.1', port=5000, debug=False, open_browser=True):
        """Run the web application."""
        
        # Create templates directory and file if they don't exist
        self.create_template()
        
        if open_browser:
            # Open browser after a short delay
            def open_browser_delayed():
                time.sleep(1.5)
                webbrowser.open(f'http://{host}:{port}')
            
            thread = threading.Thread(target=open_browser_delayed)
            thread.daemon = True
            thread.start()
        
        print(f"🏢 Kincaid Wolstein Professional Report Generator")
        print(f"🌐 Starting web server at http://{host}:{port}")
        print(f"📊 Ready to generate forensic economic reports")
        
        self.app.run(host=host, port=port, debug=debug)
    
    def create_template(self):
        """Create the HTML template for the web interface."""
        templates_dir = Path("templates")
        templates_dir.mkdir(exist_ok=True)
        
        template_path = templates_dir / "report_generator.html"
        
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kincaid Wolstein - Professional Report Generator</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root {
            --kw-primary: #2c3e50;
            --kw-secondary: #3498db;
            --kw-success: #27ae60;
            --kw-light: #ecf0f1;
        }
        
        body {
            background-color: var(--kw-light);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .navbar-brand {
            font-weight: bold;
            color: var(--kw-primary) !important;
        }
        
        .professional-header {
            background: linear-gradient(135deg, var(--kw-primary), var(--kw-secondary));
            color: white;
            padding: 2rem 0;
        }
        
        .card {
            border: none;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-radius: 10px;
        }
        
        .card-header {
            background-color: var(--kw-primary);
            color: white;
            border-radius: 10px 10px 0 0 !important;
        }
        
        .btn-professional {
            background-color: var(--kw-primary);
            border-color: var(--kw-primary);
            color: white;
        }
        
        .btn-professional:hover {
            background-color: var(--kw-secondary);
            border-color: var(--kw-secondary);
            color: white;
        }
        
        .btn-download {
            background-color: var(--kw-success);
            border-color: var(--kw-success);
            color: white;
        }
        
        .btn-download:hover {
            background-color: #229954;
            border-color: #229954;
            color: white;
        }
        
        .report-preview {
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            max-height: 500px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
        }
        
        .status-bar {
            background-color: var(--kw-primary);
            color: white;
            padding: 0.5rem;
            border-radius: 5px;
            margin-top: 1rem;
        }
        
        .evaluee-detail {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
        }
        
        .spinner-container {
            text-align: center;
            padding: 2rem;
        }
        
        .progress-text {
            margin-top: 1rem;
            font-weight: bold;
            color: var(--kw-primary);
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
        <div class="container">
            <span class="navbar-brand">
                <i class="bi bi-building"></i>
                Kincaid Wolstein Vocational and Rehabilitation Services
            </span>
            <span class="navbar-text small text-muted">
                Professional Forensic Economic Report Generator v2.0
            </span>
        </div>
    </nav>

    <div class="professional-header">
        <div class="container text-center">
            <h1><i class="bi bi-file-earmark-text"></i> Professional Report Generator</h1>
            <p class="lead">Generate comprehensive forensic economic reports with professional formatting</p>
            <p class="mb-0">One University Plaza ~ Suite 302, Hackensack, NJ 07601 | (201) 343-0700</p>
        </div>
    </div>

    <div class="container mt-4">
        <!-- Case Selection -->
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0"><i class="bi bi-person-check"></i> Case Selection</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-10">
                        <label for="evalueeSelect" class="form-label fw-bold">Select Evaluee:</label>
                        <select class="form-select" id="evalueeSelect">
                            <option value="">Loading evaluees...</option>
                        </select>
                    </div>
                    <div class="col-md-2 d-flex align-items-end">
                        <button class="btn btn-outline-secondary" onclick="loadEvaluees()">
                            <i class="bi bi-arrow-clockwise"></i> Refresh
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Evaluee Details -->
        <div class="card mb-4" id="evalueeDetailsCard" style="display: none;">
            <div class="card-header">
                <h5 class="mb-0"><i class="bi bi-info-circle"></i> Evaluee Information</h5>
            </div>
            <div class="card-body">
                <div id="evalueeDetails" class="evaluee-detail">
                    <!-- Details will be populated here -->
                </div>
            </div>
        </div>

        <!-- Report Generation -->
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0"><i class="bi bi-gear"></i> Report Generation</h5>
            </div>
            <div class="card-body">
                <div class="d-flex gap-3 align-items-center">
                    <button class="btn btn-professional btn-lg" id="generateBtn" onclick="generateReport()" disabled>
                        <i class="bi bi-file-earmark-plus"></i> Generate Professional Report
                    </button>
                    <button class="btn btn-download" id="downloadBtn" onclick="downloadReport()" disabled>
                        <i class="bi bi-download"></i> Download Report
                    </button>
                    <div class="flex-grow-1">
                        <div class="progress" id="progressBar" style="display: none;">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                 role="progressbar" style="width: 100%"></div>
                        </div>
                    </div>
                </div>
                <div id="statusMessage" class="status-bar" style="display: none;">
                    Ready to generate reports
                </div>
            </div>
        </div>

        <!-- Report Preview -->
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0"><i class="bi bi-eye"></i> Report Preview</h5>
                <div class="input-group" style="width: 300px;">
                    <input type="text" class="form-control form-control-sm" id="searchInput" placeholder="Search report...">
                    <button class="btn btn-outline-secondary btn-sm" onclick="searchReport()">
                        <i class="bi bi-search"></i>
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div id="reportPreview" class="report-preview p-3">
                    <div class="text-center text-muted">
                        <h4><i class="bi bi-file-earmark-text-fill"></i></h4>
                        <p>Select an evaluee and generate a report to preview it here.</p>
                        <hr>
                        <p><strong>Professional Features:</strong></p>
                        <ul class="list-unstyled">
                            <li>✓ Kincaid Wolstein professional template</li>
                            <li>✓ Comprehensive economic loss analysis</li>
                            <li>✓ Daubert-compliant methodology</li>
                            <li>✓ Ready for litigation use</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="bg-dark text-white text-center py-3 mt-5">
        <div class="container">
            <p class="mb-0">© 2024 Kincaid Wolstein Vocational and Rehabilitation Services | Professional Forensic Economics</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentSessionId = null;
        let currentReport = '';

        // Load evaluees on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadEvaluees();
            updateStatus('Ready to generate professional forensic economic reports');
        });

        function loadEvaluees() {
            fetch('/api/evaluees')
                .then(response => response.json())
                .then(data => {
                    const select = document.getElementById('evalueeSelect');
                    select.innerHTML = '<option value="">Select an evaluee...</option>';
                    
                    if (data.success) {
                        data.evaluees.forEach(evaluee => {
                            const option = document.createElement('option');
                            option.value = evaluee.id;
                            option.textContent = `${evaluee.name} | DOI: ${evaluee.date_of_injury} | ${evaluee.occupation}`;
                            select.appendChild(option);
                        });
                        updateStatus(`Loaded ${data.evaluees.length} cases from database`);
                    } else {
                        updateStatus('Error loading evaluees: ' + data.error, 'error');
                    }
                })
                .catch(error => {
                    updateStatus('Error loading evaluees: ' + error, 'error');
                });
        }

        document.getElementById('evalueeSelect').addEventListener('change', function() {
            const evalueeId = this.value;
            if (evalueeId) {
                loadEvalueeDetails(evalueeId);
                document.getElementById('generateBtn').disabled = false;
            } else {
                document.getElementById('evalueeDetailsCard').style.display = 'none';
                document.getElementById('generateBtn').disabled = true;
            }
        });

        function loadEvalueeDetails(evalueeId) {
            fetch(`/api/evaluee/${evalueeId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const evaluee = data.evaluee;
                        const detailsHtml = `
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>Full Name:</strong> ${evaluee.name}</p>
                                    <p><strong>Date of Birth:</strong> ${evaluee.date_of_birth}</p>
                                    <p><strong>Date of Injury:</strong> ${evaluee.date_of_injury}</p>
                                    <p><strong>Gender:</strong> ${evaluee.gender}</p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>Age at Injury:</strong> ${evaluee.age_at_injury.toFixed(1)} years</p>
                                    <p><strong>Education:</strong> ${evaluee.education_level}</p>
                                    <p><strong>Occupation:</strong> ${evaluee.occupation}</p>
                                    <p><strong>Pre-injury Earnings:</strong> $${evaluee.pre_injury_earnings.toLocaleString()}</p>
                                </div>
                            </div>
                            <div class="alert alert-info">
                                <strong>Post-injury Capacity:</strong> ${evaluee.post_injury_capacity}
                            </div>
                        `;
                        
                        document.getElementById('evalueeDetails').innerHTML = detailsHtml;
                        document.getElementById('evalueeDetailsCard').style.display = 'block';
                        updateStatus(`Selected case: ${evaluee.name} - Ready to generate report`);
                    }
                })
                .catch(error => {
                    updateStatus('Error loading evaluee details: ' + error, 'error');
                });
        }

        function generateReport() {
            const evalueeId = document.getElementById('evalueeSelect').value;
            if (!evalueeId) {
                alert('Please select an evaluee first');
                return;
            }

            // Disable button and show progress
            document.getElementById('generateBtn').disabled = true;
            document.getElementById('downloadBtn').disabled = true;
            document.getElementById('progressBar').style.display = 'block';
            updateStatus('Generating professional forensic economic report...');

            fetch('/api/generate-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({evaluee_id: parseInt(evalueeId)})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentSessionId = data.session_id;
                    checkReportStatus();
                } else {
                    updateStatus('Error: ' + data.error, 'error');
                    resetGenerateButton();
                }
            })
            .catch(error => {
                updateStatus('Error generating report: ' + error, 'error');
                resetGenerateButton();
            });
        }

        function checkReportStatus() {
            if (!currentSessionId) return;

            fetch(`/api/report-status/${currentSessionId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (data.status === 'completed') {
                            currentReport = data.report;
                            document.getElementById('reportPreview').innerHTML = 
                                `<pre>${escapeHtml(data.report)}</pre>`;
                            
                            updateStatus(`Report generated successfully (${data.length.toLocaleString()} characters) - Ready for download`);
                            
                            document.getElementById('generateBtn').disabled = false;
                            document.getElementById('downloadBtn').disabled = false;
                            document.getElementById('progressBar').style.display = 'none';
                            
                            // Show success message
                            setTimeout(() => {
                                alert(`Professional forensic economic report generated successfully!\\n\\nReport Length: ${data.length.toLocaleString()} characters\\nCase: ${data.evaluee_name}\\n\\nUse 'Download Report' to save to your preferred location.`);
                            }, 500);
                            
                        } else if (data.status === 'generating') {
                            updateStatus('Generating report... Please wait');
                            setTimeout(checkReportStatus, 2000);
                        } else if (data.status === 'error') {
                            updateStatus('Error: ' + data.error, 'error');
                            resetGenerateButton();
                        }
                    } else {
                        updateStatus('Error checking status: ' + data.error, 'error');
                        resetGenerateButton();
                    }
                })
                .catch(error => {
                    updateStatus('Error checking status: ' + error, 'error');
                    resetGenerateButton();
                });
        }

        function downloadReport() {
            if (!currentSessionId) {
                alert('No report available to download');
                return;
            }

            window.location.href = `/api/download-report/${currentSessionId}`;
            updateStatus('Report download initiated');
        }

        function searchReport() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const reportText = document.getElementById('reportPreview').textContent;
            
            if (!searchTerm || !reportText) return;
            
            // Simple highlight implementation
            const highlightedText = reportText.replace(
                new RegExp(searchTerm, 'gi'),
                `<mark>$&</mark>`
            );
            
            document.getElementById('reportPreview').innerHTML = `<pre>${highlightedText}</pre>`;
        }

        function resetGenerateButton() {
            document.getElementById('generateBtn').disabled = false;
            document.getElementById('progressBar').style.display = 'none';
        }

        function updateStatus(message, type = 'info') {
            const statusElement = document.getElementById('statusMessage');
            const timestamp = new Date().toLocaleTimeString();
            statusElement.innerHTML = `[${timestamp}] ${message}`;
            statusElement.style.display = 'block';
            
            // Color coding
            if (type === 'error') {
                statusElement.style.backgroundColor = '#e74c3c';
            } else if (type === 'success') {
                statusElement.style.backgroundColor = '#27ae60';
            } else {
                statusElement.style.backgroundColor = 'var(--kw-primary)';
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>'''
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


def main():
    """Main function to run the web application."""
    
    # Check if database exists
    db_path = "/Users/chrisskerritt/EconomicAnalysis/instance/app.db"
    if not Path(db_path).exists():
        print(f"❌ Database not found at {db_path}")
        print("Please ensure the EconomicAnalysis application database exists.")
        print("Run: python run_professional_reports.py sample")
        return
    
    # Create reports directory
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Create and run web app
    app = ReportWebApp()
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=False, open_browser=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error running server: {e}")


if __name__ == "__main__":
    main()