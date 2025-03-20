import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json
import asyncio
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

class AnalyticsReporting:
    def __init__(self, config: Dict[str, Any]):
        """Initialize analytics and reporting with configuration"""
        self.config = config
        self.analytics_config = config["plugins"]["analytics"]
        
        # Initialize data storage
        self.metrics_history: List[Dict[str, Any]] = []
        self.reports_cache: Dict[str, Dict[str, Any]] = {}
        
        # Load historical data
        self._load_data()
        
        # Start background task for metrics collection
        self.collecting = True
        asyncio.create_task(self._collect_metrics())
        
        logger.info("Analytics & Reporting initialized successfully")

    def _load_data(self) -> None:
        """Load historical analytics data"""
        try:
            data_dir = Path(__file__).parent / "data"
            data_dir.mkdir(exist_ok=True)
            
            metrics_path = data_dir / "metrics_history.json"
            if metrics_path.exists():
                with open(metrics_path, 'r') as f:
                    self.metrics_history = json.load(f)
                    
        except Exception as e:
            logger.error(f"Error loading analytics data: {str(e)}")

    async def _save_data(self) -> None:
        """Save analytics data"""
        try:
            data_dir = Path(__file__).parent / "data"
            data_dir.mkdir(exist_ok=True)
            
            metrics_path = data_dir / "metrics_history.json"
            with open(metrics_path, 'w') as f:
                json.dump(self.metrics_history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving analytics data: {str(e)}")

    async def _collect_metrics(self) -> None:
        """Collect metrics periodically"""
        while self.collecting:
            try:
                # Collect current metrics
                metrics = await self._gather_current_metrics()
                
                # Add timestamp
                metrics["timestamp"] = datetime.now().isoformat()
                
                # Store metrics
                self.metrics_history.append(metrics)
                
                # Save data
                await self._save_data()
                
                # Clean up old data (keep last 90 days)
                cutoff_date = datetime.now() - timedelta(days=90)
                self.metrics_history = [
                    m for m in self.metrics_history
                    if datetime.fromisoformat(m["timestamp"]) > cutoff_date
                ]
                
                # Wait for next collection cycle
                await asyncio.sleep(3600)  # Collect hourly
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    async def _gather_current_metrics(self) -> Dict[str, Any]:
        """Gather current metrics from all modules"""
        metrics = {
            "ai_chatbot": await self._get_chatbot_metrics(),
            "voice_command": await self._get_voice_metrics(),
            "crm": await self._get_crm_metrics(),
            "social_media": await self._get_social_metrics(),
            "messaging": await self._get_messaging_metrics(),
            "lead_nurturing": await self._get_nurturing_metrics()
        }
        
        return metrics

    async def _get_chatbot_metrics(self) -> Dict[str, Any]:
        """Get metrics from AI chatbot module"""
        try:
            chatbot = self.config["modules"].get("ai_chatbot")
            if chatbot:
                return {
                    "total_conversations": len(chatbot.conversations),
                    "active_users": len(set(chatbot.conversations.keys())),
                    "avg_response_time": chatbot.get_average_response_time()
                }
        except Exception as e:
            logger.error(f"Error getting chatbot metrics: {str(e)}")
        return {}

    async def _get_voice_metrics(self) -> Dict[str, Any]:
        """Get metrics from voice command module"""
        try:
            voice = self.config["modules"].get("voice_command")
            if voice:
                return {
                    "total_commands": voice.total_commands,
                    "successful_commands": voice.successful_commands,
                    "failed_commands": voice.failed_commands
                }
        except Exception as e:
            logger.error(f"Error getting voice metrics: {str(e)}")
        return {}

    async def _get_crm_metrics(self) -> Dict[str, Any]:
        """Get metrics from CRM module"""
        try:
            crm = self.config["modules"].get("crm")
            if crm:
                return {
                    "total_contacts": len(crm.contact_cache),
                    "last_sync": crm.last_sync,
                    "platform_stats": {
                        "hubspot": crm.hubspot_stats if hasattr(crm, 'hubspot_stats') else {},
                        "shopify": crm.shopify_stats if hasattr(crm, 'shopify_stats') else {},
                        "stripe": crm.stripe_stats if hasattr(crm, 'stripe_stats') else {}
                    }
                }
        except Exception as e:
            logger.error(f"Error getting CRM metrics: {str(e)}")
        return {}

    async def _get_social_metrics(self) -> Dict[str, Any]:
        """Get metrics from social media module"""
        try:
            social = self.config["modules"].get("social_media")
            if social:
                return {
                    "total_posts": len(social.post_history),
                    "platform_stats": await social.get_analytics()
                }
        except Exception as e:
            logger.error(f"Error getting social media metrics: {str(e)}")
        return {}

    async def _get_messaging_metrics(self) -> Dict[str, Any]:
        """Get metrics from messaging module"""
        try:
            messaging = self.config["modules"].get("messaging")
            if messaging:
                return await messaging.get_analytics()
        except Exception as e:
            logger.error(f"Error getting messaging metrics: {str(e)}")
        return {}

    async def _get_nurturing_metrics(self) -> Dict[str, Any]:
        """Get metrics from lead nurturing module"""
        try:
            nurturing = self.config["modules"].get("lead_nurturing")
            if nurturing:
                return {
                    "total_leads": len(nurturing.leads),
                    "active_campaigns": len([c for c in nurturing.campaigns.values() if c["status"] == "active"]),
                    "completed_campaigns": len([c for c in nurturing.campaigns.values() if c["status"] == "completed"])
                }
        except Exception as e:
            logger.error(f"Error getting nurturing metrics: {str(e)}")
        return {}

    async def generate_report(self, report_type: str = "overview",
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate analytics report"""
        try:
            # Parse dates
            if start_date:
                start = datetime.fromisoformat(start_date)
            else:
                start = datetime.now() - timedelta(days=30)
                
            if end_date:
                end = datetime.fromisoformat(end_date)
            else:
                end = datetime.now()
            
            # Filter metrics by date range
            metrics = [
                m for m in self.metrics_history
                if start <= datetime.fromisoformat(m["timestamp"]) <= end
            ]
            
            # Generate report based on type
            if report_type == "overview":
                report_data = await self._generate_overview_report(metrics)
            elif report_type == "engagement":
                report_data = await self._generate_engagement_report(metrics)
            elif report_type == "conversion":
                report_data = await self._generate_conversion_report(metrics)
            else:
                raise ValueError(f"Invalid report type: {report_type}")
            
            # Apply filters if provided
            if filters:
                report_data = self._apply_filters(report_data, filters)
            
            # Generate visualizations
            visualizations = await self._generate_visualizations(report_data, report_type)
            
            # Cache report
            cache_key = f"{report_type}_{start.date()}_{end.date()}"
            self.reports_cache[cache_key] = {
                "data": report_data,
                "generated_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "report_type": report_type,
                "date_range": {
                    "start": start.isoformat(),
                    "end": end.isoformat()
                },
                "data": report_data,
                "visualizations": visualizations
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _generate_overview_report(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate overview report"""
        try:
            df = pd.DataFrame(metrics)
            
            # Calculate key metrics
            report = {
                "user_engagement": {
                    "total_conversations": df["ai_chatbot"].apply(lambda x: x.get("total_conversations", 0)).max(),
                    "active_users": df["ai_chatbot"].apply(lambda x: x.get("active_users", 0)).mean(),
                    "voice_commands": df["voice_command"].apply(lambda x: x.get("total_commands", 0)).sum()
                },
                "crm_stats": {
                    "total_contacts": df["crm"].apply(lambda x: x.get("total_contacts", 0)).max(),
                    "platform_distribution": self._calculate_platform_distribution(df)
                },
                "social_media": {
                    "total_posts": df["social_media"].apply(lambda x: x.get("total_posts", 0)).max(),
                    "engagement_by_platform": self._calculate_social_engagement(df)
                },
                "messaging": {
                    "email_stats": self._calculate_email_stats(df),
                    "sms_stats": self._calculate_sms_stats(df)
                },
                "lead_nurturing": {
                    "total_leads": df["lead_nurturing"].apply(lambda x: x.get("total_leads", 0)).max(),
                    "active_campaigns": df["lead_nurturing"].apply(lambda x: x.get("active_campaigns", 0)).mean(),
                    "completion_rate": self._calculate_campaign_completion_rate(df)
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating overview report: {str(e)}")
            raise

    async def _generate_engagement_report(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate engagement report"""
        try:
            df = pd.DataFrame(metrics)
            
            report = {
                "user_activity": {
                    "daily_active_users": self._calculate_daily_active_users(df),
                    "peak_usage_hours": self._calculate_peak_hours(df),
                    "retention_rate": self._calculate_retention_rate(df)
                },
                "interaction_quality": {
                    "avg_response_time": df["ai_chatbot"].apply(lambda x: x.get("avg_response_time", 0)).mean(),
                    "command_success_rate": self._calculate_command_success_rate(df),
                    "user_satisfaction": self._calculate_satisfaction_score(df)
                },
                "platform_engagement": {
                    "social_media": self._calculate_social_engagement_trends(df),
                    "messaging": self._calculate_messaging_engagement(df),
                    "crm": self._calculate_crm_engagement(df)
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating engagement report: {str(e)}")
            raise

    async def _generate_conversion_report(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate conversion report"""
        try:
            df = pd.DataFrame(metrics)
            
            report = {
                "lead_conversion": {
                    "conversion_rate": self._calculate_conversion_rate(df),
                    "conversion_by_source": self._calculate_conversion_by_source(df),
                    "time_to_convert": self._calculate_time_to_convert(df)
                },
                "campaign_performance": {
                    "campaign_success_rate": self._calculate_campaign_success_rate(df),
                    "engagement_by_campaign": self._calculate_campaign_engagement(df),
                    "roi_by_campaign": self._calculate_campaign_roi(df)
                },
                "revenue_impact": {
                    "revenue_by_channel": self._calculate_revenue_by_channel(df),
                    "customer_lifetime_value": self._calculate_customer_ltv(df),
                    "revenue_trends": self._calculate_revenue_trends(df)
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating conversion report: {str(e)}")
            raise

    def _apply_filters(self, report_data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply filters to report data"""
        filtered_data = report_data.copy()
        
        for key, value in filters.items():
            if isinstance(value, dict):
                if "min" in value:
                    filtered_data = self._filter_min_value(filtered_data, key, value["min"])
                if "max" in value:
                    filtered_data = self._filter_max_value(filtered_data, key, value["max"])
            else:
                filtered_data = self._filter_exact_value(filtered_data, key, value)
        
        return filtered_data

    async def _generate_visualizations(self, report_data: Dict[str, Any], report_type: str) -> Dict[str, str]:
        """Generate visualizations for report data"""
        try:
            visualizations = {}
            
            if report_type == "overview":
                visualizations["user_engagement"] = await self._create_engagement_chart(report_data)
                visualizations["platform_distribution"] = await self._create_platform_chart(report_data)
                visualizations["messaging_stats"] = await self._create_messaging_chart(report_data)
                
            elif report_type == "engagement":
                visualizations["daily_activity"] = await self._create_activity_chart(report_data)
                visualizations["platform_engagement"] = await self._create_engagement_trends_chart(report_data)
                
            elif report_type == "conversion":
                visualizations["conversion_funnel"] = await self._create_conversion_funnel(report_data)
                visualizations["revenue_trends"] = await self._create_revenue_chart(report_data)
            
            return visualizations
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {str(e)}")
            return {}

    async def _create_chart(self, data: Dict[str, Any], chart_type: str) -> str:
        """Create a chart and return as base64 string"""
        try:
            plt.figure(figsize=(10, 6))
            
            if chart_type == "bar":
                plt.bar(data.keys(), data.values())
            elif chart_type == "line":
                plt.plot(list(data.keys()), list(data.values()))
            elif chart_type == "pie":
                plt.pie(data.values(), labels=data.keys(), autopct='%1.1f%%')
            
            plt.title(chart_type.capitalize() + " Chart")
            
            # Save to buffer
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            
            # Convert to base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Error creating chart: {str(e)}")
            return ""

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.collecting = False
