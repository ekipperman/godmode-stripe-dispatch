import logging
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path
from sentry_config import capture_exception
from .marketing_automation import MarketingAutomation
from .content_automation import ContentAutomation
from .analytics_reporting import AnalyticsReporting

logger = logging.getLogger(__name__)

class GrowthStrategy:
    def __init__(self, config: Dict[str, Any]):
        """Initialize growth strategy"""
        self.config = config
        self.marketing = MarketingAutomation(config)
        self.content = ContentAutomation(config)
        self.analytics = AnalyticsReporting(config)
        
        # Initialize tracking
        self.plg_tracking: Dict[str, Dict[str, Any]] = {}
        self.influencer_tracking: Dict[str, Dict[str, Any]] = {}
        self.cro_tracking: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Growth Strategy initialized")

    async def setup_plg_funnel(self, funnel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up Product-Led Growth funnel"""
        try:
            funnel_id = f"plg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Configure free trial
            trial_config = {
                "duration_days": funnel_data.get("trial_duration", 7),
                "features": funnel_data.get("trial_features", []),
                "onboarding_steps": self._generate_onboarding_steps(funnel_data)
            }
            
            # Configure freemium tier
            freemium_config = {
                "features": funnel_data.get("freemium_features", []),
                "limits": funnel_data.get("freemium_limits", {}),
                "upgrade_triggers": self._generate_upgrade_triggers(funnel_data)
            }
            
            # Set up onboarding content
            onboarding_content = await self.content.generate_website_content({
                "business_name": funnel_data["business_name"],
                "value_proposition": funnel_data["value_proposition"],
                "product_type": "SaaS Platform",
                "mission": "Empower businesses with AI automation"
            })
            
            # Track funnel setup
            self.plg_tracking[funnel_id] = {
                "status": "active",
                "trial_config": trial_config,
                "freemium_config": freemium_config,
                "onboarding_content": onboarding_content,
                "metrics": {
                    "trial_signups": 0,
                    "trial_conversions": 0,
                    "freemium_users": 0,
                    "paid_conversions": 0
                },
                "created_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "funnel_id": funnel_id,
                "config": {
                    "trial": trial_config,
                    "freemium": freemium_config
                }
            }

        except Exception as e:
            logger.error(f"Error setting up PLG funnel: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def setup_influencer_program(self, program_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up influencer marketing program"""
        try:
            program_id = f"inf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Generate influencer content
            content_templates = await self.content.generate_social_content({
                "topic": program_data["campaign_topic"],
                "audience": program_data["target_audience"],
                "platforms": program_data["platforms"],
                "tone": "professional"
            })
            
            # Configure commission structure
            commission_config = {
                "base_rate": program_data.get("base_commission", 20),
                "bonus_tiers": program_data.get("bonus_tiers", []),
                "payout_schedule": program_data.get("payout_schedule", "monthly")
            }
            
            # Track program setup
            self.influencer_tracking[program_id] = {
                "status": "active",
                "content_templates": content_templates,
                "commission_config": commission_config,
                "influencers": {},
                "metrics": {
                    "total_reach": 0,
                    "clicks": 0,
                    "conversions": 0,
                    "revenue": 0
                },
                "created_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "program_id": program_id,
                "content_templates": content_templates,
                "commission_config": commission_config
            }

        except Exception as e:
            logger.error(f"Error setting up influencer program: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def setup_cro_experiments(self, experiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up Conversion Rate Optimization experiments"""
        try:
            experiment_id = f"cro_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Generate variants
            variants = await self._generate_experiment_variants(experiment_data)
            
            # Configure tracking
            tracking_config = {
                "metrics": experiment_data["target_metrics"],
                "segment": experiment_data.get("user_segment"),
                "duration_days": experiment_data.get("duration", 14)
            }
            
            # Track experiment setup
            self.cro_tracking[experiment_id] = {
                "status": "active",
                "variants": variants,
                "tracking_config": tracking_config,
                "results": {
                    variant_id: {
                        "impressions": 0,
                        "conversions": 0,
                        "revenue": 0
                    }
                    for variant_id in variants.keys()
                },
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=tracking_config["duration_days"])).isoformat()
            }
            
            return {
                "success": True,
                "experiment_id": experiment_id,
                "variants": variants,
                "tracking_config": tracking_config
            }

        except Exception as e:
            logger.error(f"Error setting up CRO experiments: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def track_plg_metrics(self, funnel_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track Product-Led Growth metrics"""
        try:
            if funnel_id not in self.plg_tracking:
                raise ValueError(f"Invalid funnel ID: {funnel_id}")
            
            funnel = self.plg_tracking[funnel_id]
            event_type = event_data["type"]
            
            if event_type == "trial_signup":
                funnel["metrics"]["trial_signups"] += 1
            elif event_type == "trial_conversion":
                funnel["metrics"]["trial_conversions"] += 1
            elif event_type == "freemium_signup":
                funnel["metrics"]["freemium_users"] += 1
            elif event_type == "paid_conversion":
                funnel["metrics"]["paid_conversions"] += 1
            
            return {
                "success": True,
                "funnel_id": funnel_id,
                "updated_metrics": funnel["metrics"]
            }

        except Exception as e:
            logger.error(f"Error tracking PLG metrics: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def track_influencer_metrics(self, program_id: str,
                                     influencer_id: str,
                                     metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Track influencer marketing metrics"""
        try:
            if program_id not in self.influencer_tracking:
                raise ValueError(f"Invalid program ID: {program_id}")
            
            program = self.influencer_tracking[program_id]
            
            if influencer_id not in program["influencers"]:
                program["influencers"][influencer_id] = {
                    "metrics": {
                        "reach": 0,
                        "clicks": 0,
                        "conversions": 0,
                        "revenue": 0
                    }
                }
            
            # Update influencer metrics
            influencer_metrics = program["influencers"][influencer_id]["metrics"]
            for metric, value in metrics.items():
                if metric in influencer_metrics:
                    influencer_metrics[metric] += value
            
            # Update program totals
            program_metrics = program["metrics"]
            for metric, value in metrics.items():
                if metric in program_metrics:
                    program_metrics[metric] += value
            
            return {
                "success": True,
                "program_id": program_id,
                "influencer_id": influencer_id,
                "metrics": influencer_metrics
            }

        except Exception as e:
            logger.error(f"Error tracking influencer metrics: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def track_cro_metrics(self, experiment_id: str,
                              variant_id: str,
                              event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track CRO experiment metrics"""
        try:
            if experiment_id not in self.cro_tracking:
                raise ValueError(f"Invalid experiment ID: {experiment_id}")
            
            experiment = self.cro_tracking[experiment_id]
            
            if variant_id not in experiment["variants"]:
                raise ValueError(f"Invalid variant ID: {variant_id}")
            
            # Update variant metrics
            results = experiment["results"][variant_id]
            event_type = event_data["type"]
            
            if event_type == "impression":
                results["impressions"] += 1
            elif event_type == "conversion":
                results["conversions"] += 1
                results["revenue"] += event_data.get("revenue", 0)
            
            return {
                "success": True,
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "results": results
            }

        except Exception as e:
            logger.error(f"Error tracking CRO metrics: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_onboarding_steps(self, funnel_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate onboarding steps based on funnel data"""
        steps = [
            {
                "id": "welcome",
                "title": "Welcome",
                "description": "Welcome to our platform",
                "action": "next"
            },
            {
                "id": "setup",
                "title": "Setup Your Account",
                "description": "Configure your basic settings",
                "action": "setup_form"
            },
            {
                "id": "features",
                "title": "Explore Features",
                "description": "Discover key features",
                "action": "feature_tour"
            },
            {
                "id": "integration",
                "title": "Connect Your Tools",
                "description": "Set up integrations",
                "action": "integration_setup"
            }
        ]
        
        return steps

    def _generate_upgrade_triggers(self, funnel_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate upgrade triggers based on funnel data"""
        triggers = [
            {
                "type": "usage_limit",
                "metric": "api_calls",
                "threshold": 0.8,
                "message": "You're approaching your API usage limit"
            },
            {
                "type": "feature_access",
                "feature": "advanced_analytics",
                "message": "Unlock advanced analytics with our Pro plan"
            },
            {
                "type": "time_based",
                "days_active": 14,
                "message": "Upgrade now to maintain access to all features"
            }
        ]
        
        return triggers

    async def _generate_experiment_variants(self, experiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate experiment variants based on experiment data"""
        variants = {}
        
        if experiment_data["type"] == "landing_page":
            variants = {
                "control": {
                    "headline": experiment_data["current_headline"],
                    "cta": experiment_data["current_cta"]
                },
                "variant_a": {
                    "headline": await self._generate_headline_variant(experiment_data),
                    "cta": await self._generate_cta_variant(experiment_data)
                },
                "variant_b": {
                    "headline": await self._generate_headline_variant(experiment_data),
                    "cta": await self._generate_cta_variant(experiment_data)
                }
            }
        elif experiment_data["type"] == "email":
            variants = {
                "control": {
                    "subject": experiment_data["current_subject"],
                    "content": experiment_data["current_content"]
                },
                "variant_a": {
                    "subject": await self._generate_email_subject_variant(experiment_data),
                    "content": await self._generate_email_content_variant(experiment_data)
                },
                "variant_b": {
                    "subject": await self._generate_email_subject_variant(experiment_data),
                    "content": await self._generate_email_content_variant(experiment_data)
                }
            }
        
        return variants

    async def _generate_headline_variant(self, experiment_data: Dict[str, Any]) -> str:
        """Generate headline variant using AI"""
        response = await self.content.ai_chatbot.generate_content(
            f"Generate a compelling headline variant for {experiment_data['target_audience']}"
        )
        return response["headline"]

    async def _generate_cta_variant(self, experiment_data: Dict[str, Any]) -> str:
        """Generate CTA variant using AI"""
        response = await self.content.ai_chatbot.generate_content(
            f"Generate a strong call-to-action for {experiment_data['target_audience']}"
        )
        return response["cta"]

    async def _generate_email_subject_variant(self, experiment_data: Dict[str, Any]) -> str:
        """Generate email subject variant using AI"""
        response = await self.content.ai_chatbot.generate_content(
            f"Generate an email subject line for {experiment_data['campaign_type']}"
        )
        return response["subject"]

    async def _generate_email_content_variant(self, experiment_data: Dict[str, Any]) -> str:
        """Generate email content variant using AI"""
        response = await self.content.ai_chatbot.generate_content(
            f"Generate email content for {experiment_data['campaign_type']}"
        )
        return response["content"]
