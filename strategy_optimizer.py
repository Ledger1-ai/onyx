#!/usr/bin/env python3
"""
Strategy Optimizer for Intelligent Twitter Agent
===============================================
Optimizes strategies based on performance data and applies intelligent adjustments.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import statistics
from collections import defaultdict, Counter

from data_models import (
    StrategyTemplate, OptimizationRule, PerformanceAnalysis, TweetPerformance,
    ActivityType, PerformanceMetric, EngagementSession, create_default_strategy
)
from database_manager import DatabaseManager
from performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

class StrategyOptimizer:
    """Optimizes social media strategy based on performance data"""
    
    def __init__(self, db_manager: DatabaseManager, performance_tracker: PerformanceTracker):
        """Initialize strategy optimizer"""
        self.db = db_manager
        self.performance_tracker = performance_tracker
        
        # Optimization parameters
        self.min_data_points = 3  # Minimum days of data needed for optimization
        self.significance_threshold = 0.1  # 10% improvement threshold
        self.max_adjustments_per_optimization = 5
        
        # Strategy adjustment limits (prevent extreme changes)
        self.adjustment_limits = {
            "activity_distribution": 0.2,  # Max 20% change in activity distribution
            "posting_frequency": 0.5,      # Max 50% change in posting frequency
            "timing_shift": 3              # Max 3 hour shift in posting times
        }
        
        logger.info("Strategy Optimizer initialized")
    
    def optimize_strategy(self, strategy_name: str, days_of_data: int = 7) -> Dict[str, Any]:
        """Optimize a strategy based on recent performance data"""
        try:
            # Get current strategy
            strategy = self.db.get_strategy_template(strategy_name)
            if not strategy:
                logger.error(f"Strategy '{strategy_name}' not found")
                return {"error": "Strategy not found"}
            
            # Collect performance data
            performance_data = self._collect_performance_data(days_of_data)
            
            if len(performance_data) < self.min_data_points:
                logger.warning(f"Insufficient data for optimization: {len(performance_data)} days")
                return {"error": "Insufficient performance data"}
            
            # Analyze current strategy performance
            strategy_analysis = self._analyze_strategy_performance(strategy, performance_data)
            
            # Generate optimization recommendations
            optimizations = self._generate_optimizations(strategy, strategy_analysis)
            
            # Apply optimizations if they meet significance threshold
            optimization_results = self._apply_optimizations(strategy, optimizations)
            
            # Create optimization report
            report = {
                "strategy_name": strategy_name,
                "optimization_date": datetime.now().isoformat(),
                "data_period_days": days_of_data,
                "performance_analysis": strategy_analysis,
                "optimizations_applied": optimization_results,
                "success": len(optimization_results) > 0
            }
            
            logger.info(f"Strategy optimization completed for {strategy_name}: {len(optimization_results)} changes applied")
            return report
            
        except Exception as e:
            logger.error(f"Error optimizing strategy: {e}")
            return {"error": str(e)}
    
    def _collect_performance_data(self, days: int) -> List[Dict[str, Any]]:
        """Collect performance data for the specified number of days"""
        performance_data = []
        
        try:
            end_date = datetime.now()
            
            for i in range(days):
                current_date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
                
                # Get daily performance analysis
                analysis = self.db.get_performance_analysis(current_date)
                if analysis:
                    # Get tweet performances for the day
                    tweets = self.db.get_tweet_performances_by_date(current_date)
                    
                    # Get engagement sessions
                    sessions = self.db.get_recent_engagement_sessions(24)
                    date_sessions = [s for s in sessions 
                                   if s.start_time.strftime("%Y-%m-%d") == current_date]
                    
                    day_data = {
                        "date": current_date,
                        "analysis": analysis,
                        "tweets": tweets,
                        "sessions": date_sessions,
                        "metrics": analysis.metrics
                    }
                    
                    performance_data.append(day_data)
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Error collecting performance data: {e}")
            return []
    
    def _analyze_strategy_performance(self, strategy: StrategyTemplate, 
                                    performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how well the current strategy is performing"""
        analysis = {
            "target_achievement": {},
            "activity_effectiveness": {},
            "timing_analysis": {},
            "content_analysis": {},
            "trend_analysis": {},
            "problem_areas": []
        }
        
        try:
            # Target achievement analysis
            analysis["target_achievement"] = self._analyze_target_achievement(strategy, performance_data)
            
            # Activity effectiveness analysis
            analysis["activity_effectiveness"] = self._analyze_activity_effectiveness(performance_data)
            
            # Timing analysis
            analysis["timing_analysis"] = self._analyze_posting_timing(strategy, performance_data)
            
            # Content analysis
            analysis["content_analysis"] = self._analyze_content_performance(strategy, performance_data)
            
            # Trend analysis
            analysis["trend_analysis"] = self._analyze_performance_trends(performance_data)
            
            # Identify problem areas
            analysis["problem_areas"] = self._identify_problem_areas(strategy, analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing strategy performance: {e}")
            
        return analysis
    
    def _analyze_target_achievement(self, strategy: StrategyTemplate, 
                                  performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how well strategy targets are being achieved"""
        achievement = {}
        
        try:
            # Calculate average metrics over the period
            metric_values = defaultdict(list)
            
            for day_data in performance_data:
                for metric, value in day_data["metrics"].items():
                    metric_values[metric].append(value)
            
            # Compare with strategy targets
            for metric_enum, target_value in strategy.target_metrics.items():
                metric_name = metric_enum.value
                
                if metric_name in metric_values:
                    actual_values = metric_values[metric_name]
                    avg_actual = statistics.mean(actual_values)
                    
                    achievement_rate = (avg_actual / target_value) if target_value > 0 else 0
                    
                    achievement[metric_name] = {
                        "target": target_value,
                        "actual_average": avg_actual,
                        "achievement_rate": achievement_rate,
                        "status": "exceeds" if achievement_rate > 1.1 else 
                                "meets" if achievement_rate > 0.9 else "below"
                    }
            
        except Exception as e:
            logger.error(f"Error analyzing target achievement: {e}")
            
        return achievement
    
    def _analyze_activity_effectiveness(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze effectiveness of different activities"""
        effectiveness = {}
        
        try:
            # Aggregate activity data across all days
            activity_metrics = defaultdict(lambda: {
                "sessions": 0,
                "total_interactions": 0,
                "total_duration": 0,
                "quality_scores": []
            })
            
            for day_data in performance_data:
                for session in day_data["sessions"]:
                    activity = session.activity_type.value
                    
                    activity_metrics[activity]["sessions"] += 1
                    activity_metrics[activity]["total_interactions"] += sum(session.interactions_made.values())
                    
                    if session.end_time:
                        duration = (session.end_time - session.start_time).total_seconds() / 60
                        activity_metrics[activity]["total_duration"] += duration
                    
                    activity_metrics[activity]["quality_scores"].append(session.engagement_quality_score)
            
            # Calculate effectiveness metrics
            for activity, metrics in activity_metrics.items():
                if metrics["sessions"] > 0:
                    avg_quality = statistics.mean(metrics["quality_scores"])
                    interactions_per_session = metrics["total_interactions"] / metrics["sessions"]
                    
                    effectiveness[activity] = {
                        "total_sessions": metrics["sessions"],
                        "avg_interactions_per_session": interactions_per_session,
                        "avg_quality_score": avg_quality,
                        "total_duration_hours": metrics["total_duration"] / 60,
                        "effectiveness_score": (interactions_per_session * avg_quality),
                        "roi_score": metrics["total_interactions"] / max(metrics["total_duration"], 1)
                    }
            
        except Exception as e:
            logger.error(f"Error analyzing activity effectiveness: {e}")
            
        return effectiveness
    
    def _analyze_posting_timing(self, strategy: StrategyTemplate, 
                              performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze posting timing effectiveness"""
        timing_analysis = {}
        
        try:
            # Collect tweet timing and performance data
            hourly_performance = defaultdict(list)
            
            for day_data in performance_data:
                for tweet in day_data["tweets"]:
                    if tweet.posting_time:
                        hour = tweet.posting_time.hour
                        
                        # Calculate engagement rate
                        if tweet.engagement_data.impressions > 0:
                            engagement_rate = ((tweet.engagement_data.likes + 
                                              tweet.engagement_data.retweets + 
                                              tweet.engagement_data.replies) / 
                                             tweet.engagement_data.impressions)
                            hourly_performance[hour].append(engagement_rate)
            
            # Calculate average performance by hour
            hourly_averages = {}
            for hour, rates in hourly_performance.items():
                if rates:
                    hourly_averages[hour] = statistics.mean(rates)
            
            timing_analysis["hourly_performance"] = hourly_averages
            
            # Compare with strategy's optimal times
            strategy_hours = []
            for time_str in strategy.optimal_posting_times:
                try:
                    hour = int(time_str.split(":")[0])
                    strategy_hours.append(hour)
                except:
                    continue
            
            # Analyze strategy time effectiveness
            strategy_time_performance = []
            all_time_performance = []
            
            for hour, avg_performance in hourly_averages.items():
                if hour in strategy_hours:
                    strategy_time_performance.append(avg_performance)
                all_time_performance.append(avg_performance)
            
            timing_analysis["strategy_times_effectiveness"] = {
                "strategy_avg": statistics.mean(strategy_time_performance) if strategy_time_performance else 0,
                "overall_avg": statistics.mean(all_time_performance) if all_time_performance else 0,
                "relative_performance": (statistics.mean(strategy_time_performance) / 
                                       statistics.mean(all_time_performance)) if all_time_performance and strategy_time_performance else 1
            }
            
            # Identify best performing hours
            if hourly_averages:
                best_hours = sorted(hourly_averages.items(), key=lambda x: x[1], reverse=True)[:3]
                timing_analysis["best_performing_hours"] = [hour for hour, _ in best_hours]
            
        except Exception as e:
            logger.error(f"Error analyzing posting timing: {e}")
            
        return timing_analysis
    
    def _analyze_content_performance(self, strategy: StrategyTemplate, 
                                   performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content type and format performance"""
        content_analysis = {}
        
        try:
            # Analyze content type performance
            content_type_performance = defaultdict(list)
            hashtag_performance = defaultdict(list)
            
            for day_data in performance_data:
                for tweet in day_data["tweets"]:
                    if tweet.engagement_data.impressions > 0:
                        engagement_rate = ((tweet.engagement_data.likes + 
                                          tweet.engagement_data.retweets + 
                                          tweet.engagement_data.replies) / 
                                         tweet.engagement_data.impressions)
                        
                        # Content type analysis
                        content_type_performance[tweet.content_type].append(engagement_rate)
                        
                        # Hashtag analysis
                        for hashtag in tweet.hashtags:
                            hashtag_performance[hashtag].append(engagement_rate)
            
            # Calculate averages
            content_type_avg = {}
            for content_type, rates in content_type_performance.items():
                content_type_avg[content_type] = statistics.mean(rates)
            
            content_analysis["content_type_performance"] = content_type_avg
            
            # Compare with strategy content mix
            strategy_content_performance = {}
            for content_type, target_percentage in strategy.content_mix.items():
                actual_performance = content_type_avg.get(content_type, 0)
                strategy_content_performance[content_type] = {
                    "target_percentage": target_percentage,
                    "actual_performance": actual_performance,
                    "effectiveness": actual_performance / max(statistics.mean(content_type_avg.values()), 0.001)
                }
            
            content_analysis["strategy_content_effectiveness"] = strategy_content_performance
            
            # Hashtag effectiveness
            hashtag_avg = {}
            for hashtag, rates in hashtag_performance.items():
                if len(rates) >= 2:  # Only include hashtags used multiple times
                    hashtag_avg[hashtag] = statistics.mean(rates)
            
            content_analysis["hashtag_performance"] = hashtag_avg
            
            # Compare with strategy hashtags
            strategy_hashtag_performance = {}
            for hashtag in strategy.hashtag_strategy:
                performance = hashtag_avg.get(hashtag, 0)
                strategy_hashtag_performance[hashtag] = {
                    "performance": performance,
                    "effectiveness": performance / max(statistics.mean(hashtag_avg.values()), 0.001) if hashtag_avg else 0
                }
            
            content_analysis["strategy_hashtag_effectiveness"] = strategy_hashtag_performance
            
        except Exception as e:
            logger.error(f"Error analyzing content performance: {e}")
            
        return content_analysis
    
    def _analyze_performance_trends(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        trends = {}
        
        try:
            # Sort data by date
            sorted_data = sorted(performance_data, key=lambda x: x["date"])
            
            # Extract key metrics over time
            metric_trends = defaultdict(list)
            
            for day_data in sorted_data:
                for metric, value in day_data["metrics"].items():
                    metric_trends[metric].append(value)
            
            # Calculate trend direction and strength for each metric
            for metric, values in metric_trends.items():
                if len(values) >= 3:
                    # Simple trend calculation
                    first_half = values[:len(values)//2]
                    second_half = values[len(values)//2:]
                    
                    first_avg = statistics.mean(first_half)
                    second_avg = statistics.mean(second_half)
                    
                    if first_avg > 0:
                        change_percent = ((second_avg - first_avg) / first_avg) * 100
                    else:
                        change_percent = 0
                    
                    if abs(change_percent) > 10:
                        direction = "improving" if change_percent > 0 else "declining"
                    else:
                        direction = "stable"
                    
                    trends[metric] = {
                        "direction": direction,
                        "change_percent": change_percent,
                        "trend_strength": abs(change_percent) / 10,  # Normalize to 0-1+ scale
                        "current_value": values[-1],
                        "volatility": statistics.stdev(values) if len(values) > 1 else 0
                    }
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
            
        return trends
    
    def _identify_problem_areas(self, strategy: StrategyTemplate, analysis: Dict[str, Any]) -> List[str]:
        """Identify areas where the strategy is underperforming"""
        problems = []
        
        try:
            # Check target achievement
            target_achievement = analysis.get("target_achievement", {})
            for metric, achievement_data in target_achievement.items():
                if achievement_data["status"] == "below":
                    problems.append(f"Underperforming on {metric}: {achievement_data['achievement_rate']:.2%} of target")
            
            # Check activity effectiveness
            activity_effectiveness = analysis.get("activity_effectiveness", {})
            if activity_effectiveness:
                avg_effectiveness = statistics.mean([data["effectiveness_score"] 
                                                   for data in activity_effectiveness.values()])
                low_performing_activities = [activity for activity, data in activity_effectiveness.items() 
                                           if data["effectiveness_score"] < avg_effectiveness * 0.7]
                
                if low_performing_activities:
                    problems.append(f"Low effectiveness activities: {', '.join(low_performing_activities)}")
            
            # Check timing effectiveness
            timing_analysis = analysis.get("timing_analysis", {})
            timing_effectiveness = timing_analysis.get("strategy_times_effectiveness", {})
            if timing_effectiveness.get("relative_performance", 1) < 0.9:
                problems.append("Strategy posting times are underperforming compared to best times")
            
            # Check content performance
            content_analysis = analysis.get("content_analysis", {})
            content_effectiveness = content_analysis.get("strategy_content_effectiveness", {})
            underperforming_content = [content_type for content_type, data in content_effectiveness.items() 
                                     if data["effectiveness"] < 0.8]
            
            if underperforming_content:
                problems.append(f"Underperforming content types: {', '.join(underperforming_content)}")
            
            # Check trends
            trend_analysis = analysis.get("trend_analysis", {})
            declining_metrics = [metric for metric, trend_data in trend_analysis.items() 
                               if trend_data["direction"] == "declining"]
            
            if declining_metrics:
                problems.append(f"Declining metrics: {', '.join(declining_metrics)}")
            
        except Exception as e:
            logger.error(f"Error identifying problem areas: {e}")
            
        return problems
    
    def _generate_optimizations(self, strategy: StrategyTemplate, 
                              analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        optimizations = []
        
        try:
            # Activity distribution optimizations
            activity_optimizations = self._optimize_activity_distribution(strategy, analysis)
            optimizations.extend(activity_optimizations)
            
            # Timing optimizations
            timing_optimizations = self._optimize_posting_times(strategy, analysis)
            optimizations.extend(timing_optimizations)
            
            # Content optimizations
            content_optimizations = self._optimize_content_strategy(strategy, analysis)
            optimizations.extend(content_optimizations)
            
            # Target optimizations
            target_optimizations = self._optimize_targets(strategy, analysis)
            optimizations.extend(target_optimizations)
            
            # Sort by impact score
            optimizations.sort(key=lambda x: x.get("impact_score", 0), reverse=True)
            
            # Limit number of optimizations
            return optimizations[:self.max_adjustments_per_optimization]
            
        except Exception as e:
            logger.error(f"Error generating optimizations: {e}")
            return []
    
    def _optimize_activity_distribution(self, strategy: StrategyTemplate, 
                                      analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize activity distribution based on effectiveness"""
        optimizations = []
        
        try:
            activity_effectiveness = analysis.get("activity_effectiveness", {})
            
            if not activity_effectiveness:
                return optimizations
            
            # Find most and least effective activities
            activities_by_effectiveness = sorted(activity_effectiveness.items(), 
                                               key=lambda x: x[1]["effectiveness_score"], 
                                               reverse=True)
            
            if len(activities_by_effectiveness) >= 2:
                most_effective = activities_by_effectiveness[0]
                least_effective = activities_by_effectiveness[-1]
                
                # Check if there's a significant difference
                effectiveness_ratio = (most_effective[1]["effectiveness_score"] / 
                                     max(least_effective[1]["effectiveness_score"], 0.001))
                
                if effectiveness_ratio > 1.5:  # 50% more effective
                    # Suggest increasing most effective activity and decreasing least effective
                    most_effective_type = ActivityType(most_effective[0])
                    least_effective_type = ActivityType(least_effective[0])
                    
                    current_most = strategy.activity_distribution.get(most_effective_type, 0)
                    current_least = strategy.activity_distribution.get(least_effective_type, 0)
                    
                    # Calculate adjustment (limited by adjustment limits)
                    max_adjustment = self.adjustment_limits["activity_distribution"]
                    adjustment = min(max_adjustment, current_least * 0.3)  # Move 30% of least effective
                    
                    optimizations.append({
                        "type": "activity_distribution",
                        "description": f"Increase {most_effective[0]} activity, decrease {least_effective[0]}",
                        "changes": {
                            most_effective_type: current_most + adjustment,
                            least_effective_type: current_least - adjustment
                        },
                        "impact_score": effectiveness_ratio,
                        "rationale": f"{most_effective[0]} is {effectiveness_ratio:.1f}x more effective than {least_effective[0]}"
                    })
            
        except Exception as e:
            logger.error(f"Error optimizing activity distribution: {e}")
            
        return optimizations
    
    def _optimize_posting_times(self, strategy: StrategyTemplate, 
                              analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize posting times based on performance data"""
        optimizations = []
        
        try:
            timing_analysis = analysis.get("timing_analysis", {})
            
            # Check if strategy times are underperforming
            timing_effectiveness = timing_analysis.get("strategy_times_effectiveness", {})
            relative_performance = timing_effectiveness.get("relative_performance", 1)
            
            if relative_performance < 0.9:  # Strategy times perform 10% worse than average
                best_hours = timing_analysis.get("best_performing_hours", [])
                
                if best_hours:
                    # Suggest shifting to better performing times
                    current_times = strategy.optimal_posting_times.copy()
                    
                    # Replace least effective current times with best performing times
                    hourly_performance = timing_analysis.get("hourly_performance", {})
                    
                    # Find current strategy hours with performance data
                    strategy_hour_performance = []
                    for time_str in current_times:
                        try:
                            hour = int(time_str.split(":")[0])
                            if hour in hourly_performance:
                                strategy_hour_performance.append((hour, hourly_performance[hour], time_str))
                        except:
                            continue
                    
                    if strategy_hour_performance:
                        # Sort by performance (worst first)
                        strategy_hour_performance.sort(key=lambda x: x[1])
                        
                        # Replace worst performing time with best available time
                        worst_hour, worst_performance, worst_time = strategy_hour_performance[0]
                        best_hour = best_hours[0]
                        
                        if best_hour not in [h for h, _, _ in strategy_hour_performance]:
                            new_times = [time for time in current_times if time != worst_time]
                            new_times.append(f"{best_hour:02d}:00")
                            
                            optimizations.append({
                                "type": "posting_times",
                                "description": f"Shift from {worst_time} to {best_hour:02d}:00",
                                "changes": {
                                    "optimal_posting_times": new_times
                                },
                                "impact_score": (hourly_performance[best_hour] / worst_performance) if worst_performance > 0 else 2,
                                "rationale": f"Hour {best_hour} performs {(hourly_performance[best_hour] / worst_performance):.1f}x better than {worst_hour}"
                            })
            
        except Exception as e:
            logger.error(f"Error optimizing posting times: {e}")
            
        return optimizations
    
    def _optimize_content_strategy(self, strategy: StrategyTemplate, 
                                 analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize content strategy based on performance"""
        optimizations = []
        
        try:
            content_analysis = analysis.get("content_analysis", {})
            
            # Optimize content mix
            content_performance = content_analysis.get("content_type_performance", {})
            if content_performance and len(content_performance) > 1:
                # Find best and worst performing content types
                best_content = max(content_performance.keys(), key=lambda k: content_performance[k])
                worst_content = min(content_performance.keys(), key=lambda k: content_performance[k])
                
                performance_ratio = (content_performance[best_content] / 
                                   max(content_performance[worst_content], 0.001))
                
                if performance_ratio > 1.3:  # 30% better performance
                    current_mix = strategy.content_mix.copy()
                    
                    if best_content in current_mix and worst_content in current_mix:
                        # Shift allocation from worst to best
                        shift_amount = min(0.1, current_mix[worst_content] * 0.3)  # Max 10% or 30% of current
                        
                        new_mix = current_mix.copy()
                        new_mix[best_content] = min(0.8, current_mix[best_content] + shift_amount)  # Cap at 80%
                        new_mix[worst_content] = max(0.05, current_mix[worst_content] - shift_amount)  # Min 5%
                        
                        optimizations.append({
                            "type": "content_mix",
                            "description": f"Increase {best_content} content, decrease {worst_content}",
                            "changes": {
                                "content_mix": new_mix
                            },
                            "impact_score": performance_ratio,
                            "rationale": f"{best_content} performs {performance_ratio:.1f}x better than {worst_content}"
                        })
            
            # Optimize hashtag strategy
            hashtag_performance = content_analysis.get("hashtag_performance", {})
            strategy_hashtag_effectiveness = content_analysis.get("strategy_hashtag_effectiveness", {})
            
            if hashtag_performance and strategy_hashtag_effectiveness:
                # Find underperforming strategy hashtags
                underperforming_hashtags = [hashtag for hashtag, data in strategy_hashtag_effectiveness.items() 
                                          if data["effectiveness"] < 0.8]
                
                # Find better performing hashtags not in strategy
                better_hashtags = [hashtag for hashtag, performance in hashtag_performance.items() 
                                 if hashtag not in strategy.hashtag_strategy and 
                                 performance > statistics.mean(hashtag_performance.values())]
                
                if underperforming_hashtags and better_hashtags:
                    # Replace worst performing hashtag with best alternative
                    worst_hashtag = min(strategy_hashtag_effectiveness.keys(), 
                                      key=lambda h: strategy_hashtag_effectiveness[h]["effectiveness"])
                    best_alternative = max(better_hashtags, key=lambda h: hashtag_performance[h])
                    
                    new_hashtags = [h for h in strategy.hashtag_strategy if h != worst_hashtag]
                    new_hashtags.append(best_alternative)
                    
                    optimizations.append({
                        "type": "hashtag_strategy",
                        "description": f"Replace #{worst_hashtag} with #{best_alternative}",
                        "changes": {
                            "hashtag_strategy": new_hashtags
                        },
                        "impact_score": hashtag_performance[best_alternative] / max(
                            strategy_hashtag_effectiveness[worst_hashtag]["performance"], 0.001),
                        "rationale": f"#{best_alternative} performs better than #{worst_hashtag}"
                    })
            
        except Exception as e:
            logger.error(f"Error optimizing content strategy: {e}")
            
        return optimizations
    
    def _optimize_targets(self, strategy: StrategyTemplate, 
                         analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize performance targets based on actual performance"""
        optimizations = []
        
        try:
            target_achievement = analysis.get("target_achievement", {})
            trend_analysis = analysis.get("trend_analysis", {})
            
            for metric_name, achievement_data in target_achievement.items():
                # Find corresponding enum
                metric_enum = None
                for enum_val in PerformanceMetric:
                    if enum_val.value == metric_name:
                        metric_enum = enum_val
                        break
                
                if not metric_enum:
                    continue
                
                current_target = achievement_data["target"]
                actual_avg = achievement_data["actual_average"]
                achievement_rate = achievement_data["achievement_rate"]
                
                # Check if we should adjust target
                should_adjust = False
                new_target = current_target
                adjustment_reason = ""
                
                if achievement_rate > 1.2:  # Consistently exceeding target by 20%
                    # Increase target
                    new_target = actual_avg * 1.1  # Set target 10% above current average
                    should_adjust = True
                    adjustment_reason = f"Consistently exceeding target by {(achievement_rate - 1) * 100:.1f}%"
                    
                elif achievement_rate < 0.7:  # Consistently missing target by 30%
                    # Check if trend is improving
                    trend_data = trend_analysis.get(metric_name, {})
                    if trend_data.get("direction") == "improving":
                        # Keep target but note it's challenging
                        pass
                    else:
                        # Lower target to be more realistic
                        new_target = actual_avg * 1.2  # Set target 20% above current average
                        should_adjust = True
                        adjustment_reason = f"Target too aggressive, missing by {(1 - achievement_rate) * 100:.1f}%"
                
                if should_adjust and abs(new_target - current_target) / current_target > 0.1:  # At least 10% change
                    new_targets = strategy.target_metrics.copy()
                    new_targets[metric_enum] = new_target
                    
                    optimizations.append({
                        "type": "target_metrics",
                        "description": f"Adjust {metric_name} target from {current_target:.3f} to {new_target:.3f}",
                        "changes": {
                            "target_metrics": new_targets
                        },
                        "impact_score": abs(new_target - current_target) / current_target,
                        "rationale": adjustment_reason
                    })
            
        except Exception as e:
            logger.error(f"Error optimizing targets: {e}")
            
        return optimizations
    
    def _apply_optimizations(self, strategy: StrategyTemplate, 
                           optimizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply approved optimizations to the strategy"""
        applied_optimizations = []
        
        try:
            for optimization in optimizations:
                # Check if optimization meets significance threshold
                impact_score = optimization.get("impact_score", 0)
                
                if impact_score >= (1 + self.significance_threshold):  # At least 10% improvement expected
                    # Apply the optimization
                    changes = optimization.get("changes", {})
                    
                    for field, new_value in changes.items():
                        if hasattr(strategy, field):
                            setattr(strategy, field, new_value)
                            
                            # Update timestamp
                            strategy.updated_at = datetime.now()
                            
                            applied_optimizations.append({
                                "type": optimization["type"],
                                "description": optimization["description"],
                                "field": field,
                                "new_value": new_value,
                                "impact_score": impact_score,
                                "rationale": optimization.get("rationale", ""),
                                "applied_at": datetime.now().isoformat()
                            })
            
            # Save updated strategy
            if applied_optimizations:
                success = self.db.save_strategy_template(strategy)
                if not success:
                    logger.error("Failed to save optimized strategy")
                    return []
                
                logger.info(f"Applied {len(applied_optimizations)} optimizations to strategy {strategy.strategy_name}")
            
        except Exception as e:
            logger.error(f"Error applying optimizations: {e}")
            
        return applied_optimizations
    
    def create_optimization_rule(self, rule_name: str, condition: str, action: str, 
                               parameters: Dict[str, Any], priority: int = 1) -> bool:
        """Create a new optimization rule"""
        try:
            from uuid import uuid4
            
            rule = OptimizationRule(
                rule_id=f"rule_{uuid4().hex[:12]}",
                name=rule_name,
                description=f"Auto-generated rule: {rule_name}",
                condition=condition,
                action=action,
                parameters=parameters,
                priority=priority,
                is_active=True
            )
            
            return self.db.save_optimization_rule(rule)
            
        except Exception as e:
            logger.error(f"Error creating optimization rule: {e}")
            return False
    
    def evaluate_strategy_performance(self, strategy_name: str, days: int = 30) -> Dict[str, Any]:
        """Evaluate overall strategy performance over a longer period"""
        try:
            # Get strategy
            strategy = self.db.get_strategy_template(strategy_name)
            if not strategy:
                return {"error": "Strategy not found"}
            
            # Collect extended performance data
            performance_data = self._collect_performance_data(days)
            
            if not performance_data:
                return {"error": "No performance data available"}
            
            # Calculate comprehensive metrics
            evaluation = {
                "strategy_name": strategy_name,
                "evaluation_period": f"{days} days",
                "total_data_points": len(performance_data),
                "overall_performance": {},
                "target_achievement_summary": {},
                "activity_roi_analysis": {},
                "content_effectiveness": {},
                "timing_optimization": {},
                "recommendations": []
            }
            
            # Overall performance metrics
            all_metrics = defaultdict(list)
            for day_data in performance_data:
                for metric, value in day_data["metrics"].items():
                    all_metrics[metric].append(value)
            
            performance_summary = {}
            for metric, values in all_metrics.items():
                performance_summary[metric] = {
                    "average": statistics.mean(values),
                    "best": max(values),
                    "worst": min(values),
                    "trend": "improving" if values[-1] > values[0] else "declining" if values[-1] < values[0] else "stable",
                    "consistency": 1 - (statistics.stdev(values) / max(statistics.mean(values), 0.001))
                }
            
            evaluation["overall_performance"] = performance_summary
            
            # Target achievement over time
            target_achievement_over_time = []
            for day_data in performance_data:
                day_achievement = {}
                for metric_enum, target in strategy.target_metrics.items():
                    metric_name = metric_enum.value
                    actual_value = day_data["metrics"].get(metric_name, 0)
                    achievement_rate = actual_value / target if target > 0 else 0
                    day_achievement[metric_name] = achievement_rate
                
                target_achievement_over_time.append({
                    "date": day_data["date"],
                    "achievements": day_achievement
                })
            
            evaluation["target_achievement_summary"] = target_achievement_over_time
            
            # Generate long-term recommendations
            evaluation["recommendations"] = self._generate_long_term_recommendations(
                strategy, performance_data, evaluation
            )
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating strategy performance: {e}")
            return {"error": str(e)}
    
    def _generate_long_term_recommendations(self, strategy: StrategyTemplate, 
                                          performance_data: List[Dict[str, Any]], 
                                          evaluation: Dict[str, Any]) -> List[str]:
        """Generate long-term strategic recommendations"""
        recommendations = []
        
        try:
            overall_performance = evaluation.get("overall_performance", {})
            
            # Analyze overall trends
            improving_metrics = [metric for metric, data in overall_performance.items() 
                               if data["trend"] == "improving"]
            declining_metrics = [metric for metric, data in overall_performance.items() 
                               if data["trend"] == "declining"]
            
            if declining_metrics:
                recommendations.append(
                    f"Address declining metrics: {', '.join(declining_metrics[:3])}. "
                    "Consider strategy pivot or increased focus on these areas."
                )
            
            if len(improving_metrics) > len(declining_metrics):
                recommendations.append(
                    "Overall positive trend detected. Consider scaling current successful tactics."
                )
            
            # Consistency analysis
            inconsistent_metrics = [metric for metric, data in overall_performance.items() 
                                  if data["consistency"] < 0.7]
            
            if inconsistent_metrics:
                recommendations.append(
                    f"Improve consistency in: {', '.join(inconsistent_metrics[:2])}. "
                    "Consider more systematic approach to these metrics."
                )
            
            # Performance level analysis
            avg_engagement = overall_performance.get("engagement_rate", {}).get("average", 0)
            if avg_engagement > 0.05:
                recommendations.append("Excellent engagement rates. Consider thought leadership content.")
            elif avg_engagement < 0.02:
                recommendations.append("Low engagement rates. Focus on audience research and content relevance.")
            
            # Growth analysis
            avg_growth = overall_performance.get("follower_growth", {}).get("average", 0)
            if avg_growth < 1:
                recommendations.append("Low follower growth. Increase community engagement and networking.")
            
        except Exception as e:
            logger.error(f"Error generating long-term recommendations: {e}")
            
        return recommendations 