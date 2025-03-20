import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

class AnalyticsReporting:
    def __init__(self, config: Dict[str, Any]):
        """Initialize analytics and reporting with configuration"""
        self.config = config
        self.analytics_config = config["plugins"]["analytics"]
        
        # Create reports directory if it doesn't exist
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # Initialize cache for storing aggregated data
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(minutes=15)  # Cache data for 15 minutes
        
        logger.info("Analytics & Reporting initialized successfully")

    async def generate_report(self, 
                            report_type: str,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a comprehensive report"""
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # Get data based on report type
            data = await self._get_report_data(report_type, start_date, end_date, filters)
            
            # Generate visualizations
            visualizations = await self._create_visualizations(report_type, data)
            
            # Generate insights
            insights = await self._generate_insights(report_type, data)
            
            # Compile report
            report = {
                "type": report_type,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "data": data,
                "visualizations": visualizations,
                "insights": insights,
                "generated_at": datetime.now().isoformat()
            }
            
            # Save report
            await self._save_report(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise

    async def _get_report_data(self,
                             report_type: str,
                             start_date: datetime,
                             end_date: datetime,
                             filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get data for the report from various sources"""
        data = {}
        
        # Check cache first
        cache_key = f"{report_type}_{start_date.date()}_{end_date.date()}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]

        try:
            if report_type == "business_overview":
                # Aggregate data from all sources
                data = await self._get_business_overview(start_date, end_date)
            
            elif report_type == "social_media":
                # Get social media metrics
                data = await self._get_social_media_metrics(start_date, end_date)
            
            elif report_type == "crm":
                # Get CRM analytics
                data = await self._get_crm_analytics(start_date, end_date)
            
            elif report_type == "messaging":
                # Get messaging statistics
                data = await self._get_messaging_stats(start_date, end_date)
            
            elif report_type == "automation":
                # Get automation metrics
                data = await self._get_automation_metrics(start_date, end_date)
            
            # Apply filters if provided
            if filters:
                data = self._apply_filters(data, filters)
            
            # Cache the data
            self._cache_data(cache_key, data)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting report data: {str(e)}")
            raise

    async def _create_visualizations(self,
                                   report_type: str,
                                   data: Dict[str, Any]) -> Dict[str, Any]:
        """Create visualizations based on report type and data"""
        visualizations = {}
        
        try:
            if report_type == "business_overview":
                visualizations = await self._create_overview_visualizations(data)
            
            elif report_type == "social_media":
                visualizations = await self._create_social_media_visualizations(data)
            
            elif report_type == "crm":
                visualizations = await self._create_crm_visualizations(data)
            
            elif report_type == "messaging":
                visualizations = await self._create_messaging_visualizations(data)
            
            elif report_type == "automation":
                visualizations = await self._create_automation_visualizations(data)
            
            return visualizations
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {str(e)}")
            raise

    async def _generate_insights(self,
                               report_type: str,
                               data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights from the data"""
        insights = []
        
        try:
            if report_type == "business_overview":
                insights = await self._generate_business_insights(data)
            
            elif report_type == "social_media":
                insights = await self._generate_social_media_insights(data)
            
            elif report_type == "crm":
                insights = await self._generate_crm_insights(data)
            
            elif report_type == "messaging":
                insights = await self._generate_messaging_insights(data)
            
            elif report_type == "automation":
                insights = await self._generate_automation_insights(data)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            raise

    async def _get_business_overview(self,
                                   start_date: datetime,
                                   end_date: datetime) -> Dict[str, Any]:
        """Get comprehensive business overview data"""
        try:
            # Get data from various plugins
            crm_data = await self._get_crm_analytics(start_date, end_date)
            social_data = await self._get_social_media_metrics(start_date, end_date)
            messaging_data = await self._get_messaging_stats(start_date, end_date)
            
            # Aggregate key metrics
            overview = {
                "revenue": {
                    "total": crm_data["revenue"]["total"],
                    "growth": crm_data["revenue"]["growth"],
                    "by_source": crm_data["revenue"]["by_source"]
                },
                "customers": {
                    "total": crm_data["customers"]["total"],
                    "new": crm_data["customers"]["new"],
                    "active": crm_data["customers"]["active"]
                },
                "engagement": {
                    "social_media": {
                        "total_interactions": social_data["total_interactions"],
                        "followers_growth": social_data["followers_growth"]
                    },
                    "messaging": {
                        "email_open_rate": messaging_data["email"]["open_rate"],
                        "sms_response_rate": messaging_data["sms"]["response_rate"]
                    }
                },
                "trends": {
                    "revenue_trend": crm_data["revenue"]["trend"],
                    "engagement_trend": social_data["engagement_trend"]
                }
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting business overview: {str(e)}")
            raise

    async def _create_overview_visualizations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create visualizations for business overview"""
        try:
            visualizations = {}
            
            # Revenue trend chart
            revenue_df = pd.DataFrame(data["revenue"]["trend"])
            fig_revenue = px.line(
                revenue_df,
                x="date",
                y="amount",
                title="Revenue Trend"
            )
            visualizations["revenue_trend"] = fig_revenue.to_json()
            
            # Customer growth chart
            customer_data = {
                "Total": data["customers"]["total"],
                "New": data["customers"]["new"],
                "Active": data["customers"]["active"]
            }
            fig_customers = go.Figure(data=[
                go.Bar(x=list(customer_data.keys()),
                      y=list(customer_data.values()))
            ])
            fig_customers.update_layout(title="Customer Metrics")
            visualizations["customer_metrics"] = fig_customers.to_json()
            
            # Engagement metrics
            engagement_data = {
                "Social Interactions": data["engagement"]["social_media"]["total_interactions"],
                "Email Open Rate": data["engagement"]["messaging"]["email_open_rate"],
                "SMS Response Rate": data["engagement"]["messaging"]["sms_response_rate"]
            }
            fig_engagement = px.pie(
                values=list(engagement_data.values()),
                names=list(engagement_data.keys()),
                title="Engagement Distribution"
            )
            visualizations["engagement_distribution"] = fig_engagement.to_json()
            
            return visualizations
            
        except Exception as e:
            logger.error(f"Error creating overview visualizations: {str(e)}")
            raise

    async def _generate_business_insights(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights for business overview"""
        insights = []
        
        try:
            # Revenue insights
            revenue_growth = data["revenue"]["growth"]
            insights.append({
                "category": "revenue",
                "type": "growth",
                "message": f"Revenue has {'increased' if revenue_growth > 0 else 'decreased'} by {abs(revenue_growth)}% compared to previous period",
                "impact": "high" if abs(revenue_growth) > 10 else "medium"
            })
            
            # Customer insights
            new_customer_ratio = (data["customers"]["new"] / data["customers"]["total"]) * 100
            insights.append({
                "category": "customers",
                "type": "acquisition",
                "message": f"{data['customers']['new']} new customers acquired ({new_customer_ratio:.1f}% growth)",
                "impact": "high" if new_customer_ratio > 5 else "medium"
            })
            
            # Engagement insights
            email_open_rate = data["engagement"]["messaging"]["email_open_rate"]
            insights.append({
                "category": "engagement",
                "type": "email",
                "message": f"Email open rate is at {email_open_rate}%",
                "impact": "high" if email_open_rate > 25 else "medium"
            })
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating business insights: {str(e)}")
            raise

    async def _save_report(self, report: Dict[str, Any]) -> None:
        """Save report to file system"""
        try:
            report_path = self.reports_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Report saved to {report_path}")
            
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            raise

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key in self.cache_expiry:
            return datetime.now() < self.cache_expiry[cache_key]
        return False

    def _cache_data(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Cache data with expiration"""
        self.cache[cache_key] = data
        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration

    def _apply_filters(self,
                      data: Dict[str, Any],
                      filters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply filters to the data"""
        filtered_data = data.copy()
        
        for key, value in filters.items():
            if key in filtered_data:
                if isinstance(filtered_data[key], dict):
                    filtered_data[key] = {k: v for k, v in filtered_data[key].items()
                                        if self._matches_filter(v, value)}
                elif isinstance(filtered_data[key], list):
                    filtered_data[key] = [item for item in filtered_data[key]
                                        if self._matches_filter(item, value)]
        
        return filtered_data

    def _matches_filter(self, item: Any, filter_value: Any) -> bool:
        """Check if item matches filter criteria"""
        if isinstance(filter_value, dict):
            for k, v in filter_value.items():
                if k == "gt" and not (isinstance(item, (int, float)) and item > v):
                    return False
                elif k == "lt" and not (isinstance(item, (int, float)) and item < v):
                    return False
                elif k == "contains" and not (isinstance(item, str) and v in item):
                    return False
        else:
            return item == filter_value
        
        return True
