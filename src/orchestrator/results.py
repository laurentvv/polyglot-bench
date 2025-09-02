"""
Results compilation and analysis system.
Aggregates raw benchmark results and generates performance analysis.
"""

import os
import sys
import statistics
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import math

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


@dataclass
class TestResult:
    """Single test execution result."""
    execution_time: float
    memory_usage: int
    cpu_usage: float
    output: str
    error: str
    success: bool
    language: str
    test_name: str
    iteration: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LanguagePerformance:
    """Aggregated performance metrics for a language on a specific test."""
    language: str
    test_name: str
    avg_time: float
    min_time: float
    max_time: float
    std_time: float
    median_time: float
    avg_memory: float
    peak_memory: int
    min_memory: int
    avg_cpu: float
    max_cpu: float
    success_rate: float
    total_iterations: int
    successful_iterations: int
    performance_score: float = 0.0
    reliability_score: float = 0.0


@dataclass
class TestAnalysis:
    """Analysis results for a specific test across all languages."""
    test_name: str
    language_performances: Dict[str, LanguagePerformance]
    fastest_language: str
    most_memory_efficient: str
    most_reliable: str
    performance_ranking: List[Tuple[str, float]]  # (language, score)
    statistical_significance: Dict[str, Dict[str, float]]  # language comparisons


@dataclass
class OverallRankings:
    """Overall performance rankings across all tests."""
    by_speed: List[Tuple[str, float]]  # (language, avg_score)
    by_memory: List[Tuple[str, float]]
    by_reliability: List[Tuple[str, float]]
    by_overall: List[Tuple[str, float]]
    category_winners: Dict[str, str]  # test_category -> best_language


@dataclass
class PerformanceSummary:
    """Complete benchmark performance summary."""
    benchmark_id: str
    timestamp: datetime
    total_tests: int
    total_languages: int
    total_executions: int
    results: Dict[str, TestAnalysis]
    overall_rankings: OverallRankings
    execution_time: float
    system_info: Dict[str, Any]
    configuration: Dict[str, Any]
    summary_statistics: Dict[str, Any]


