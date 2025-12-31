#!/usr/bin/env python3
"""
Dashboard Server for Intelligent Twitter Agent
==============================================
Web-based real-time monitoring and analytics dashboard.
"""

import logging
import json
import asyncio
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from typing import Dict, List, Any, Optional

from database_manager import DatabaseManager
from schedule_manager import ScheduleManager
from performance_tracker import PerformanceTracker
from strategy_optimizer import StrategyOptimizer
from agent_integration import AgentIntegration
from data_models import ActivityType, SlotStatus, SystemIdentity, CompanyConfig, PersonalityConfig, convert_to_dict
from intelligent_agent import IntelligentTwitterAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global components
db_manager = None
schedule_manager = None
performance_tracker = None
strategy_optimizer = None
agent_integration = None

# Real-time data cache
live_data_cache = {
    "current_activity": None,
    "next_activity": None,
    "daily_progress": 0,
    "live_metrics": {},
    "recent_activities": [],
    "system_status": "running"
}

def initialize_dashboard():
    """Initialize dashboard components"""
    global db_manager, schedule_manager, performance_tracker, strategy_optimizer, agent_integration
    
    try:
        # Initialize components
        db_manager = DatabaseManager()
        schedule_manager = ScheduleManager(db_manager)
        performance_tracker = PerformanceTracker(db_manager)
        strategy_optimizer = StrategyOptimizer(db_manager, performance_tracker)
        
        logger.info("Dashboard components initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing dashboard: {e}")
        print(f"DEBUG ERROR INITIALIZING: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_system_status():
    """Get current system status"""
    try:
        current_time = datetime.now()
        today = current_time.strftime("%Y-%m-%d")
        
        # Get current activity
        current_activity = schedule_manager.get_current_activity()
        next_activity = schedule_manager.get_next_activity()
        
        # Get today's schedule summary
        schedule_summary = schedule_manager.get_schedule_summary(today)
        
        # Get recent performance
        performance_summary = performance_tracker.get_performance_summary(days=1)
        
        # Database stats
        db_stats = db_manager.get_database_stats()
        
        status_data = {
            "timestamp": current_time.isoformat(),
            "system_status": "running",
            "current_activity": {
                "activity": current_activity.activity_type.value if current_activity else None,
                "start_time": current_activity.start_time.isoformat() if current_activity else None,
                "end_time": current_activity.end_time.isoformat() if current_activity else None,
                "progress": _calculate_activity_progress(current_activity) if current_activity else 0
            },
            "next_activity": {
                "activity": next_activity.activity_type.value if next_activity else None,
                "start_time": next_activity.start_time.isoformat() if next_activity else None,
                "time_until": _calculate_time_until(next_activity) if next_activity else None
            },
            "daily_progress": schedule_summary.get("completion_rate", 0),
            "total_activities": schedule_summary.get("total_slots", 0),
            "completed_activities": sum(1 for status, count in schedule_summary.get("status_distribution", {}).items() 
                                      if status == "completed" for _ in range(count)),
            "performance_metrics": performance_summary,
            "database_stats": db_stats
        }
        
        # Update cache
        live_data_cache.update(status_data)
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedule')
def get_schedule():
    """Get current schedule data"""
    try:
        date = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
        schedule_summary = schedule_manager.get_schedule_summary(date)
        
        # Get detailed slots
        slots = db_manager.get_schedule_slots(date)
        
        schedule_data = {
            "date": date,
            "summary": schedule_summary,
            "slots": [
                {
                    "slot_id": slot.slot_id,
                    "start_time": slot.start_time.isoformat(),
                    "end_time": slot.end_time.isoformat(),
                    "activity_type": slot.activity_type.value,
                    "status": slot.status.value,
                    "priority": slot.priority,
                    "is_flexible": slot.is_flexible,
                    "performance_data": slot.performance_data
                }
                for slot in slots
            ]
        }
        
        return jsonify(schedule_data)
        
    except Exception as e:
        logger.error(f"Error getting schedule: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/performance')
def get_performance():
    """Get performance analytics"""
    try:
        days = int(request.args.get('days', 7))
        time_range = request.args.get('time_range', '7D')
        
        # Get performance summary
        performance_summary = performance_tracker.get_performance_summary(days=days)
        
        # Get trend analysis
        trend_analysis = performance_tracker.generate_trend_analysis(days=days)
        
        # Get recent tweet performances
        today = datetime.now().strftime("%Y-%m-%d")
        recent_tweets = db_manager.get_tweet_performances_by_date(today)
        
        performance_data = {
            "summary": performance_summary,
            "trends": {
                "period_days": trend_analysis.period_days,
                "start_date": trend_analysis.start_date,
                "end_date": trend_analysis.end_date,
                "trends": trend_analysis.trends,
                "trend_score": trend_analysis.trend_score,
                "predictions": trend_analysis.predictions
            },
            "account_overview": performance_tracker.get_account_overview(time_range=time_range),
            "account_trends": performance_tracker.get_account_trends(time_range=time_range),
            "recent_tweets": [
                {
                    "tweet_id": tweet.tweet_id,
                    "content_type": tweet.content_type,
                    "posting_time": tweet.posting_time.isoformat() if tweet.posting_time else None,
                    "engagement": {
                        "likes": tweet.engagement_data.likes if hasattr(tweet.engagement_data, 'likes') else 0,
                        "retweets": tweet.engagement_data.retweets if hasattr(tweet.engagement_data, 'retweets') else 0,
                        "replies": tweet.engagement_data.replies if hasattr(tweet.engagement_data, 'replies') else 0,
                        "impressions": tweet.engagement_data.impressions if hasattr(tweet.engagement_data, 'impressions') else 0
                    },
                    "sentiment_score": tweet.sentiment_score,
                    "virality_score": tweet.virality_score
                }
                for tweet in recent_tweets[-10:]  # Last 10 tweets
            ]
        }
        
        return jsonify(performance_data)
    except Exception as e:
        logger.error(f"Error getting performance data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/ingest', methods=['POST'])
def ingest_account_analytics():
    """Ingest account-level analytics (from X/i/analytics scrape or manual input)"""
    try:
        payload = request.get_json(force=True) or {}
        date = payload.get('date', datetime.now().strftime("%Y-%m-%d"))
        time_range = payload.get('time_range', '7D')
        # Remaining keys treated as metrics
        metrics = {k: v for k, v in payload.items() if k not in ['date', 'time_range']}
        ok = performance_tracker.ingest_account_analytics(date, time_range, metrics)
        if ok:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to save account analytics"}), 500
    except Exception as e:
        logger.error(f"Error ingesting account analytics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
        

@app.route('/api/optimization')
def get_optimization():
    """Get strategy optimization data"""
    try:
        # Get current strategy
        strategy = schedule_manager._get_active_strategy()
        
        if not strategy:
            return jsonify({"error": "No active strategy found"}), 404
        
        # Run optimization analysis
        optimization_report = strategy_optimizer.optimize_strategy(strategy.strategy_name, days_of_data=7)
        
        # Get strategy performance evaluation
        strategy_performance = strategy_optimizer.evaluate_strategy_performance(strategy.strategy_name, days=7)
        
        optimization_data = {
            "current_strategy": {
                "name": strategy.strategy_name,
                "description": strategy.description,
                "activity_distribution": {k.value: v for k, v in strategy.activity_distribution.items()},
                "optimal_posting_times": strategy.optimal_posting_times,
                "target_metrics": {k.value: v for k, v in strategy.target_metrics.items()},
                "hashtag_strategy": strategy.hashtag_strategy
            },
            "optimization_report": optimization_report,
            "strategy_performance": strategy_performance
        }
        
        return jsonify(optimization_data)
        
    except Exception as e:
        logger.error(f"Error getting optimization data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs')
def get_recent_logs():
    """Get recent activity logs"""
    try:
        limit = int(request.args.get('limit', 50))
        
        # Get recent engagement sessions
        recent_sessions = db_manager.get_recent_engagement_sessions(hours=24)
        
        # Get recent performance analyses
        recent_analyses = []
        for i in range(7):  # Last 7 days
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            analysis = db_manager.get_performance_analysis(date)
            if analysis:
                recent_analyses.append(analysis)
        
        logs_data = {
            "recent_sessions": [
                {
                    "session_id": session.session_id,
                    "start_time": session.start_time.isoformat(),
                    "end_time": session.end_time.isoformat() if session.end_time else None,
                    "activity_type": session.activity_type.value,
                    "accounts_engaged": len(session.accounts_engaged),
                    "interactions_made": session.interactions_made,
                    "engagement_quality_score": session.engagement_quality_score,
                    "session_notes": session.session_notes
                }
                for session in recent_sessions[:limit]
            ],
            "recent_analyses": [
                {
                    "date": analysis.date,
                    "performance_score": analysis.performance_score,
                    "insights": analysis.insights,
                    "recommendations": analysis.recommendations,
                    "metrics": analysis.metrics
                }
                for analysis in recent_analyses[:10]
            ]
        }
        
        return jsonify(logs_data)
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/control/start', methods=['POST'])
def start_agent():
    """Start the agent"""
    try:
        global agent_integration

        # Instantiate the intelligent agent singleton and wire into AgentIntegration
        if not agent_integration or not getattr(agent_integration, "intelligent_agent", None):
            agent = IntelligentTwitterAgent()
            agent_integration = AgentIntegration(intelligent_agent=agent)

        if agent_integration.start():
            return jsonify({"status": "success", "message": "Agent started successfully"})
        else:
            return jsonify({"status": "error", "message": "Failed to start agent"}), 500

    except Exception as e:
        logger.error(f"Error starting agent: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/control/stop', methods=['POST'])
def stop_agent():
    """Stop the agent"""
    try:
        global agent_integration
        
        if agent_integration:
            agent_integration.stop()
            return jsonify({"status": "success", "message": "Agent stopped successfully"})
        else:
            return jsonify({"status": "success", "message": "Agent was not running"})
            
    except Exception as e:
        logger.error(f"Error stopping agent: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/control/optimize', methods=['POST'])
def trigger_optimization():
    """Trigger manual optimization"""
    try:
        if not agent_integration:
            return jsonify({"status": "error", "message": "Agent not initialized"}), 400
        
        optimization_report = agent_integration.trigger_optimization()
        return jsonify({"status": "success", "optimization_report": optimization_report})
        
    except Exception as e:
        logger.error(f"Error triggering optimization: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Implement task, settings, and notifications endpoints expected by dashboard.js

@app.route('/api/tasks/update-frequencies', methods=['POST'])
def update_frequencies():
    """Persist distribution to active strategy and recreate today's schedule"""
    try:
        payload = request.get_json(force=True) or {}
        dist = payload.get("distribution", {})
        if not isinstance(dist, dict) or len(dist) == 0:
            return jsonify({"success": False, "error": "Invalid distribution payload"}), 400

        # Map UI keys to ActivityType
        key_map = {
            "tweet": ActivityType.TWEET,
            "scroll_engage": ActivityType.SCROLL_ENGAGE,
            "search_engage": ActivityType.SEARCH_ENGAGE,
            "reply": ActivityType.REPLY,
            "content_creation": ActivityType.CONTENT_CREATION,
            "thread": ActivityType.THREAD,
            "radar_discovery": ActivityType.RADAR_DISCOVERY,
        }

        # Normalize to 1.0 total
        total = sum(int(dist.get(k, 0)) for k in key_map.keys())
        total = total if total > 0 else 100
        normalized = {
            key_map[k]: max(0.0, float(dist.get(k, 0)) / float(total))
            for k in key_map.keys()
        }

        # Update active strategy
        strategy = schedule_manager._get_active_strategy()
        if not strategy:
            return jsonify({"success": False, "error": "No active strategy found"}), 404
        strategy.activity_distribution = normalized
        strategy.updated_at = datetime.now()
        # Persist template (assumes db_manager supports saving StrategyTemplate)
        try:
            db_manager.save_strategy_template(strategy)
        except Exception as e:
            logger.warning(f"save_strategy_template failed: {e}")

        # Force recreate today's schedule
        today = datetime.now().strftime("%Y-%m-%d")
        schedule = schedule_manager.get_or_create_daily_schedule(today, strategy=strategy, force_recreate=True)
        slots = db_manager.get_schedule_slots(today)

        # Emit real-time update
        socketio.emit('schedule_update', {
            "date": today,
            "summary": schedule_manager.get_schedule_summary(today),
            "slots": [
                {
                    "slot_id": s.slot_id,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat(),
                    "activity_type": s.activity_type.value,
                    "status": s.status.value,
                    "priority": s.priority,
                    "is_flexible": s.is_flexible,
                    "performance_data": s.performance_data
                } for s in slots
            ]
        })

        return jsonify({"success": True, "updated_tasks": len(slots)})
    except Exception as e:
        logger.error(f"Error updating frequencies: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tasks/configuration', methods=['GET'])
def get_task_configuration():
    """Return available tasks and current schedule context for modal"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        slots = db_manager.get_schedule_slots(today)
        tasks = [
            {"id": "tweet", "name": "Tweet", "enabled": True},
            {"id": "image_tweet", "name": "Image Tweet", "enabled": True},
            {"id": "video_tweet", "name": "Video Tweet", "enabled": True},
            {"id": "thread", "name": "Thread", "enabled": True},
            {"id": "scroll_engage", "name": "Scroll & Engage", "enabled": True},
            {"id": "search_engage", "name": "Search & Engage", "enabled": True},
            {"id": "reply", "name": "Reply", "enabled": True},
            {"id": "content_creation", "name": "Content Creation", "enabled": True},
            {"id": "radar_discovery", "name": "Radar Discovery", "enabled": True},
        ]
        schedule_data = {
            "date": today,
            "summary": schedule_manager.get_schedule_summary(today),
            "slots": [
                {
                    "slot_id": s.slot_id,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat(),
                    "activity_type": s.activity_type.value,
                    "status": s.status.value,
                    "priority": s.priority
                } for s in slots
            ]
        }
        return jsonify({"success": True, "tasks": tasks, "schedule": schedule_data})
    except Exception as e:
        logger.error(f"Error getting task configuration: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tasks/save-config', methods=['POST'])
def save_task_config():
    """Persist any modal configuration (stub)"""
    try:
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tasks/regenerate', methods=['POST'])
def regenerate_schedule():
    """Regenerate today's schedule using current strategy"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        schedule_manager.get_or_create_daily_schedule(today, force_recreate=True)
        return jsonify({"success": True, "message": "Schedule regenerated"})
    except Exception as e:
        logger.error(f"Error regenerating schedule: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tasks/create-fresh', methods=['POST'])
def create_fresh_schedule():
    """Create a fresh schedule for today (force recreate)"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        schedule_manager.get_or_create_daily_schedule(today, force_recreate=True)
        return jsonify({"success": True, "message": "Fresh schedule created"})
    except Exception as e:
        logger.error(f"Error creating fresh schedule: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tasks/swap-options', methods=['POST'])
def swap_options():
    """Return alternative activity options for a given slot"""
    try:
        payload = request.get_json(force=True) or {}
        slot_id = payload.get("taskId")
        if not slot_id:
            return jsonify({"success": False, "error": "Missing taskId"}), 400

        today = datetime.now().strftime("%Y-%m-%d")
        slots = db_manager.get_schedule_slots(today)
        target = next((s for s in slots if s.slot_id == slot_id), None)
        if not target:
            return jsonify({"success": False, "error": "Slot not found"}), 404

        all_options = [
            ActivityType.TWEET, ActivityType.IMAGE_TWEET, ActivityType.VIDEO_TWEET,
            ActivityType.THREAD, ActivityType.SCROLL_ENGAGE, ActivityType.SEARCH_ENGAGE,
            ActivityType.REPLY, ActivityType.CONTENT_CREATION, ActivityType.RADAR_DISCOVERY
        ]
        options = [{"id": a.value, "name": a.value.replace("_", " ").title()}
                   for a in all_options if a != target.activity_type]

        return jsonify({"success": True, "options": options})
    except Exception as e:
        logger.error(f"Error getting swap options: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tasks/swap', methods=['POST'])
def swap_task():
    """Swap a slot's activity_type to a new one and persist"""
    try:
        payload = request.get_json(force=True) or {}
        slot_id = payload.get("oldTaskId")
        new_type_value = payload.get("newTaskId")
        if not slot_id or not new_type_value:
            return jsonify({"success": False, "error": "Missing oldTaskId or newTaskId"}), 400

        new_type = ActivityType(new_type_value)
        today = datetime.now().strftime("%Y-%m-%d")
        slots = db_manager.get_schedule_slots(today)
        target = next((s for s in slots if s.slot_id == slot_id), None)
        if not target:
            return jsonify({"success": False, "error": "Slot not found"}), 404

        # Update slot and save
        target.activity_type = new_type
        target.activity_config = schedule_manager._get_activity_config(new_type, schedule_manager._get_active_strategy())
        target.updated_at = datetime.now()
        if not db_manager.save_schedule_slot(target):
            return jsonify({"success": False, "error": "Failed to save slot"}), 500

        # Emit real-time update for schedule
        socketio.emit('schedule_update', {
            "date": today,
            "summary": schedule_manager.get_schedule_summary(today),
            "slots": [
                {
                    "slot_id": s.slot_id,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat(),
                    "activity_type": s.activity_type.value,
                    "status": s.status.value,
                    "priority": s.priority
                } for s in db_manager.get_schedule_slots(today)
            ]
        })

        return jsonify({"success": True, "message": "Task swapped successfully"})
    except Exception as e:
        logger.error(f"Error swapping task: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tasks/update-status', methods=['POST'])
def update_task_status():
    """Update a slot status via badge click"""
    try:
        payload = request.get_json(force=True) or {}
        slot_id = payload.get("slot_id")
        status_str = payload.get("status")
        if not slot_id or not status_str:
            return jsonify({"success": False, "error": "Missing slot_id or status"}), 400

        status_map = {
            "scheduled": SlotStatus.SCHEDULED,
            "in_progress": SlotStatus.IN_PROGRESS,
            "completed": SlotStatus.COMPLETED,
            "failed": SlotStatus.FAILED,
            "skipped": SlotStatus.SKIPPED
        }
        status = status_map.get(status_str)
        if not status:
            return jsonify({"success": False, "error": "Invalid status"}), 400

        success = False
        if status == SlotStatus.IN_PROGRESS:
            success = schedule_manager.mark_activity_started(slot_id)
        elif status == SlotStatus.COMPLETED:
            success = schedule_manager.mark_activity_completed(slot_id)
        elif status == SlotStatus.FAILED:
            success = schedule_manager.mark_activity_failed(slot_id, "Marked failed via dashboard")
        elif status == SlotStatus.SCHEDULED or status == SlotStatus.SKIPPED:
            try:
                success = db_manager.update_slot_status(slot_id, status.value, {"updated_at": datetime.now().isoformat()})
            except Exception as e:
                logger.warning(f"update_slot_status failed: {e}")
                success = False

        if not success:
            return jsonify({"success": False, "error": "Failed to update status"}), 500

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error updating task status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/settings/update', methods=['POST'])
def update_settings():
    """Persist settings flags and broadcast to UI"""
    try:
        try:
            dashboard_settings
        except NameError:
            # Initialize defaults on first use
            globals()["dashboard_settings"] = {
                "enable_follower_shoutouts": False,
                "enable_auto_replies": False,
                "max_shoutouts_per_session": 3,
                "max_auto_replies_per_session": 5
            }

        payload = request.get_json(force=True) or {}
        for k, v in payload.items():
            globals()["dashboard_settings"][k] = v

        # Broadcast
        socketio.emit('settings_update', globals()["dashboard_settings"])
        return jsonify({"success": True, **globals()["dashboard_settings"]})
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/notifications/manage', methods=['POST'])
def notifications_manage():
    """Start automatic notifications management using agent"""
    try:
        if not agent_integration or not getattr(agent_integration, "intelligent_agent", None):
            return jsonify({"success": False, "message": "Agent not initialized"}), 400

        payload = request.get_json(force=True) or {}
        enable_shout = bool(payload.get("enable_follower_shoutouts", True))
        enable_auto = bool(payload.get("enable_auto_replies", True))
        max_shout = int(payload.get("max_shoutouts_per_session", 3))
        max_auto = int(payload.get("max_auto_replies_per_session", 10))

        # Run async method
        result = asyncio.run(agent_integration.intelligent_agent._manage_notifications_automatically(
            enable_shout, enable_auto, max_shout, max_auto
        ))
        return jsonify({"success": True, "message": result})
    except Exception as e:
        logger.error(f"Error managing notifications: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/notifications/auto-reply', methods=['POST'])
def notifications_auto_reply():
    """Trigger auto reply with current settings"""
    try:
        if not agent_integration or not getattr(agent_integration, "intelligent_agent", None):
            return jsonify({"success": False, "message": "Agent not initialized"}), 400
        payload = request.get_json(force=True) or {}
        max_replies = int(payload.get("max_replies", 5))
        reply_style = payload.get("reply_style", "helpful")

        result = asyncio.run(agent_integration.intelligent_agent._auto_reply_to_notifications(
            max_replies=max_replies, reply_style=reply_style, filter_keywords=[]
        ))
        return jsonify({"success": True, "message": result})
    except Exception as e:
        logger.error(f"Error in auto-reply: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/notifications/shoutout', methods=['POST'])
def notifications_shoutout():
    """Create a follower shoutout via agent"""
    try:
        if not agent_integration or not getattr(agent_integration, "intelligent_agent", None):
            return jsonify({"success": False, "message": "Agent not initialized"}), 400
        payload = request.get_json(force=True) or {}
        username = (payload.get("username") or "").strip().replace("@", "")
        include_bio = bool(payload.get("include_bio_analysis", True))
        art_style = payload.get("artwork_style", "geometric")
        if not username:
            return jsonify({"success": False, "message": "username required"}), 400

        result = asyncio.run(agent_integration.intelligent_agent._create_follower_shoutout(
            username=username, include_bio_analysis=include_bio, artwork_style=art_style
        ))
        return jsonify({"success": True, "message": result})
    except Exception as e:
        logger.error(f"Error creating shoutout: {e}")

@app.route('/api/debug_ping', methods=['GET'])
def debug_ping():
    return jsonify({"message": "pong", "timestamp": str(datetime.now())})


@app.route('/api/config/identity', methods=['GET'])
def get_system_identity_config():
    """Get system identity configuration"""
    try:
        logger.info("GET /api/system/identity called")
        user_id = request.args.get('user_id', 'default_tenant')
        
        # Check if db_manager is initialized
        if db_manager is None:
            logger.warning("DB Manager is None - Dashboard not initialized?")
            # Fall through to migration/empty
        else:
            # Try to get from database first
            try:
                identity = db_manager.get_system_identity(user_id)
                if identity:
                    return jsonify({
                        "source": "database",
                        "identity": convert_to_dict(identity)
                    })
            except Exception as e:
                logger.error(f"Database fetch failed: {e}")
            
        # Fallback: Migration from config.json
        try:
            if not os.path.exists('config.json'):
                return jsonify({
                    "source": "empty",
                    "identity": convert_to_dict(SystemIdentity(user_id=user_id))
                })

            with open('config.json', 'r') as f:
                config_data = json.load(f)
                
            comp_data = config_data.get("company_config", {})
            pers_data = config_data.get("personality_config", {})
            logo_path = config_data.get("company_logo_path", "")
            
            # Construct objects with defensive defaults
            company = CompanyConfig(
                name=comp_data.get("name", ""),
                industry=comp_data.get("industry", ""),
                mission=comp_data.get("mission", ""),
                brand_colors=comp_data.get("brand_colors", {}) or {},
                twitter_username=comp_data.get("twitter_username", ""),
                company_logo_path=comp_data.get("company_logo_path", ""),
                values=comp_data.get("values", []) or [],
                focus_areas=comp_data.get("focus_areas", []) or [],
                brand_voice=comp_data.get("brand_voice", ""),
                target_audience=comp_data.get("target_audience", ""),
                key_products=comp_data.get("key_products", []) or [],
                competitive_advantages=comp_data.get("competitive_advantages", []) or [],
                location=comp_data.get("location", ""),
                contact_info=comp_data.get("contact_info", {}) or {},
                business_model=comp_data.get("business_model", ""),
                core_philosophy=comp_data.get("core_philosophy", ""),
                subsidiaries=comp_data.get("subsidiaries", []) or [],
                partner_categories=comp_data.get("partner_categories", []) or []
            )
            
            personality = PersonalityConfig(
                tone=pers_data.get("tone", ""),
                engagement_style=pers_data.get("engagement_style", ""),
                communication_style=pers_data.get("communication_style", ""),
                hashtag_strategy=pers_data.get("hashtag_strategy", ""),
                content_themes=pers_data.get("content_themes", []) or [],
                posting_frequency=pers_data.get("posting_frequency", "")
            )
            
            identity = SystemIdentity(
                user_id=user_id,
                company_logo_path=logo_path,
                company_config=company,
                personality_config=personality
            )
            
            # Save initialized identity ONLY if db_manager exists
            if db_manager:
                try:
                    db_manager.save_system_identity(identity)
                except Exception as e:
                    logger.error(f"Failed to auto-save migrated identity: {e}")
            
            return jsonify({
                "source": "migration",
                "identity": convert_to_dict(identity)
            })
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return jsonify({
                "source": "empty",
                "identity": convert_to_dict(SystemIdentity(user_id=user_id))
            })
            
    except Exception as e:
        logger.error(f"Error in get_system_identity_config: {e}")
        # Provide a valid JSON error response instead of crashing
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@app.route('/api/config/identity', methods=['POST'])
def save_system_identity_config():
    """Save system identity configuration"""
    try:
        payload = request.get_json(force=True) or {}
        user_id = payload.get('user_id', 'default_tenant')
        data = payload.get('identity', {})
        
        comp_data = data.get("company_config", {})
        pers_data = data.get("personality_config", {})
        
        company = CompanyConfig(
            name=comp_data.get("name", ""),
            industry=comp_data.get("industry", ""),
            mission=comp_data.get("mission", ""),
            brand_colors=comp_data.get("brand_colors", {}) or {},
            twitter_username=comp_data.get("twitter_username", ""),
            company_logo_path=comp_data.get("company_logo_path", ""),
            values=comp_data.get("values", []) or [],
            focus_areas=comp_data.get("focus_areas", []) or [],
            brand_voice=comp_data.get("brand_voice", ""),
            target_audience=comp_data.get("target_audience", ""),
            key_products=comp_data.get("key_products", []) or [],
            competitive_advantages=comp_data.get("competitive_advantages", []) or [],
            location=comp_data.get("location", ""),
            contact_info=comp_data.get("contact_info", {}) or {},
            business_model=comp_data.get("business_model", ""),
            core_philosophy=comp_data.get("core_philosophy", ""),
            subsidiaries=comp_data.get("subsidiaries", []) or [],
            partner_categories=comp_data.get("partner_categories", []) or []
        )
        
        personality = PersonalityConfig(
            tone=pers_data.get("tone", ""),
            engagement_style=pers_data.get("engagement_style", ""),
            communication_style=pers_data.get("communication_style", ""),
            hashtag_strategy=pers_data.get("hashtag_strategy", ""),
            content_themes=pers_data.get("content_themes", []) or [],
            posting_frequency=pers_data.get("posting_frequency", "")
        )
        
        identity = SystemIdentity(
            user_id=user_id,
            company_logo_path=data.get("company_logo_path", ""),
            company_config=company,
            personality_config=personality
        )
        
        if db_manager.save_system_identity(identity):
            return jsonify({"success": True, "message": "Identity saved successfully"})
        else:
            return jsonify({"success": False, "error": "Database save failed"}), 500
            
    except Exception as e:
        logger.error(f"Error saving identity: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Client connected to dashboard")
    emit('status', live_data_cache)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected from dashboard")

@socketio.on('request_update')
def handle_update_request():
    """Handle manual update request"""
    try:
        # Get fresh status data
        with app.test_request_context():
            status_response = get_system_status()
            if status_response.status_code == 200:
                emit('status_update', json.loads(status_response.data))
    except Exception as e:
        logger.error(f"Error handling update request: {e}")

# Helper functions
def _calculate_activity_progress(activity):
    """Calculate progress of current activity"""
    if not activity:
        return 0
    
    now = datetime.now()
    total_duration = (activity.end_time - activity.start_time).total_seconds()
    elapsed_duration = (now - activity.start_time).total_seconds()
    
    if elapsed_duration < 0:
        return 0
    if elapsed_duration > total_duration:
        return 100
    
    return int((elapsed_duration / total_duration) * 100)

def _calculate_time_until(activity):
    """Calculate time until next activity"""
    if not activity:
        return None
    
    now = datetime.now()
    time_diff = activity.start_time - now
    
    if time_diff.total_seconds() < 0:
        return "0 minutes"
    
    total_minutes = int(time_diff.total_seconds() / 60)
    
    if total_minutes < 60:
        return f"{total_minutes} minutes"
    else:
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes}m"

def broadcast_updates():
    """Background thread to broadcast real-time updates"""
    while True:
        try:
            time.sleep(30)  # Update every 30 seconds
            
            with app.test_request_context():
                status_response = get_system_status()
                if status_response.status_code == 200:
                    status_data = json.loads(status_response.data)
                    socketio.emit('status_update', status_data)
                    
        except Exception as e:
            logger.error(f"Error in broadcast updates: {e}")
            time.sleep(60)  # Wait longer on error

def start_dashboard_server(host='127.0.0.1', port=5000, debug=False):
    """Start the dashboard server"""
    try:
        if not initialize_dashboard():
            logger.error("Failed to initialize dashboard components")
            return False
        
        # Start background update thread
        update_thread = threading.Thread(target=broadcast_updates, daemon=True)
        update_thread.start()
        
        logger.info(f"Starting dashboard server on http://{host}:{port}")
        socketio.run(app, host=host, port=port, debug=debug)
        
        return True
        
    except Exception as e:
        logger.error(f"Error starting dashboard server: {e}")
        return False

if __name__ == "__main__":
    start_dashboard_server(debug=True)
