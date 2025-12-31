#!/usr/bin/env python3
"""
Performance Tracker for Intelligent Twitter Agent
================================================
Tracks performance metrics, analyzes engagement data, and provides insights.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import statistics
import json
from collections import defaultdict, Counter

from data_models import (
    TweetPerformance, EngagementData, PerformanceMetric, 
    ActivityType, PerformanceAnalysis, TrendAnalysis,
    EngagementSession, FollowerAnalytics, AccountAnalytics,
    create_performance_analysis_template
)
from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """Track and analyze agent performance metrics"""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager"""
        self.db = db_manager
        self.analysis_cache = {}
        self.trend_cache = {}
        
        # Performance thresholds
        self.engagement_thresholds = {
            "excellent": 0.08,
            "good": 0.04,
            "fair": 0.02,
            "poor": 0.01
        }
        
        # Metrics weights for overall performance score
        self.metric_weights = {
            "engagement_rate": 0.3,
            "follower_growth": 0.2,
            "tweet_impressions": 0.15,
            "reach": 0.15,
            "click_through_rate": 0.1,
            "content_quality": 0.1
        }
        
        logger.info("Performance Tracker initialized")
    
    def track_tweet_performance(self, tweet_id: str, metrics: Dict[str, Any], 
                              content_info: Optional[Dict] = None) -> bool:
        """Track performance metrics for a specific tweet"""
        try:
            # Create engagement data
            engagement_data = EngagementData(
                likes=metrics.get("likes", 0),
                retweets=metrics.get("retweets", 0),
                replies=metrics.get("replies", 0),
                impressions=metrics.get("impressions", 0),
                clicks=metrics.get("clicks", 0),
                profile_visits=metrics.get("profile_visits", 0),
                follows=metrics.get("follows", 0),
                reach=metrics.get("reach", 0)
            )
            
            # Calculate derived metrics
            if engagement_data.impressions > 0:
                total_engagements = engagement_data.likes + engagement_data.retweets + engagement_data.replies
                engagement_data.save_rate = total_engagements / engagement_data.impressions
                
                if engagement_data.clicks > 0:
                    engagement_data.share_rate = engagement_data.clicks / engagement_data.impressions
            
            # Create performance record
            performance = TweetPerformance(
                tweet_id=tweet_id,
                metrics=metrics,
                engagement_data=engagement_data,
                content_type=content_info.get("content_type", "text") if content_info else "text",
                hashtags=content_info.get("hashtags", []) if content_info else [],
                mentions=content_info.get("mentions", []) if content_info else [],
                posting_time=content_info.get("posting_time") if content_info else None,
                sentiment_score=self._calculate_sentiment_score(metrics),
                virality_score=self._calculate_virality_score(engagement_data)
            )
            
            # Save to database
            return self.db.save_tweet_performance(performance)
            
        except Exception as e:
            logger.error(f"Error tracking tweet performance: {e}")
            return False
    
    
    def track_linkedin_post_performance(self, post_id: str, content: str, metrics: Dict[str, Any]) -> bool:
        """Track performance for a LinkedIn post (wrapper)"""
        # Augment metrics structure to match generic expectation
        normalized_metrics = {
            "likes": metrics.get("likes", 0),
            "retweets": metrics.get("shares", 0), # Map share -> retweet
            "replies": metrics.get("comments", 0), # Map comment -> reply
            "impressions": metrics.get("impressions", 0),
            "clicks": metrics.get("clicks", 0),
            "platform": "linkedin"
        }
        return self.track_tweet_performance(post_id, normalized_metrics, content_info={"text": content})

    def _calculate_sentiment_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate sentiment score based on engagement patterns"""
        try:
            likes = metrics.get("likes", 0)
            replies = metrics.get("replies", 0)
            retweets = metrics.get("retweets", 0)
            
            # Simple sentiment calculation
            # More likes and retweets = positive sentiment
            # High reply ratio might indicate controversy
            
            total_engagements = likes + replies + retweets
            if total_engagements == 0:
                return 0.5  # Neutral
            
            positive_weight = (likes + retweets) / total_engagements
            reply_ratio = replies / total_engagements if total_engagements > 0 else 0
            
            # High reply ratio might indicate negative sentiment
            sentiment = positive_weight - (reply_ratio * 0.3)
            
            return max(0.0, min(1.0, sentiment))
            
        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.5
    
    def _calculate_virality_score(self, engagement: EngagementData) -> float:
        """Calculate virality score based on engagement velocity"""
        try:
            if engagement.impressions == 0:
                return 0.0
            
            # Virality factors
            retweet_factor = engagement.retweets / max(engagement.impressions, 1)
            engagement_factor = (engagement.likes + engagement.retweets + engagement.replies) / max(engagement.impressions, 1)
            reach_factor = engagement.reach / max(engagement.impressions, 1) if engagement.reach > 0 else 0
            
            # Weighted virality score
            virality = (retweet_factor * 0.5) + (engagement_factor * 0.3) + (reach_factor * 0.2)
            
            return min(1.0, virality * 10)  # Scale to 0-1 range
            
        except Exception as e:
            logger.error(f"Error calculating virality score: {e}")
            return 0.0
    
    def track_engagement_session(self, session_id: str, activity_type: ActivityType,
                               interactions: Dict[str, int], accounts_engaged: List[str],
                               session_duration: int, topics: List[str] = None) -> bool:
        """Track an engagement session"""
        try:
            # Calculate engagement quality score
            quality_score = self._calculate_engagement_quality(interactions, accounts_engaged, session_duration)
            
            session = EngagementSession(
                session_id=session_id,
                start_time=datetime.now() - timedelta(minutes=session_duration),
                end_time=datetime.now(),
                activity_type=activity_type,
                accounts_engaged=accounts_engaged,
                interactions_made=interactions,
                topics_engaged=topics or [],
                engagement_quality_score=quality_score,
                session_notes=f"Session duration: {session_duration} minutes"
            )
            
            return self.db.save_engagement_session(session)
            
        except Exception as e:
            logger.error(f"Error tracking engagement session: {e}")
            return False
    
    def _calculate_engagement_quality(self, interactions: Dict[str, int], 
                                    accounts_engaged: List[str], duration: int) -> float:
        """Calculate quality score for an engagement session"""
        try:
            if duration == 0:
                return 0.0
            
            total_interactions = sum(interactions.values())
            unique_accounts = len(set(accounts_engaged))
            
            # Quality factors
            interaction_rate = total_interactions / duration  # Interactions per minute
            account_diversity = unique_accounts / max(total_interactions, 1)  # Unique accounts per interaction
            
            # Weighted quality score
            quality = (interaction_rate * 0.6) + (account_diversity * 0.4)
            
            return min(1.0, quality / 2)  # Normalize to 0-1 range
            
        except Exception as e:
            logger.error(f"Error calculating engagement quality: {e}")
            return 0.0
    
    def analyze_daily_performance(self, date: str) -> PerformanceAnalysis:
        """Perform comprehensive daily performance analysis"""
        try:
            analysis = create_performance_analysis_template(date)
            
            # Get tweet performances for the day
            tweet_performances = self.db.get_tweet_performances_by_date(date)
            
            # Get engagement sessions
            engagement_sessions = self.db.get_recent_engagement_sessions(24)
            date_sessions = [s for s in engagement_sessions 
                           if s.start_time.strftime("%Y-%m-%d") == date]
            
            # Calculate core metrics
            analysis.metrics = self._calculate_daily_metrics(tweet_performances, date_sessions)
            
            # Analyze engagement patterns
            analysis.engagement_analysis = self._analyze_engagement_patterns(tweet_performances, date_sessions)
            
            # Identify top performing content
            analysis.top_performing_content = self._identify_top_content(tweet_performances)
            
            # Evaluate activity effectiveness
            analysis.activity_effectiveness = self._evaluate_activity_effectiveness(date_sessions)
            
            # Generate insights
            analysis.insights = self._generate_insights(analysis.metrics, tweet_performances, date_sessions)
            
            # Generate recommendations
            analysis.recommendations = self._generate_recommendations(analysis)
            
            # Calculate overall performance score
            analysis.performance_score = self._calculate_performance_score(analysis.metrics)
            
            # Save analysis
            self.db.save_performance_analysis(analysis)
            
            logger.info(f"Completed daily performance analysis for {date}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing daily performance: {e}")
            return create_performance_analysis_template(date)
    
    def _calculate_daily_metrics(self, tweets: List[TweetPerformance], 
                               sessions: List[EngagementSession]) -> Dict[str, float]:
        """Calculate daily performance metrics"""
        metrics = {}
        
        try:
            if tweets:
                # Tweet metrics
                total_likes = sum(t.engagement_data.likes for t in tweets)
                total_retweets = sum(t.engagement_data.retweets for t in tweets)
                total_replies = sum(t.engagement_data.replies for t in tweets)
                total_impressions = sum(t.engagement_data.impressions for t in tweets)
                total_reach = sum(t.engagement_data.reach for t in tweets)
                
                # Calculate rates
                if total_impressions > 0:
                    metrics["engagement_rate"] = (total_likes + total_retweets + total_replies) / total_impressions
                    metrics["like_rate"] = total_likes / total_impressions
                    metrics["retweet_rate"] = total_retweets / total_impressions
                    metrics["reply_rate"] = total_replies / total_impressions
                
                metrics["total_tweets"] = len(tweets)
                metrics["total_impressions"] = total_impressions
                metrics["total_reach"] = total_reach
                metrics["average_sentiment"] = statistics.mean([t.sentiment_score for t in tweets])
                metrics["average_virality"] = statistics.mean([t.virality_score for t in tweets])
            
            if sessions:
                # Engagement session metrics
                total_interactions = sum(sum(s.interactions_made.values()) for s in sessions)
                total_accounts_engaged = len(set(acc for s in sessions for acc in s.accounts_engaged))
                avg_quality = statistics.mean([s.engagement_quality_score for s in sessions])
                
                metrics["engagement_sessions"] = len(sessions)
                metrics["total_interactions"] = total_interactions
                metrics["unique_accounts_engaged"] = total_accounts_engaged
                metrics["average_session_quality"] = avg_quality
            
            # Set defaults for missing metrics
            default_metrics = {
                "engagement_rate": 0.0,
                "follower_growth": 0.0,
                "tweet_impressions": 0.0,
                "reach": 0.0,
                "click_through_rate": 0.0
            }
            
            for key, default_value in default_metrics.items():
                if key not in metrics:
                    metrics[key] = default_value
            
        except Exception as e:
            logger.error(f"Error calculating daily metrics: {e}")
            
        return metrics
    
    def _analyze_engagement_patterns(self, tweets: List[TweetPerformance], 
                                   sessions: List[EngagementSession]) -> Dict[str, Any]:
        """Analyze engagement patterns and trends"""
        patterns = {}
        
        try:
            if tweets:
                # Time-based analysis
                hourly_performance = defaultdict(list)
                for tweet in tweets:
                    if tweet.posting_time:
                        hour = tweet.posting_time.hour
                        engagement_rate = (tweet.engagement_data.likes + tweet.engagement_data.retweets + 
                                         tweet.engagement_data.replies) / max(tweet.engagement_data.impressions, 1)
                        hourly_performance[hour].append(engagement_rate)
                
                # Calculate average performance by hour
                hourly_avg = {}
                for hour, rates in hourly_performance.items():
                    hourly_avg[hour] = statistics.mean(rates)
                
                patterns["hourly_performance"] = hourly_avg
                
                # Best performing hour
                if hourly_avg:
                    best_hour = max(hourly_avg.keys(), key=lambda h: hourly_avg[h])
                    patterns["best_posting_hour"] = best_hour
                
                # Content type analysis
                content_performance = defaultdict(list)
                for tweet in tweets:
                    content_type = tweet.content_type
                    engagement_rate = (tweet.engagement_data.likes + tweet.engagement_data.retweets + 
                                     tweet.engagement_data.replies) / max(tweet.engagement_data.impressions, 1)
                    content_performance[content_type].append(engagement_rate)
                
                content_avg = {}
                for content_type, rates in content_performance.items():
                    content_avg[content_type] = statistics.mean(rates)
                
                patterns["content_type_performance"] = content_avg
                
                # Hashtag analysis
                hashtag_performance = defaultdict(list)
                for tweet in tweets:
                    engagement_rate = (tweet.engagement_data.likes + tweet.engagement_data.retweets + 
                                     tweet.engagement_data.replies) / max(tweet.engagement_data.impressions, 1)
                    for hashtag in tweet.hashtags:
                        hashtag_performance[hashtag].append(engagement_rate)
                
                # Calculate average performance by hashtag
                hashtag_avg = {}
                for hashtag, rates in hashtag_performance.items():
                    if len(rates) >= 2:  # Only include hashtags used multiple times
                        hashtag_avg[hashtag] = statistics.mean(rates)
                
                patterns["hashtag_performance"] = hashtag_avg
            
            if sessions:
                # Session patterns
                activity_effectiveness = defaultdict(list)
                for session in sessions:
                    activity_effectiveness[session.activity_type.value].append(session.engagement_quality_score)
                
                activity_avg = {}
                for activity, scores in activity_effectiveness.items():
                    activity_avg[activity] = statistics.mean(scores)
                
                patterns["activity_effectiveness"] = activity_avg
                
        except Exception as e:
            logger.error(f"Error analyzing engagement patterns: {e}")
            
        return patterns
    
    def _identify_top_content(self, tweets: List[TweetPerformance]) -> List[Dict[str, Any]]:
        """Identify top performing content"""
        top_content = []
        
        try:
            if not tweets:
                return top_content
            
            # Sort tweets by engagement rate
            tweet_scores = []
            for tweet in tweets:
                if tweet.engagement_data.impressions > 0:
                    engagement_rate = ((tweet.engagement_data.likes + tweet.engagement_data.retweets + 
                                      tweet.engagement_data.replies) / tweet.engagement_data.impressions)
                    tweet_scores.append((tweet, engagement_rate))
            
            # Sort by engagement rate
            tweet_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Take top 5 or all if less than 5
            top_count = min(5, len(tweet_scores))
            
            for i in range(top_count):
                tweet, score = tweet_scores[i]
                
                content_info = {
                    "tweet_id": tweet.tweet_id,
                    "engagement_rate": round(score, 4),
                    "likes": tweet.engagement_data.likes,
                    "retweets": tweet.engagement_data.retweets,
                    "replies": tweet.engagement_data.replies,
                    "impressions": tweet.engagement_data.impressions,
                    "content_type": tweet.content_type,
                    "hashtags": tweet.hashtags,
                    "sentiment_score": tweet.sentiment_score,
                    "virality_score": tweet.virality_score,
                    "posting_hour": tweet.posting_time.hour if tweet.posting_time else None,
                    "rank": i + 1
                }
                
                top_content.append(content_info)
                
        except Exception as e:
            logger.error(f"Error identifying top content: {e}")
            
        return top_content
    
    def _evaluate_activity_effectiveness(self, sessions: List[EngagementSession]) -> Dict[str, Any]:
        """Evaluate effectiveness of different activities"""
        effectiveness = {}
        
        try:
            if not sessions:
                return effectiveness
            
            # Group sessions by activity type
            activity_groups = defaultdict(list)
            for session in sessions:
                activity_groups[session.activity_type.value].append(session)
            
            # Calculate effectiveness metrics for each activity
            for activity, activity_sessions in activity_groups.items():
                total_interactions = sum(sum(s.interactions_made.values()) for s in activity_sessions)
                total_duration = sum((s.end_time - s.start_time).total_seconds() / 60 
                                   for s in activity_sessions if s.end_time)
                avg_quality = statistics.mean([s.engagement_quality_score for s in activity_sessions])
                
                effectiveness[activity] = {
                    "session_count": len(activity_sessions),
                    "total_interactions": total_interactions,
                    "total_duration_minutes": total_duration,
                    "interactions_per_minute": total_interactions / max(total_duration, 1),
                    "average_quality_score": avg_quality,
                    "effectiveness_score": (total_interactions * avg_quality) / max(total_duration, 1)
                }
                
        except Exception as e:
            logger.error(f"Error evaluating activity effectiveness: {e}")
            
        return effectiveness
    
    def _generate_insights(self, metrics: Dict[str, float], tweets: List[TweetPerformance], 
                          sessions: List[EngagementSession]) -> List[str]:
        """Generate actionable insights from performance data"""
        insights = []
        
        try:
            # Engagement rate insights
            engagement_rate = metrics.get("engagement_rate", 0)
            if engagement_rate > self.engagement_thresholds["excellent"]:
                insights.append("Excellent engagement rate achieved! Current strategy is highly effective.")
            elif engagement_rate > self.engagement_thresholds["good"]:
                insights.append("Good engagement rate. Consider optimizing top-performing content types.")
            elif engagement_rate > self.engagement_thresholds["fair"]:
                insights.append("Fair engagement rate. Focus on improving content quality and timing.")
            else:
                insights.append("Low engagement rate detected. Strategy review and optimization needed.")
            
            # Tweet volume insights
            tweet_count = metrics.get("total_tweets", 0)
            if tweet_count < 2:
                insights.append("Low tweet volume. Consider increasing posting frequency for better visibility.")
            elif tweet_count > 8:
                insights.append("High tweet volume. Monitor for audience fatigue and optimize quality over quantity.")
            
            # Session quality insights
            avg_session_quality = metrics.get("average_session_quality", 0)
            if avg_session_quality > 0.7:
                insights.append("High quality engagement sessions. Current interaction strategy is effective.")
            elif avg_session_quality < 0.3:
                insights.append("Low engagement session quality. Focus on more meaningful interactions.")
            
            # Content-specific insights
            if tweets:
                # Sentiment analysis
                avg_sentiment = metrics.get("average_sentiment", 0.5)
                if avg_sentiment > 0.7:
                    insights.append("Positive sentiment in content resonates well with audience.")
                elif avg_sentiment < 0.3:
                    insights.append("Content sentiment may be too negative. Consider more positive messaging.")
                
                # Virality insights
                avg_virality = metrics.get("average_virality", 0)
                if avg_virality > 0.5:
                    insights.append("High virality content detected. Analyze successful patterns for replication.")
                elif avg_virality < 0.1:
                    insights.append("Low virality scores. Focus on creating more shareable content.")
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            
        return insights
    
    def _generate_recommendations(self, analysis: PerformanceAnalysis) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        try:
            metrics = analysis.metrics
            engagement_analysis = analysis.engagement_analysis
            
            # Engagement rate recommendations
            engagement_rate = metrics.get("engagement_rate", 0)
            if engagement_rate < 0.02:
                recommendations.append("Increase engagement activities and focus on community building")
                recommendations.append("Experiment with different content formats (images, videos, threads)")
                recommendations.append("Post during identified peak engagement hours")
            
            # Timing recommendations
            if "best_posting_hour" in engagement_analysis:
                best_hour = engagement_analysis["best_posting_hour"]
                recommendations.append(f"Schedule more content around {best_hour}:00 for optimal engagement")
            
            # Content type recommendations
            content_performance = engagement_analysis.get("content_type_performance", {})
            if content_performance:
                best_content_type = max(content_performance.keys(), 
                                      key=lambda k: content_performance[k])
                recommendations.append(f"Focus more on {best_content_type} content (highest performing)")
            
            # Hashtag recommendations
            hashtag_performance = engagement_analysis.get("hashtag_performance", {})
            if hashtag_performance:
                top_hashtags = sorted(hashtag_performance.items(), 
                                    key=lambda x: x[1], reverse=True)[:3]
                if top_hashtags:
                    top_tags = [tag for tag, _ in top_hashtags]
                    recommendations.append(f"Use high-performing hashtags: {', '.join(top_tags)}")
            
            # Activity recommendations
            activity_effectiveness = analysis.activity_effectiveness
            if activity_effectiveness:
                most_effective = max(activity_effectiveness.keys(),
                                   key=lambda k: activity_effectiveness[k].get("effectiveness_score", 0))
                recommendations.append(f"Increase {most_effective} activities (most effective)")
            
            # Session quality recommendations
            avg_quality = metrics.get("average_session_quality", 0)
            if avg_quality < 0.5:
                recommendations.append("Improve engagement session quality through more thoughtful interactions")
                recommendations.append("Focus on engaging with accounts in your target niche")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            
        return recommendations
    
    def _calculate_performance_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall performance score"""
        try:
            total_score = 0.0
            total_weight = 0.0
            
            for metric, weight in self.metric_weights.items():
                if metric in metrics:
                    # Normalize metric value (assuming 0-1 range for most metrics)
                    normalized_value = min(1.0, metrics[metric])
                    
                    # Special handling for specific metrics
                    if metric == "follower_growth":
                        # Normalize follower growth (assume 0-50 new followers per day is excellent)
                        normalized_value = min(1.0, metrics[metric] / 50.0)
                    elif metric == "tweet_impressions":
                        # Normalize impressions (assume 0-10000 impressions per day is excellent)
                        normalized_value = min(1.0, metrics[metric] / 10000.0)
                    
                    total_score += normalized_value * weight
                    total_weight += weight
            
            return (total_score / total_weight) if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.0
    
    def generate_trend_analysis(self, days: int = 7, platform: Optional[str] = None) -> TrendAnalysis:
        """Generate trend analysis over multiple days"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            trend_analysis = TrendAnalysis(
                period_days=days,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            # Get metrics for each day
            daily_metrics = []
            for i in range(days):
                current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                analysis = self.db.get_performance_analysis(current_date, platform=platform)
                if analysis:
                    daily_metrics.append((current_date, analysis.metrics))
            
            if daily_metrics:
                # Calculate trends
                trend_analysis.trends = self._calculate_metric_trends(daily_metrics)
                trend_analysis.trend_score = self._calculate_trend_score(daily_metrics)
                trend_analysis.predictions = self._generate_predictions(daily_metrics)
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Error generating trend analysis: {e}")
            return TrendAnalysis(period_days=days, start_date="", end_date="")
    
    def _calculate_metric_trends(self, daily_metrics: List[Tuple[str, Dict]]) -> Dict[str, Any]:
        """Calculate trends for individual metrics, including raw values for charting"""
        trends = {}
        
        try:
            # Group metrics by type
            metric_values = defaultdict(list)
            
            for date, metrics in daily_metrics:
                for metric, value in metrics.items():
                    metric_values[metric].append((date, value))
            
            # Calculate trend for each metric
            for metric, values in metric_values.items():
                if len(values) >= 3:  # Need at least 3 data points
                    trend_data = self._analyze_metric_trend(values)
                    # Attach raw values (date, value) pairs for frontend charts
                    trend_data["values"] = values
                    trends[metric] = trend_data
                    
        except Exception as e:
            logger.error(f"Error calculating metric trends: {e}")
            
        return trends
    
    def _analyze_metric_trend(self, values: List[Tuple[str, float]]) -> Dict[str, Any]:
        """Analyze trend for a single metric"""
        try:
            # Sort by date
            values.sort(key=lambda x: x[0])
            
            # Extract just the values
            metric_values = [v[1] for v in values]
            
            # Calculate trend direction
            first_half = metric_values[:len(metric_values)//2]
            second_half = metric_values[len(metric_values)//2:]
            
            first_avg = statistics.mean(first_half)
            second_avg = statistics.mean(second_half)
            
            if second_avg > first_avg * 1.1:
                direction = "increasing"
            elif second_avg < first_avg * 0.9:
                direction = "decreasing"
            else:
                direction = "stable"
            
            # Calculate trend strength
            if first_avg > 0:
                change_percent = ((second_avg - first_avg) / first_avg) * 100
            else:
                change_percent = 0
            
            return {
                "direction": direction,
                "change_percent": round(change_percent, 2),
                "current_value": metric_values[-1],
                "average_value": statistics.mean(metric_values),
                "volatility": statistics.stdev(metric_values) if len(metric_values) > 1 else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing metric trend: {e}")
            return {"direction": "unknown", "change_percent": 0}
    
    def _calculate_trend_score(self, daily_metrics: List[Tuple[str, Dict]]) -> float:
        """Calculate overall trend score"""
        try:
            if len(daily_metrics) < 2:
                return 0.5
            
            # Get first and last day metrics
            first_day_metrics = daily_metrics[0][1]
            last_day_metrics = daily_metrics[-1][1]
            
            improvements = 0
            total_metrics = 0
            
            for metric in first_day_metrics:
                if metric in last_day_metrics:
                    first_value = first_day_metrics[metric]
                    last_value = last_day_metrics[metric]
                    
                    if first_value > 0 and last_value > first_value:
                        improvements += 1
                    
                    total_metrics += 1
            
            return improvements / total_metrics if total_metrics > 0 else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating trend score: {e}")
            return 0.5
    
    def _generate_predictions(self, daily_metrics: List[Tuple[str, Dict]]) -> Dict[str, Any]:
        """Generate simple predictions based on trends"""
        predictions = {}
        
        try:
            if len(daily_metrics) < 3:
                return predictions
            
            # Simple linear prediction for key metrics
            key_metrics = ["engagement_rate", "follower_growth", "total_impressions"]
            
            for metric in key_metrics:
                values = []
                for date, metrics in daily_metrics:
                    if metric in metrics:
                        values.append(metrics[metric])
                
                if len(values) >= 3:
                    # Simple linear trend prediction
                    recent_trend = (values[-1] - values[-3]) / 2  # Average change over last 2 days
                    predicted_next_day = values[-1] + recent_trend
                    
                    predictions[f"{metric}_next_day"] = max(0, predicted_next_day)
                    
                    # Confidence based on trend consistency
                    if len(values) >= 5:
                        recent_changes = [values[i] - values[i-1] for i in range(1, len(values))]
                        trend_consistency = 1 - (statistics.stdev(recent_changes) / (statistics.mean(values) + 0.001))
                        predictions[f"{metric}_confidence"] = max(0.1, min(0.9, trend_consistency))
                    
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            
        return predictions
    
    def ingest_account_analytics(self, date: str, time_range: str, analytics: Dict[str, Any]) -> bool:
        """Ingest account-level analytics (from X analytics or scraper) and persist"""
        try:
            record = AccountAnalytics(
                date=date,
                time_range=time_range.upper(),
                verified_followers=int(analytics.get("verified_followers", analytics.get("verified", 0) or 0)),
                total_followers=int(analytics.get("total_followers", analytics.get("followers", 0) or 0)),
                impressions=int(analytics.get("impressions", 0)),
                engagements=int(analytics.get("engagements", 0)),
                engagement_rate=float(analytics.get("engagement_rate", 0.0)),
                profile_visits=int(analytics.get("profile_visits", 0)),
                replies=int(analytics.get("replies", 0)),
                likes=int(analytics.get("likes", 0)),
                reposts=int(analytics.get("reposts", analytics.get("retweets", 0) or 0)),
                bookmarks=int(analytics.get("bookmarks", 0)),
                shares=int(analytics.get("shares", 0)),
                follows=int(analytics.get("follows", 0)),
                unfollows=int(analytics.get("unfollows", 0)),
                posts_count=int(analytics.get("posts_count", analytics.get("posts", 0) or 0)),
                replies_count=int(analytics.get("replies_count", 0))
            )
            return self.db.save_account_analytics(record)
        except Exception as e:
            logger.error(f"Error ingesting account analytics: {e}")
            return False

    def _compute_percent_change(self, current: Union[int, float], previous: Union[int, float]) -> float:
        """Compute percent change from previous to current"""
        try:
            if previous == 0:
                return 0.0
            return ((current - previous) / previous) * 100.0
        except Exception:
            return 0.0

    def get_account_overview(self, time_range: str = "7D", platform: Optional[str] = None) -> Dict[str, Any]:
        """Return latest account analytics and percent change vs previous period"""
        overview = {"current": {}, "percent_change": {}}
        try:
            records = self.db.get_recent_account_analytics(time_range=time_range.upper(), limit=2, platform=platform)
            if not records:
                return overview
            current = records[0]
            previous = records[1] if len(records) > 1 else None

            # Current snapshot
            overview["current"] = {
                "date": current.date,
                "time_range": current.time_range,
                "platform": current.platform,
                "verified_followers": current.verified_followers,
                "total_followers": current.total_followers,
                "impressions": current.impressions,
                "engagements": current.engagements,
                "engagement_rate": current.engagement_rate,
                "profile_visits": current.profile_visits,
                "replies": current.replies,
                "likes": current.likes,
                "reposts": current.reposts,
                "bookmarks": current.bookmarks,
                "shares": current.shares,
                "follows": current.follows,
                "unfollows": current.unfollows,
                "posts_count": current.posts_count,
                "replies_count": current.replies_count,
            }

            # Percent changes
            if previous:
                overview["percent_change"] = {
                    "verified_followers": self._compute_percent_change(current.verified_followers, previous.verified_followers),
                    "total_followers": self._compute_percent_change(current.total_followers, previous.total_followers),
                    "impressions": self._compute_percent_change(current.impressions, previous.impressions),
                    "engagements": self._compute_percent_change(current.engagements, previous.engagements),
                    "engagement_rate": self._compute_percent_change(current.engagement_rate, previous.engagement_rate),
                    "profile_visits": self._compute_percent_change(current.profile_visits, previous.profile_visits),
                    "replies": self._compute_percent_change(current.replies, previous.replies),
                    "likes": self._compute_percent_change(current.likes, previous.likes),
                    "reposts": self._compute_percent_change(current.reposts, previous.reposts),
                    "bookmarks": self._compute_percent_change(current.bookmarks, previous.bookmarks),
                    "shares": self._compute_percent_change(current.shares, previous.shares),
                    "follows": self._compute_percent_change(current.follows, previous.follows),
                    "unfollows": self._compute_percent_change(current.unfollows, previous.unfollows),
                }
            return overview
        except Exception as e:
            logger.error(f"Error building account overview: {e}")
            return overview

    def get_account_trends(self, time_range: str = "7D", platform: Optional[str] = None) -> Dict[str, Any]:
        """Build trends for account-level metrics with (date,value) arrays for charts"""
        trends: Dict[str, Any] = {}
        try:
            # Fetch recent records for the given time range; choose reasonable limits
            limit_map = {"7D": 7, "30D": 30, "90D": 90}
            limit = limit_map.get(time_range.upper(), 7)
            records = self.db.get_recent_account_analytics(time_range=time_range.upper(), limit=limit, platform=platform)
            if not records:
                return trends

            # Build value arrays
            def series(metric_name: str, values: List[tuple]) -> Dict[str, Any]:
                # Simple direction estimation
                vals_only = [v for _, v in values if isinstance(v, (int, float))]
                if len(vals_only) >= 2:
                    direction = "increasing" if vals_only[-1] > vals_only[0] else "decreasing" if vals_only[-1] < vals_only[0] else "stable"
                else:
                    direction = "stable"
                return {"metric": metric_name, "values": values, "direction": direction}

            # Prepare pairs sorted by date desc already; reverse to asc
            records_sorted = list(reversed(records))
            trends["impressions"] = series("impressions", [(r.date, r.impressions) for r in records_sorted])
            trends["engagements"] = series("engagements", [(r.date, r.engagements) for r in records_sorted])
            trends["engagement_rate"] = series("engagement_rate", [(r.date, r.engagement_rate) for r in records_sorted])
            trends["profile_visits"] = series("profile_visits", [(r.date, r.profile_visits) for r in records_sorted])
            trends["total_followers"] = series("total_followers", [(r.date, r.total_followers) for r in records_sorted])
            return trends
        except Exception as e:
            logger.error(f"Error building account trends: {e}")
            return trends

    def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get a comprehensive performance summary"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            summary = {
                "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "total_days": days,
                "daily_analyses": [],
                "aggregate_metrics": {},
                "trends": {},
                "overall_performance": "unknown"
            }
            
            # Collect daily analyses
            total_metrics = defaultdict(list)
            
            for i in range(days):
                current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                analysis = self.db.get_performance_analysis(current_date)
                
                if analysis:
                    summary["daily_analyses"].append({
                        "date": current_date,
                        "performance_score": analysis.performance_score,
                        "key_metrics": analysis.metrics
                    })
                    
                    # Collect metrics for aggregation
                    for metric, value in analysis.metrics.items():
                        total_metrics[metric].append(value)
            
            # Calculate aggregate metrics
            for metric, values in total_metrics.items():
                if values:
                    summary["aggregate_metrics"][metric] = {
                        "average": statistics.mean(values),
                        "total": sum(values),
                        "best_day": max(values),
                        "worst_day": min(values),
                        "trend": "improving" if values[-1] > values[0] else "declining" if values[-1] < values[0] else "stable"
                    }
            
            # Overall performance assessment
            if summary["daily_analyses"]:
                avg_score = statistics.mean([d["performance_score"] for d in summary["daily_analyses"]])
                if avg_score > 0.8:
                    summary["overall_performance"] = "excellent"
                elif avg_score > 0.6:
                    summary["overall_performance"] = "good"
                elif avg_score > 0.4:
                    summary["overall_performance"] = "fair"
                else:
                    summary["overall_performance"] = "needs_improvement"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}
