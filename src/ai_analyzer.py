"""
AI-powered content analysis using Llama API
"""
import os
from typing import List, Dict, Optional
import json
import logging
from datetime import datetime
try:
    import textstat
except ImportError:
    textstat = None

try:
    from langdetect import detect
except ImportError:
    detect = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .llama_client import LlamaClient
import config

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self):
        self.client = None
        self.model = config.LLAMA_MODEL
        
        # Try custom Llama client first
        try:
            if config.LLAMA_API_KEY and config.LLAMA_API_KEY != "your_llama_api_key_here":
                self.client = LlamaClient(config.LLAMA_API_KEY, config.LLAMA_BASE_URL)
                logger.info("Initialized custom Llama client")
            else:
                logger.warning("No valid Llama API key configured")
        except Exception as e:
            logger.warning(f"Failed to initialize Llama client: {e}")
            
        # Fallback to OpenAI client if available
        if not self.client and OpenAI:
            try:
                self.client = OpenAI(
                    api_key=config.LLAMA_API_KEY,
                    base_url=config.LLAMA_BASE_URL,
                )
                logger.info("Initialized OpenAI client as fallback")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        if not self.client:
            logger.warning("No AI client available - analysis will be basic")
        
    def analyze_group_activity(self, group_name: str, activities: List[Dict], hours: int = 24) -> Dict:
        """Analyze activity in a specific group using AI"""
        if not activities:
            return {
                'group_name': group_name,
                'summary': 'No activity detected in this group.',
                'insights': [],
                'sentiment': 'neutral',
                'stats': {'message_count': 0, 'user_count': 0}
            }
        
        # Prepare activity data for analysis
        activity_text = self._format_activities_for_analysis(activities)
        user_count = len(set([act.get('author', 'unknown') for act in activities]))
        message_count = len(activities)
        
        # Generate AI analysis
        try:
            if not self.client:
                ai_analysis = f"AI analysis unavailable (client not initialized). Found {message_count} messages from {user_count} users in {group_name}."
            else:
                prompt = config.ANALYSIS_PROMPT_TEMPLATE.format(
                    group_name=group_name,
                    hours=hours,
                    message_count=message_count,
                    user_count=user_count,
                    activity_data=activity_text
                )
                
                messages = [
                    {"role": "system", "content": "You are an expert social media analyst specializing in online community dynamics and digital communication patterns."},
                    {"role": "user", "content": prompt}
                ]
                
                # Use custom Llama client or OpenAI client
                if isinstance(self.client, LlamaClient):
                    ai_analysis = self.client.chat_completion(messages, self.model, max_tokens=500, temperature=0.7)
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=500,
                        temperature=0.7
                    )
                    ai_analysis = response.choices[0].message.content
            
            # Add quantitative analysis
            stats = self._calculate_activity_stats(activities)
            
            return {
                'group_name': group_name,
                'ai_analysis': ai_analysis,
                'stats': stats,
                'timestamp': datetime.now().isoformat(),
                'period_hours': hours
            }
            
        except Exception as e:
            logger.error(f"AI analysis failed for {group_name}: {e}")
            return {
                'group_name': group_name,
                'ai_analysis': f"Analysis unavailable due to error: {str(e)}",
                'stats': self._calculate_activity_stats(activities),
                'timestamp': datetime.now().isoformat(),
                'period_hours': hours
            }
    
    def _format_activities_for_analysis(self, activities: List[Dict]) -> str:
        """Format activity data for AI analysis"""
        formatted_activities = []
        
        for activity in activities[-20:]:  # Last 20 messages to avoid token limits
            author = activity.get('author', 'unknown')
            content = activity.get('content', '')
            timestamp = activity.get('timestamp', '')
            activity_type = activity.get('type', 'message')
            
            # Clean and truncate content
            content = content[:200] if content else '[No content]'
            
            formatted_activities.append(
                f"[{timestamp}] {author} ({activity_type}): {content}"
            )
        
        return "\n".join(formatted_activities)
    
    def _calculate_activity_stats(self, activities: List[Dict]) -> Dict:
        """Calculate quantitative statistics about the activity"""
        if not activities:
            return {
                'message_count': 0,
                'user_count': 0,
                'avg_message_length': 0,
                'most_active_user': None,
                'activity_timeline': []
            }
        
        # Basic stats
        message_count = len(activities)
        users = [act.get('author', 'unknown') for act in activities]
        unique_users = list(set(users))
        user_count = len(unique_users)
        
        # Content analysis
        contents = [act.get('content', '') for act in activities if act.get('content')]
        avg_message_length = sum(len(c) for c in contents) / len(contents) if contents else 0
        
        # Most active user
        user_counts = {}
        for user in users:
            user_counts[user] = user_counts.get(user, 0) + 1
        most_active_user = max(user_counts, key=user_counts.get) if user_counts else None
        
        # Activity timeline (simplified)
        timeline = []
        for activity in activities[-10:]:  # Last 10 activities
            timeline.append({
                'time': activity.get('timestamp', ''),
                'author': activity.get('author', 'unknown'),
                'type': activity.get('type', 'message')
            })
        
        # Language detection (if possible)
        detected_languages = []
        if detect:  # Only if langdetect is available
            for content in contents[:5]:  # Check first 5 messages
                try:
                    if content and len(content) > 10:
                        lang = detect(content)
                        detected_languages.append(lang)
                except:
                    pass
        
        primary_language = max(set(detected_languages), key=detected_languages.count) if detected_languages else 'unknown'
        
        return {
            'message_count': message_count,
            'user_count': user_count,
            'avg_message_length': round(avg_message_length, 1),
            'most_active_user': most_active_user,
            'most_active_user_messages': user_counts.get(most_active_user, 0) if most_active_user else 0,
            'activity_timeline': timeline,
            'primary_language': primary_language,
            'unique_users': unique_users
        }
    
    def generate_comprehensive_summary(self, group_analyses: List[Dict]) -> str:
        """Generate a comprehensive summary of all group activities"""
        if not group_analyses:
            return "No group activity to summarize."
        
        # Prepare summary data
        total_messages = sum(analysis['stats']['message_count'] for analysis in group_analyses)
        group_count = len(group_analyses)
        time_period = f"Last {group_analyses[0].get('period_hours', 24)} hours"
        
        # Format individual group summaries
        group_summaries = []
        for analysis in group_analyses:
            group_name = analysis['group_name']
            message_count = analysis['stats']['message_count']
            user_count = analysis['stats']['user_count']
            ai_summary = analysis['ai_analysis'][:200] + "..." if len(analysis['ai_analysis']) > 200 else analysis['ai_analysis']
            
            group_summaries.append(f"**{group_name}**: {message_count} messages, {user_count} users\n{ai_summary}")
        
        group_summaries_text = "\n\n".join(group_summaries)
        
        try:
            if not self.client:
                return f"Summary: {group_count} groups monitored, {total_messages} total messages in {time_period}. AI analysis unavailable (client not initialized).\n\nBasic stats:\n" + group_summaries_text
            
            prompt = config.SUMMARY_PROMPT_TEMPLATE.format(
                group_count=group_count,
                total_messages=total_messages,
                time_period=time_period,
                group_summaries=group_summaries_text
            )
            
            messages = [
                {"role": "system", "content": "You are a professional analyst creating executive summaries of digital community activity."},
                {"role": "user", "content": prompt}
            ]
            
            # Use custom Llama client or OpenAI client
            if isinstance(self.client, LlamaClient):
                return self.client.chat_completion(messages, self.model, max_tokens=600, temperature=0.6)
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=600,
                    temperature=0.6
                )
                return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"Summary generation failed: {str(e)}\n\nBasic stats: {group_count} groups, {total_messages} total messages in {time_period}"
    
    def analyze_trends(self, historical_data: List[Dict]) -> Dict:
        """Analyze trends over time"""
        if len(historical_data) < 2:
            return {"trend": "insufficient_data", "insights": []}
        
        # Calculate trend metrics
        recent_total = sum(d['stats']['message_count'] for d in historical_data[-3:])
        older_total = sum(d['stats']['message_count'] for d in historical_data[-6:-3])
        
        if older_total == 0:
            trend_direction = "new_activity"
        else:
            change_percent = ((recent_total - older_total) / older_total) * 100
            if change_percent > 20:
                trend_direction = "increasing"
            elif change_percent < -20:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
        
        return {
            "trend": trend_direction,
            "change_percent": change_percent if 'change_percent' in locals() else 0,
            "insights": [
                f"Activity trend: {trend_direction}",
                f"Recent period: {recent_total} messages",
                f"Previous period: {older_total} messages"
            ]
        }
    
    def detect_anomalies(self, current_stats: Dict, historical_averages: Dict) -> List[str]:
        """Detect unusual activity patterns"""
        anomalies = []
        
        # Check for unusual message volume
        avg_messages = historical_averages.get('avg_message_count', 0)
        current_messages = current_stats.get('message_count', 0)
        
        if avg_messages > 0:
            if current_messages > avg_messages * 2:
                anomalies.append(f"Unusually high message volume: {current_messages} vs avg {avg_messages}")
            elif current_messages < avg_messages * 0.3:
                anomalies.append(f"Unusually low message volume: {current_messages} vs avg {avg_messages}")
        
        # Check for new users
        avg_users = historical_averages.get('avg_user_count', 0)
        current_users = current_stats.get('user_count', 0)
        
        if avg_users > 0 and current_users > avg_users * 1.5:
            anomalies.append(f"High new user activity: {current_users} vs avg {avg_users}")
        
        return anomalies