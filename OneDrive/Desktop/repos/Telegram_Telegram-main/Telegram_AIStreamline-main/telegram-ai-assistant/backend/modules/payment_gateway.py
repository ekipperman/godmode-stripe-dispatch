import logging
from typing import Dict, Any, Optional
import stripe
import paypalrestsdk
from datetime import datetime
import json
from sentry_config import capture_exception

logger = logging.getLogger(__name__)

class PaymentGateway:
    def __init__(self, config: Dict[str, Any]):
        """Initialize payment gateway with configuration"""
        self.config = config
        self.payment_config = config["plugins"]["payment_gateway"]
        
        # Initialize Stripe
        if self.payment_config["stripe"]["enabled"]:
            stripe.api_key = self.payment_config["stripe"]["secret_key"]
            self.stripe_client = stripe
            
        # Initialize PayPal
        if self.payment_config["paypal"]["enabled"]:
            paypalrestsdk.configure({
                "mode": self.payment_config["paypal"]["mode"],  # sandbox or live
                "client_id": self.payment_config["paypal"]["client_id"],
                "client_secret": self.payment_config["paypal"]["client_secret"]
            })
            self.paypal_client = paypalrestsdk
            
        # Initialize payment history
        self.payment_history: List[Dict[str, Any]] = []
        
        logger.info("Payment Gateway initialized successfully")

    async def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment through the specified gateway"""
        try:
            gateway = payment_data.get("gateway", "stripe").lower()
            
            if gateway == "stripe":
                return await self._process_stripe_payment(payment_data)
            elif gateway == "paypal":
                return await self._process_paypal_payment(payment_data)
            else:
                raise ValueError(f"Unsupported payment gateway: {gateway}")
                
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _process_stripe_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment through Stripe"""
        try:
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(float(payment_data["amount"]) * 100),  # Convert to cents
                currency=payment_data.get("currency", "usd"),
                payment_method=payment_data["payment_method"],
                confirmation_method="manual",
                confirm=True,
                return_url=payment_data.get("return_url"),
                metadata={
                    "customer_id": payment_data.get("customer_id"),
                    "order_id": payment_data.get("order_id")
                }
            )
            
            # Record payment
            self._record_payment({
                "gateway": "stripe",
                "amount": payment_data["amount"],
                "currency": payment_data.get("currency", "usd"),
                "status": intent.status,
                "payment_id": intent.id,
                "customer_id": payment_data.get("customer_id"),
                "order_id": payment_data.get("order_id")
            })
            
            return {
                "success": True,
                "payment_id": intent.id,
                "status": intent.status,
                "client_secret": intent.client_secret
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _process_paypal_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment through PayPal"""
        try:
            # Create payment
            payment = self.paypal_client.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "transactions": [{
                    "amount": {
                        "total": str(payment_data["amount"]),
                        "currency": payment_data.get("currency", "USD")
                    },
                    "description": payment_data.get("description", "Payment for order")
                }],
                "redirect_urls": {
                    "return_url": payment_data["return_url"],
                    "cancel_url": payment_data["cancel_url"]
                }
            })
            
            if payment.create():
                # Record payment
                self._record_payment({
                    "gateway": "paypal",
                    "amount": payment_data["amount"],
                    "currency": payment_data.get("currency", "USD"),
                    "status": payment.state,
                    "payment_id": payment.id,
                    "customer_id": payment_data.get("customer_id"),
                    "order_id": payment_data.get("order_id")
                })
                
                return {
                    "success": True,
                    "payment_id": payment.id,
                    "status": payment.state,
                    "approval_url": next(link.href for link in payment.links if link.rel == "approval_url")
                }
            else:
                return {
                    "success": False,
                    "error": payment.error
                }
                
        except Exception as e:
            logger.error(f"PayPal error: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    def _record_payment(self, payment_details: Dict[str, Any]) -> None:
        """Record payment in history"""
        self.payment_history.append({
            **payment_details,
            "timestamp": datetime.now().isoformat()
        })

    async def get_payment_status(self, payment_id: str, gateway: str) -> Dict[str, Any]:
        """Get status of a payment"""
        try:
            if gateway == "stripe":
                payment = stripe.PaymentIntent.retrieve(payment_id)
                return {
                    "success": True,
                    "status": payment.status,
                    "amount": payment.amount / 100,  # Convert from cents
                    "currency": payment.currency,
                    "metadata": payment.metadata
                }
            elif gateway == "paypal":
                payment = self.paypal_client.Payment.find(payment_id)
                return {
                    "success": True,
                    "status": payment.state,
                    "amount": payment.transactions[0].amount.total,
                    "currency": payment.transactions[0].amount.currency
                }
            else:
                raise ValueError(f"Unsupported payment gateway: {gateway}")
                
        except Exception as e:
            logger.error(f"Error getting payment status: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def refund_payment(self, payment_id: str, gateway: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """Refund a payment"""
        try:
            if gateway == "stripe":
                refund = stripe.Refund.create(
                    payment_intent=payment_id,
                    amount=int(amount * 100) if amount else None
                )
                return {
                    "success": True,
                    "refund_id": refund.id,
                    "status": refund.status,
                    "amount": refund.amount / 100
                }
            elif gateway == "paypal":
                payment = self.paypal_client.Payment.find(payment_id)
                sale_id = payment.transactions[0].related_resources[0].sale.id
                sale = self.paypal_client.Sale.find(sale_id)
                refund = sale.refund({
                    "amount": {
                        "total": str(amount) if amount else payment.transactions[0].amount.total,
                        "currency": payment.transactions[0].amount.currency
                    }
                })
                return {
                    "success": True,
                    "refund_id": refund.id,
                    "status": refund.state,
                    "amount": float(refund.amount.total)
                }
            else:
                raise ValueError(f"Unsupported payment gateway: {gateway}")
                
        except Exception as e:
            logger.error(f"Error refunding payment: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def get_payment_history(self, customer_id: Optional[str] = None,
                                gateway: Optional[str] = None,
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get payment history with optional filtering"""
        try:
            history = self.payment_history
            
            if customer_id:
                history = [p for p in history if p.get("customer_id") == customer_id]
                
            if gateway:
                history = [p for p in history if p["gateway"] == gateway]
                
            if limit:
                history = history[-limit:]
                
            return history
            
        except Exception as e:
            logger.error(f"Error getting payment history: {str(e)}")
            capture_exception(e)
            return []

    async def get_analytics(self) -> Dict[str, Any]:
        """Get payment analytics"""
        try:
            stripe_payments = [p for p in self.payment_history if p["gateway"] == "stripe"]
            paypal_payments = [p for p in self.payment_history if p["gateway"] == "paypal"]
            
            return {
                "total_payments": len(self.payment_history),
                "total_amount": sum(float(p["amount"]) for p in self.payment_history),
                "by_gateway": {
                    "stripe": {
                        "count": len(stripe_payments),
                        "amount": sum(float(p["amount"]) for p in stripe_payments)
                    },
                    "paypal": {
                        "count": len(paypal_payments),
                        "amount": sum(float(p["amount"]) for p in paypal_payments)
                    }
                },
                "recent_payments": self.payment_history[-5:]  # Last 5 payments
            }
            
        except Exception as e:
            logger.error(f"Error getting payment analytics: {str(e)}")
            capture_exception(e)
            return {}
