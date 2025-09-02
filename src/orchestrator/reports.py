"""
Report generation system for benchmark results.
Supports JSON, HTML, and CSV output formats with visualizations.
"""

import os
import sys
import json
import csv
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import asdict

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.config import OutputConfig


class ReportGenerator:
    """Generates benchmark reports in multiple formats."""
    
    def __init__(self, output_config: OutputConfig):
        self.config = output_config
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure output directory exists
        os.makedirs(self.config.directory, exist_ok=True)
        
        print(f" Report generator initialized (output: {self.config.directory})")
    
    def generate_all_reports(self, performance_summary, formats: List[str] = None):
        """Generate reports in all requested formats."""
        if formats is None:
            formats = ['json', 'html', 'csv']
        
        print(f" Generating reports in formats: {', '.join(formats)}")
        
        generated_files = []
        
        for format_type in formats:
            try:
                if format_type.lower() == 'json':
                    file_path = self.generate_json_report(performance_summary)
                    generated_files.append(file_path)
                
                elif format_type.lower() == 'html':
                    file_path = self.generate_html_report(performance_summary)
                    generated_files.append(file_path)
                
                elif format_type.lower() == 'csv':
                    file_paths = self.generate_csv_reports(performance_summary)
                    generated_files.extend(file_paths)
                
                else:
                    print(f"  Unknown format: {format_type}")
            
            except Exception as e:
                print(f" Failed to generate {format_type} report: {e}")
        
        print(f" Reports generated: {len(generated_files)} files")
        for file_path in generated_files:
            print(f"   {os.path.basename(file_path)}")
        
        return generated_files
    
    def generate_json_report(self, performance_summary) -> str:
        """Generate JSON format report."""
        file_path = os.path.join(
            self.config.directory,
            f"benchmark_results_{self.timestamp}.json"
        )
        
        # Convert to serializable format
        report_data = self._prepare_json_data(performance_summary)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=self._json_serializer)
        
        print(f"   JSON report: {os.path.basename(file_path)}")
        return file_path
    
    def generate_html_report(self, performance_summary) -> str:
        """Generate HTML format report with visualizations."""
        file_path = os.path.join(
            self.config.directory,
            f"benchmark_report_{self.timestamp}.html"
        )
        
        html_content = self._generate_html_content(performance_summary)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"   HTML report: {os.path.basename(file_path)}")
        return file_path
    
    def generate_csv_reports(self, performance_summary) -> List[str]:
        """Generate CSV format reports."""
        file_paths = []
        
        # Generate comprehensive results CSV
        comprehensive_path = os.path.join(
            self.config.directory,
            f"benchmark_comprehensive_{self.timestamp}.csv"
        )
        self._generate_comprehensive_csv(performance_summary, comprehensive_path)
        file_paths.append(comprehensive_path)
        
        # Generate rankings CSV
        rankings_path = os.path.join(
            self.config.directory,
            f"benchmark_rankings_{self.timestamp}.csv"
        )
        self._generate_rankings_csv(performance_summary, rankings_path)
        file_paths.append(rankings_path)
        
        print(f"   CSV reports: {len(file_paths)} files")
        return file_paths
    
    def _prepare_json_data(self, performance_summary) -> Dict[str, Any]:
        """Prepare data for JSON serialization."""
        data = {
            'benchmark_info': {
                'benchmark_id': performance_summary.benchmark_id,
                'timestamp': performance_summary.timestamp.isoformat(),
                'execution_time': performance_summary.execution_time,
                'total_tests': performance_summary.total_tests,
                'total_languages': performance_summary.total_languages,
                'total_executions': performance_summary.total_executions
            },
            'configuration': performance_summary.configuration,
            'system_info': performance_summary.system_info,
            'summary_statistics': performance_summary.summary_statistics,
            'test_results': {},
            'overall_rankings': {
                'by_speed': performance_summary.overall_rankings.by_speed,
                'by_memory': performance_summary.overall_rankings.by_memory,
                'by_reliability': performance_summary.overall_rankings.by_reliability,
                'by_overall': performance_summary.overall_rankings.by_overall,
                'category_winners': performance_summary.overall_rankings.category_winners
            }
        }
        
        # Add test results
        for test_name, analysis in performance_summary.results.items():
            data['test_results'][test_name] = {
                'fastest_language': analysis.fastest_language,
                'most_memory_efficient': analysis.most_memory_efficient,
                'most_reliable': analysis.most_reliable,
                'performance_ranking': analysis.performance_ranking,
                'language_performances': {}
            }
            
            for language, perf in analysis.language_performances.items():
                data['test_results'][test_name]['language_performances'][language] = {
                    'avg_time': perf.avg_time,
                    'min_time': perf.min_time,
                    'max_time': perf.max_time,
                    'std_time': perf.std_time,
                    'median_time': perf.median_time,
                    'avg_memory': perf.avg_memory,
                    'peak_memory': perf.peak_memory,
                    'avg_cpu': perf.avg_cpu,
                    'max_cpu': perf.max_cpu,
                    'success_rate': perf.success_rate,
                    'total_iterations': perf.total_iterations,
                    'successful_iterations': perf.successful_iterations,
                    'performance_score': perf.performance_score,
                    'reliability_score': perf.reliability_score
                }
        
        return data
    
    def _generate_html_content(self, performance_summary) -> str:
        """Generate HTML report content."""
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Benchmark Report - {performance_summary.benchmark_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #007acc;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #007acc;
            margin: 0;
            font-size: 2.5em;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007acc;
        }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .metric-card .value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #007acc;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #007acc;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #007acc;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .language-python {{ color: #3776ab; }}
        .language-rust {{ color: #dea584; }}
        .language-go {{ color: #00add8; }}
        .language-typescript {{ color: #3178c6; }}
        .winner {{
            background-color: #d4edda !important;
            font-weight: bold;
        }}
        .performance-score {{
            padding: 4px 8px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
        }}
        .score-excellent {{ background-color: #28a745; }}
        .score-good {{ background-color: #17a2b8; }}
        .score-average {{ background-color: #ffc107; color: #333; }}
        .score-poor {{ background-color: #dc3545; }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1> Multi-Language Performance Benchmark</h1>
            <p>Benchmark ID: {performance_summary.benchmark_id}</p>
            <p>Generated: {performance_summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="metric-card">
                <h3> Total Tests</h3>
                <div class="value">{performance_summary.total_tests}</div>
            </div>
            <div class="metric-card">
                <h3> Languages</h3>
                <div class="value">{performance_summary.total_languages}</div>
            </div>
            <div class="metric-card">
                <h3> Executions</h3>
                <div class="value">{performance_summary.total_executions}</div>
            </div>
            <div class="metric-card">
                <h3> Duration</h3>
                <div class="value">{performance_summary.execution_time:.1f}s</div>
            </div>
        </div>
        
        {self._generate_rankings_html(performance_summary)}
        
        {self._generate_test_results_html(performance_summary)}
        
        <div class="footer">
            <p>Generated by Multi-Language Performance Benchmark Tool</p>
            <p>Report timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_template
    
    def _generate_rankings_html(self, performance_summary) -> str:
        """Generate HTML for overall rankings."""
        rankings = performance_summary.overall_rankings.by_overall
        
        if not rankings:
            return '<div class="section"><h2> Overall Rankings</h2><p>No ranking data available.</p></div>'
        
        html = '''
        <div class="section">
            <h2> Overall Performance Rankings</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Language</th>
                        <th>Performance Score</th>
                        <th>Performance Level</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for i, (language, score) in enumerate(rankings, 1):
            score_class = self._get_score_class(score)
            performance_level = self._get_performance_level(i)
            row_class = "winner" if i == 1 else ""
            
            html += f'''
                    <tr class="{row_class}">
                        <td>{i}</td>
                        <td class="language-{language}">{language.title()}</td>
                        <td><span class="performance-score {score_class}">{score:.2f}</span></td>
                        <td>{performance_level}</td>
                    </tr>
            '''
        
        html += '''
                </tbody>
            </table>
        </div>
        '''
        
        return html
    
    def _generate_test_results_html(self, performance_summary) -> str:
        """Generate HTML for individual test results."""
        if not performance_summary.results:
            return '<div class="section"><h2> Test Results</h2><p>No test results available.</p></div>'
        
        html = '<div class="section"><h2> Individual Test Results</h2>'
        
        for test_name, analysis in performance_summary.results.items():
            html += f'''
            <h3>Test: {test_name}</h3>
            <table>
                <thead>
                    <tr>
                        <th>Language</th>
                        <th>Avg Time (ms)</th>
                        <th>Memory (MB)</th>
                        <th>Success Rate</th>
                        <th>Performance Score</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
            '''
            
            # Sort by performance score
            sorted_perfs = sorted(
                analysis.language_performances.items(),
                key=lambda x: x[1].performance_score,
                reverse=True
            )
            
            for i, (language, perf) in enumerate(sorted_perfs):
                row_class = "winner" if i == 0 else ""
                score_class = self._get_score_class(perf.performance_score)
                
                avg_time_ms = perf.avg_time * 1000
                avg_memory_mb = perf.avg_memory / 1024 / 1024
                success_rate_pct = perf.success_rate * 100
                
                status = " Winner" if language == analysis.fastest_language else ""
                if language == analysis.most_memory_efficient:
                    status += "  Memory Efficient"
                if language == analysis.most_reliable:
                    status += "  Most Reliable"
                
                html += f'''
                        <tr class="{row_class}">
                            <td class="language-{language}">{language.title()}</td>
                            <td>{avg_time_ms:.2f}</td>
                            <td>{avg_memory_mb:.2f}</td>
                            <td>{success_rate_pct:.1f}%</td>
                            <td><span class="performance-score {score_class}">{perf.performance_score:.2f}</span></td>
                            <td>{status}</td>
                        </tr>
                '''
            
            html += '''
                    </tbody>
                </table>
            '''
        
        html += '</div>'
        return html
    
    def _generate_comprehensive_csv(self, performance_summary, file_path: str):
        """Generate comprehensive CSV report."""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Test', 'Language', 'Avg Time (ms)', 'Min Time (ms)', 'Max Time (ms)',
                'Std Dev (ms)', 'Median Time (ms)', 'Avg Memory (MB)', 'Peak Memory (MB)',
                'Avg CPU (%)', 'Max CPU (%)', 'Success Rate (%)', 'Total Iterations',
                'Successful Iterations', 'Performance Score', 'Reliability Score'
            ])
            
            # Data rows
            for test_name, analysis in performance_summary.results.items():
                for language, perf in analysis.language_performances.items():
                    writer.writerow([
                        test_name,
                        language,
                        round(perf.avg_time * 1000, 3),
                        round(perf.min_time * 1000, 3),
                        round(perf.max_time * 1000, 3),
                        round(perf.std_time * 1000, 3),
                        round(perf.median_time * 1000, 3),
                        round(perf.avg_memory / 1024 / 1024, 3),
                        round(perf.peak_memory / 1024 / 1024, 3),
                        round(perf.avg_cpu, 2),
                        round(perf.max_cpu, 2),
                        round(perf.success_rate * 100, 1),
                        perf.total_iterations,
                        perf.successful_iterations,
                        round(perf.performance_score, 2),
                        round(perf.reliability_score, 2)
                    ])
    
    def _generate_rankings_csv(self, performance_summary, file_path: str):
        """Generate rankings CSV report."""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Overall rankings
            writer.writerow(['Category', 'Rank', 'Language', 'Score'])
            
            categories = [
                ('Overall', performance_summary.overall_rankings.by_overall),
                ('Speed', performance_summary.overall_rankings.by_speed),
                ('Memory', performance_summary.overall_rankings.by_memory),
                ('Reliability', performance_summary.overall_rankings.by_reliability)
            ]
            
            for category_name, rankings in categories:
                for i, (language, score) in enumerate(rankings, 1):
                    writer.writerow([category_name, i, language, round(score, 2)])
    
    def _get_score_class(self, score: float) -> str:
        """Get CSS class for performance score."""
        if score >= 80:
            return "score-excellent"
        elif score >= 60:
            return "score-good"
        elif score >= 40:
            return "score-average"
        else:
            return "score-poor"
    
    def _get_performance_level(self, rank: int) -> str:
        """Get performance level description."""
        if rank == 1:
            return " Excellent"
        elif rank == 2:
            return " Very Good"
        elif rank == 3:
            return " Good"
        elif rank <= 5:
            return " Average"
        else:
            return " Below Average"
    
    def _json_serializer(self, obj):
        """JSON serializer for datetime and other objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


if __name__ == "__main__":
    # Test report generator
    from utils.config import OutputConfig
    
    config = OutputConfig()
    generator = ReportGenerator(config)
    print("Report generator test completed")