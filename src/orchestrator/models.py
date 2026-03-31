"""
Shared data models for the benchmark orchestrator.
Consolidates dataclasses used across different modules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple


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
    performance_ranking: List[Tuple[str, float]] = field(default_factory=list)
    statistical_significance: Dict[str, Dict[str, float]] = field(default_factory=dict)


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
    language_versions: Dict[str, str] = field(default_factory=dict)