class ResultsCompiler:
    """Compiles and analyzes raw benchmark results."""
    
    def __init__(self):
        self.performance_weights = {
            'time': 0.7,
            'memory': 0.2,
            'reliability': 0.1
        }
        print(" Results compiler initialized")
    
    def compile_results(self, raw_results: Dict[str, Dict[str, List[TestResult]]], 
                       benchmark_id: str, execution_time: float,
                       system_info: Dict[str, Any] = None,
                       configuration: Dict[str, Any] = None) -> PerformanceSummary:
        """Compile raw results into performance summary."""
        print(" Compiling benchmark results...")
        
        if not raw_results:
            raise ValueError("No raw results provided")
        
        # Analyze each test
        test_analyses = {}
        total_executions = 0
        
        for test_name, language_results in raw_results.items():
            print(f"  Analyzing {test_name}...")
            
            test_analysis = self._analyze_test_results(test_name, language_results)
            test_analyses[test_name] = test_analysis
            
            # Count total executions
            for lang_results in language_results.values():
                total_executions += len(lang_results)
        
        # Calculate overall rankings
        print("  Calculating overall rankings...")
        overall_rankings = self._calculate_overall_rankings(test_analyses)
        
        # Generate summary statistics
        summary_stats = self._generate_summary_statistics(test_analyses, raw_results)
        
        performance_summary = PerformanceSummary(
            benchmark_id=benchmark_id,
            timestamp=datetime.now(),
            total_tests=len(test_analyses),
            total_languages=len(self._get_all_languages(raw_results)),
            total_executions=total_executions,
            results=test_analyses,
            overall_rankings=overall_rankings,
            execution_time=execution_time,
            system_info=system_info or {},
            configuration=configuration or {},
            summary_statistics=summary_stats
        )
        
        print(f" Results compiled: {len(test_analyses)} tests, {total_executions} executions")
        return performance_summary
    
    def _analyze_test_results(self, test_name: str, 
                            language_results: Dict[str, List[TestResult]]) -> TestAnalysis:
        """Analyze results for a specific test across languages."""
        language_performances = {}
        
        for language, results in language_results.items():
            if not results:
                continue
            
            performance = self._calculate_language_performance(language, test_name, results)
            language_performances[language] = performance
        
        # Determine winners
        fastest_language = self._find_fastest_language(language_performances)
        most_memory_efficient = self._find_most_memory_efficient(language_performances)
        most_reliable = self._find_most_reliable(language_performances)
        
        # Calculate performance ranking
        performance_ranking = self._rank_languages_by_performance(language_performances)
        
        # Calculate statistical significance
        statistical_significance = self._calculate_statistical_significance(language_results)
        
        return TestAnalysis(
            test_name=test_name,
            language_performances=language_performances,
            fastest_language=fastest_language,
            most_memory_efficient=most_memory_efficient,
            most_reliable=most_reliable,
            performance_ranking=performance_ranking,
            statistical_significance=statistical_significance
        )
    
    def _calculate_language_performance(self, language: str, test_name: str, 
                                      results: List[TestResult]) -> LanguagePerformance:
        """Calculate performance metrics for a language on a specific test."""
        if not results:
            return LanguagePerformance(
                language=language,
                test_name=test_name,
                avg_time=0, min_time=0, max_time=0, std_time=0, median_time=0,
                avg_memory=0, peak_memory=0, min_memory=0,
                avg_cpu=0, max_cpu=0,
                success_rate=0, total_iterations=0, successful_iterations=0
            )
        
        # Filter successful results for performance calculations
        successful_results = [r for r in results if r.success]
        total_iterations = len(results)
        successful_iterations = len(successful_results)
        
        if successful_results:
            # Time metrics
            times = [r.execution_time for r in successful_results]
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            std_time = statistics.stdev(times) if len(times) > 1 else 0.0
            median_time = statistics.median(times)
            
            # Memory metrics
            memories = [r.memory_usage for r in successful_results if r.memory_usage > 0]
            avg_memory = statistics.mean(memories) if memories else 0.0
            peak_memory = max(memories) if memories else 0
            min_memory = min(memories) if memories else 0
            
            # CPU metrics
            cpu_usages = [r.cpu_usage for r in successful_results if r.cpu_usage > 0]
            avg_cpu = statistics.mean(cpu_usages) if cpu_usages else 0.0
            max_cpu = max(cpu_usages) if cpu_usages else 0.0
        else:
            # No successful results
            avg_time = min_time = max_time = std_time = median_time = 0.0
            avg_memory = peak_memory = min_memory = 0
            avg_cpu = max_cpu = 0.0
        
        success_rate = successful_iterations / total_iterations if total_iterations > 0 else 0.0
        
        # Calculate composite scores
        performance_score = self._calculate_performance_score(avg_time, avg_memory, success_rate)
        reliability_score = self._calculate_reliability_score(success_rate, std_time)
        
        return LanguagePerformance(
            language=language,
            test_name=test_name,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_time=std_time,
            median_time=median_time,
            avg_memory=avg_memory,
            peak_memory=peak_memory,
            min_memory=min_memory,
            avg_cpu=avg_cpu,
            max_cpu=max_cpu,
            success_rate=success_rate,
            total_iterations=total_iterations,
            successful_iterations=successful_iterations,
            performance_score=performance_score,
            reliability_score=reliability_score
        )
    
    def _calculate_performance_score(self, avg_time: float, avg_memory: float, 
                                   success_rate: float) -> float:
        """Calculate normalized performance score (higher is better)."""
        if avg_time <= 0:
            return 0.0
        
        # Normalize execution time (lower is better, so invert)
        time_score = 1000.0 / (avg_time * 1000)  # Convert to ms and invert
        
        # Normalize memory usage (lower is better, so invert)
        memory_score = 100.0 / max(avg_memory / 1024 / 1024, 1.0)  # Convert to MB and invert
        
        # Weight and combine scores
        total_score = (
            time_score * self.performance_weights['time'] +
            memory_score * self.performance_weights['memory'] +
            success_rate * 100 * self.performance_weights['reliability']
        )
        
        return total_score
    
    def _calculate_reliability_score(self, success_rate: float, std_time: float) -> float:
        """Calculate reliability score based on success rate and consistency."""
        consistency_score = 1.0 / (1.0 + std_time)  # Lower std deviation = higher consistency
        return (success_rate * 0.8) + (consistency_score * 0.2)
    
    def _find_fastest_language(self, language_performances: Dict[str, LanguagePerformance]) -> str:
        """Find the language with the fastest average execution time."""
        if not language_performances:
            return ""
        
        fastest = min(
            language_performances.items(),
            key=lambda x: x[1].avg_time if x[1].successful_iterations > 0 else float('inf')
        )
        
        return fastest[0] if fastest[1].successful_iterations > 0 else ""
    
    def _find_most_memory_efficient(self, language_performances: Dict[str, LanguagePerformance]) -> str:
        """Find the language with the lowest memory usage."""
        if not language_performances:
            return ""
        
        most_efficient = min(
            language_performances.items(),
            key=lambda x: x[1].avg_memory if x[1].successful_iterations > 0 else float('inf')
        )
        
        return most_efficient[0] if most_efficient[1].successful_iterations > 0 else ""
    
    def _find_most_reliable(self, language_performances: Dict[str, LanguagePerformance]) -> str:
        """Find the language with the highest success rate."""
        if not language_performances:
            return ""
        
        most_reliable = max(
            language_performances.items(),
            key=lambda x: x[1].success_rate
        )
        
        return most_reliable[0]
    
    def _rank_languages_by_performance(self, 
                                     language_performances: Dict[str, LanguagePerformance]) -> List[Tuple[str, float]]:
        """Rank languages by overall performance score."""
        rankings = [
            (lang, perf.performance_score)
            for lang, perf in language_performances.items()
            if perf.successful_iterations > 0
        ]
        
        return sorted(rankings, key=lambda x: x[1], reverse=True)
    
    def _calculate_statistical_significance(self, 
                                          language_results: Dict[str, List[TestResult]]) -> Dict[str, Dict[str, float]]:
        """Calculate statistical significance between language pairs."""
        significance = {}
        
        languages = list(language_results.keys())
        
        for i, lang1 in enumerate(languages):
            significance[lang1] = {}
            
            for j, lang2 in enumerate(languages):
                if i != j:
                    # Get successful execution times
                    times1 = [r.execution_time for r in language_results[lang1] if r.success]
                    times2 = [r.execution_time for r in language_results[lang2] if r.success]
                    
                    if len(times1) > 1 and len(times2) > 1:
                        # Simple t-test approximation
                        significance[lang1][lang2] = self._calculate_t_test_p_value(times1, times2)
                    else:
                        significance[lang1][lang2] = 1.0  # No significance
        
        return significance
    
    def _calculate_t_test_p_value(self, sample1: List[float], sample2: List[float]) -> float:
        """Calculate approximate p-value for two-sample t-test."""
        if len(sample1) < 2 or len(sample2) < 2:
            return 1.0
        
        try:
            mean1, mean2 = statistics.mean(sample1), statistics.mean(sample2)
            var1, var2 = statistics.variance(sample1), statistics.variance(sample2)
            n1, n2 = len(sample1), len(sample2)
            
            # Welch's t-test
            pooled_se = math.sqrt(var1/n1 + var2/n2)
            t_stat = abs(mean1 - mean2) / pooled_se if pooled_se > 0 else 0
            
            # Approximate p-value (simplified)
            # For more accurate results, use scipy.stats.ttest_ind
            p_value = 2 * (1 - self._approximate_t_cdf(t_stat, min(n1, n2) - 1))
            
            return max(0.0, min(1.0, p_value))
        except Exception:
            return 1.0
    
    def _approximate_t_cdf(self, t: float, df: int) -> float:
        """Rough approximation of t-distribution CDF."""
        # Very rough approximation - for production use scipy.stats
        if df >= 30:
            # Approximate as normal distribution
            return 0.5 * (1 + math.erf(t / math.sqrt(2)))
        else:
            # Simple approximation
            return max(0.0, min(1.0, 0.5 + t / (2 * math.sqrt(df + t*t))))
    
    def _calculate_overall_rankings(self, 
                                  test_analyses: Dict[str, TestAnalysis]) -> OverallRankings:
        """Calculate overall performance rankings across all tests."""
        # Collect all languages
        all_languages = set()
        for analysis in test_analyses.values():
            all_languages.update(analysis.language_performances.keys())
        
        all_languages = list(all_languages)
        
        # Calculate average scores by category
        speed_scores = {lang: [] for lang in all_languages}
        memory_scores = {lang: [] for lang in all_languages}
        reliability_scores = {lang: [] for lang in all_languages}
        overall_scores = {lang: [] for lang in all_languages}
        
        for analysis in test_analyses.values():
            for lang in all_languages:
                if lang in analysis.language_performances:
                    perf = analysis.language_performances[lang]
                    
                    if perf.successful_iterations > 0:
                        # Speed score (inverse of time)
                        speed_score = 1000.0 / (perf.avg_time * 1000) if perf.avg_time > 0 else 0
                        speed_scores[lang].append(speed_score)
                        
                        # Memory score (inverse of memory usage)
                        memory_score = 100.0 / max(perf.avg_memory / 1024 / 1024, 1.0)
                        memory_scores[lang].append(memory_score)
                        
                        # Reliability score
                        reliability_scores[lang].append(perf.reliability_score * 100)
                        
                        # Overall score
                        overall_scores[lang].append(perf.performance_score)
        
        # Calculate averages and create rankings
        by_speed = self._create_ranking(speed_scores)
        by_memory = self._create_ranking(memory_scores)
        by_reliability = self._create_ranking(reliability_scores)
        by_overall = self._create_ranking(overall_scores)
        
        # Determine category winners
        category_winners = {}
        for test_name, analysis in test_analyses.items():
            if analysis.performance_ranking:
                category_winners[test_name] = analysis.performance_ranking[0][0]
        
        return OverallRankings(
            by_speed=by_speed,
            by_memory=by_memory,
            by_reliability=by_reliability,
            by_overall=by_overall,
            category_winners=category_winners
        )
    
    def _create_ranking(self, scores_by_language: Dict[str, List[float]]) -> List[Tuple[str, float]]:
        """Create ranking from scores by language."""
        avg_scores = []
        
        for lang, scores in scores_by_language.items():
            if scores:
                avg_score = statistics.mean(scores)
                avg_scores.append((lang, avg_score))
        
        return sorted(avg_scores, key=lambda x: x[1], reverse=True)
    
    def _get_all_languages(self, raw_results: Dict[str, Dict[str, List[TestResult]]]) -> List[str]:
        """Get all unique languages from raw results."""
        all_languages = set()
        for language_results in raw_results.values():
            all_languages.update(language_results.keys())
        return list(all_languages)
    
    def _generate_summary_statistics(self, test_analyses: Dict[str, TestAnalysis],
                                   raw_results: Dict[str, Dict[str, List[TestResult]]]) -> Dict[str, Any]:
        """Generate summary statistics for the benchmark run."""
        total_successful = 0
        total_failed = 0
        
        for language_results in raw_results.values():
            for results in language_results.values():
                for result in results:
                    if result.success:
                        total_successful += 1
                    else:
                        total_failed += 1
        
        overall_success_rate = total_successful / (total_successful + total_failed) if (total_successful + total_failed) > 0 else 0
        
        return {
            'total_successful_executions': total_successful,
            'total_failed_executions': total_failed,
            'overall_success_rate': overall_success_rate,
            'tests_analyzed': len(test_analyses),
            'languages_tested': len(self._get_all_languages(raw_results))
        }


if __name__ == "__main__":
    # Test results compiler
    compiler = ResultsCompiler()
    print("Results compiler test completed")