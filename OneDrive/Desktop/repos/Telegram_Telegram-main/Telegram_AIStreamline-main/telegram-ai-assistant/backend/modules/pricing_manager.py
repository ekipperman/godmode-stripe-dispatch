import logging
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
from datetime import datetime, timedelta
import json
from decimal import Decimal
from pathlib import Path
from sentry_config import capture_exception

logger = logging.getLogger(__name__)

class PricingManager:
    def __init__(self, config: Dict[str, Any]):
        """Initialize pricing manager"""
        self.config = config
        self.pricing_config = self._load_pricing_config()
        
        # Initialize usage tracking
        self.usage_tracking: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Pricing Manager initialized")

    def _load_pricing_config(self) -> Dict[str, Any]:
        """Load pricing configuration"""
        try:
            template_path = Path(__file__).parent / "templates" / "pricing_model.json"
            with open(template_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading pricing config: {str(e)}")
            capture_exception(e)
            return {}

    async def calculate_subscription_price(self, plan_id: str, billing_cycle: str = "monthly") -> Dict[str, Any]:
        """Calculate subscription price with any applicable discounts"""
        try:
            plan = self.pricing_config["subscription_plans"].get(plan_id)
            if not plan:
                raise ValueError(f"Invalid plan ID: {plan_id}")
            
            if plan["price"] == "custom":
                return {
                    "success": True,
                    "price": "Contact sales",
                    "billing_cycle": billing_cycle
                }
            
            base_price = plan["price"][billing_cycle]
            
            # Apply annual discount if applicable
            if billing_cycle == "yearly":
                annual_discount = self.pricing_config["promotional_offers"]["annual_discount"]
                discount_amount = base_price * (annual_discount["percentage"] / 100)
                final_price = base_price - discount_amount
            else:
                final_price = base_price
            
            return {
                "success": True,
                "original_price": base_price,
                "final_price": final_price,
                "billing_cycle": billing_cycle,
                "features": plan["features"],
                "limits": plan["limits"]
            }

        except Exception as e:
            logger.error(f"Error calculating subscription price: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def calculate_usage_cost(self, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cost based on usage"""
        try:
            total_cost = Decimal('0')
            cost_breakdown = {}
            
            # Calculate AI token usage cost
            if "ai_tokens" in usage_data:
                for model, tokens in usage_data["ai_tokens"].items():
                    pricing = self.pricing_config["usage_based_pricing"]["ai_tokens"][model]
                    tokens_in_thousands = tokens / 1000
                    
                    # Apply bulk discounts if applicable
                    price_per_1k = pricing["price_per_1k"]
                    for threshold, discounted_price in pricing["bulk_discounts"].items():
                        threshold_value = int(threshold.replace("M+", "000000").replace("k+", "000"))
                        if tokens >= threshold_value:
                            price_per_1k = discounted_price
                    
                    cost = Decimal(str(tokens_in_thousands)) * Decimal(str(price_per_1k))
                    total_cost += cost
                    cost_breakdown["ai_tokens"] = {
                        "usage": tokens,
                        "rate": price_per_1k,
                        "cost": float(cost)
                    }
            
            # Calculate storage usage cost
            if "storage" in usage_data:
                storage_gb = usage_data["storage"]
                pricing = self.pricing_config["usage_based_pricing"]["storage"]
                
                # Apply bulk discounts if applicable
                price_per_gb = pricing["price_per_gb"]
                for threshold, discounted_price in pricing["bulk_discounts"].items():
                    threshold_value = int(threshold.replace("TB+", "000").replace("GB+", ""))
                    if storage_gb >= threshold_value:
                        price_per_gb = discounted_price
                
                cost = Decimal(str(storage_gb)) * Decimal(str(price_per_gb))
                total_cost += cost
                cost_breakdown["storage"] = {
                    "usage": storage_gb,
                    "rate": price_per_gb,
                    "cost": float(cost)
                }
            
            # Calculate API calls cost
            if "api_calls" in usage_data:
                calls = usage_data["api_calls"]
                pricing = self.pricing_config["usage_based_pricing"]["api_calls"]
                calls_in_thousands = calls / 1000
                
                # Apply bulk discounts if applicable
                price_per_1k = pricing["price_per_1k"]
                for threshold, discounted_price in pricing["bulk_discounts"].items():
                    threshold_value = int(threshold.replace("M+", "000000").replace("k+", "000"))
                    if calls >= threshold_value:
                        price_per_1k = discounted_price
                
                cost = Decimal(str(calls_in_thousands)) * Decimal(str(price_per_1k))
                total_cost += cost
                cost_breakdown["api_calls"] = {
                    "usage": calls,
                    "rate": price_per_1k,
                    "cost": float(cost)
                }
            
            return {
                "success": True,
                "total_cost": float(total_cost),
                "breakdown": cost_breakdown
            }

        except Exception as e:
            logger.error(f"Error calculating usage cost: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def calculate_payment_fees(self, amount: Decimal, payment_method: str, provider: str) -> Dict[str, Any]:
        """Calculate payment processing fees"""
        try:
            if payment_method == "credit_card":
                fees = self.pricing_config["payment_processing_fees"]["credit_card"][provider]
                percentage_fee = amount * (Decimal(str(fees["percentage"])) / 100)
                fixed_fee = Decimal(str(fees["fixed"]))
                total_fee = percentage_fee + fixed_fee
            
            elif payment_method == "crypto":
                fees = self.pricing_config["payment_processing_fees"]["crypto"][provider]
                percentage_fee = amount * (Decimal(str(fees["percentage"])) / 100)
                fixed_fee = Decimal(str(fees["fixed"]))
                total_fee = percentage_fee + fixed_fee
            
            else:
                raise ValueError(f"Invalid payment method: {payment_method}")
            
            return {
                "success": True,
                "fee_amount": float(total_fee),
                "final_amount": float(amount + total_fee),
                "breakdown": {
                    "base_amount": float(amount),
                    "percentage_fee": float(percentage_fee),
                    "fixed_fee": float(fixed_fee)
                }
            }

        except Exception as e:
            logger.error(f"Error calculating payment fees: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def apply_promotional_offer(self, user_id: str, offer_type: str, plan_id: str = None) -> Dict[str, Any]:
        """Apply promotional offer to user's subscription"""
        try:
            if offer_type == "new_user_discount":
                offer = self.pricing_config["promotional_offers"]["new_user_discount"]
                if plan_id not in offer["applicable_plans"]:
                    raise ValueError(f"Plan {plan_id} not eligible for new user discount")
                
                return {
                    "success": True,
                    "discount_percentage": offer["percentage"],
                    "duration_months": offer["duration_months"]
                }
            
            elif offer_type == "referral":
                offer = self.pricing_config["promotional_offers"]["referral_program"]
                return {
                    "success": True,
                    "referrer_reward": offer["referrer_reward"],
                    "referee_discount": offer["referee_discount"]
                }
            
            else:
                raise ValueError(f"Invalid offer type: {offer_type}")

        except Exception as e:
            logger.error(f"Error applying promotional offer: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def track_usage(self, user_id: str, usage_type: str, amount: int) -> Dict[str, Any]:
        """Track user's resource usage"""
        try:
            if user_id not in self.usage_tracking:
                self.usage_tracking[user_id] = {
                    "ai_tokens": 0,
                    "storage": 0,
                    "api_calls": 0,
                    "last_updated": datetime.now().isoformat()
                }
            
            self.usage_tracking[user_id][usage_type] += amount
            self.usage_tracking[user_id]["last_updated"] = datetime.now().isoformat()
            
            return {
                "success": True,
                "current_usage": self.usage_tracking[user_id]
            }

        except Exception as e:
            logger.error(f"Error tracking usage: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def get_usage_report(self, user_id: str, start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get usage report for specified period"""
        try:
            if user_id not in self.usage_tracking:
                return {
                    "success": True,
                    "usage": {
                        "ai_tokens": 0,
                        "storage": 0,
                        "api_calls": 0
                    },
                    "period": {
                        "start": start_date.isoformat() if start_date else None,
                        "end": end_date.isoformat() if end_date else None
                    }
                }
            
            usage = self.usage_tracking[user_id]
            
            # Calculate costs
            costs = await self.calculate_usage_cost({
                "ai_tokens": {"gpt-3.5-turbo": usage["ai_tokens"]},
                "storage": usage["storage"],
                "api_calls": usage["api_calls"]
            })
            
            return {
                "success": True,
                "usage": {
                    "ai_tokens": usage["ai_tokens"],
                    "storage": usage["storage"],
                    "api_calls": usage["api_calls"]
                },
                "costs": costs["breakdown"] if costs["success"] else None,
                "period": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }

        except Exception as e:
            logger.error(f"Error getting usage report: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def check_usage_limits(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        """Check if user has exceeded their plan limits"""
        try:
            plan = self.pricing_config["subscription_plans"].get(plan_id)
            if not plan:
                raise ValueError(f"Invalid plan ID: {plan_id}")
            
            if user_id not in self.usage_tracking:
                return {
                    "success": True,
                    "within_limits": True
                }
            
            usage = self.usage_tracking[user_id]
            limits = plan["limits"]
            
            # Check each limit
            exceeded_limits = {}
            
            if limits["monthly_messages"] != "unlimited":
                if usage.get("messages", 0) > limits["monthly_messages"]:
                    exceeded_limits["messages"] = {
                        "limit": limits["monthly_messages"],
                        "current": usage["messages"]
                    }
            
            if limits["storage_gb"] != "unlimited" and limits["storage_gb"] != "custom":
                if usage["storage"] > limits["storage_gb"]:
                    exceeded_limits["storage"] = {
                        "limit": limits["storage_gb"],
                        "current": usage["storage"]
                    }
            
            return {
                "success": True,
                "within_limits": len(exceeded_limits) == 0,
                "exceeded_limits": exceeded_limits if exceeded_limits else None
            }

        except Exception as e:
            logger.error(f"Error checking usage limits: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }
