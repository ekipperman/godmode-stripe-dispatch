import logging
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio
from datetime import datetime
import json
from decimal import Decimal
from sentry_config import capture_exception
import stripe
from coinbase_commerce.client import Client as CoinbaseClient
from bitpay.client import Client as BitPayClient

logger = logging.getLogger(__name__)

class UnifiedPaymentGateway:
    def __init__(self, config: Dict[str, Any]):
        """Initialize unified payment gateway"""
        self.config = config
        self.payment_config = config["plugins"]["payment_gateway"]
        
        # Initialize Stripe
        stripe.api_key = self.payment_config["stripe"]["secret_key"]
        
        # Initialize Coinbase Commerce
        self.coinbase = CoinbaseClient(api_key=self.payment_config["coinbase"]["api_key"])
        
        # Initialize BitPay
        self.bitpay = BitPayClient(
            api_key=self.payment_config["bitpay"]["api_key"],
            merchant_token=self.payment_config["bitpay"]["merchant_token"]
        )
        
        # Initialize transaction history
        self.transaction_history: List[Dict[str, Any]] = []
        
        logger.info("Unified Payment Gateway initialized")

    async def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create payment based on selected method"""
        try:
            method = payment_data["payment_method"]
            amount = Decimal(payment_data["amount"])
            currency = payment_data.get("currency", "USD")
            
            if method == "credit_card":
                return await self._create_stripe_payment(payment_data)
            elif method == "crypto":
                crypto_provider = payment_data.get("crypto_provider", "coinbase")
                if crypto_provider == "coinbase":
                    return await self._create_coinbase_payment(payment_data)
                elif crypto_provider == "bitpay":
                    return await self._create_bitpay_payment(payment_data)
                else:
                    raise ValueError(f"Unsupported crypto provider: {crypto_provider}")
            else:
                raise ValueError(f"Unsupported payment method: {method}")

        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _create_stripe_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Stripe payment intent"""
        try:
            amount = int(Decimal(payment_data["amount"]) * 100)  # Convert to cents
            currency = payment_data.get("currency", "USD").lower()
            
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method_types=["card"],
                metadata={
                    "order_id": payment_data.get("order_id"),
                    "customer_id": payment_data.get("customer_id")
                }
            )
            
            # Record transaction
            self._record_transaction(
                payment_method="credit_card",
                provider="stripe",
                amount=payment_data["amount"],
                currency=currency,
                status="pending",
                transaction_id=intent.id
            )
            
            return {
                "success": True,
                "payment_intent": intent.id,
                "client_secret": intent.client_secret
            }

        except Exception as e:
            logger.error(f"Error creating Stripe payment: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _create_coinbase_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Coinbase Commerce payment"""
        try:
            charge = self.coinbase.charge.create(
                name=payment_data.get("description", "Payment"),
                description=payment_data.get("description", "Payment"),
                pricing_type="fixed_price",
                local_price={
                    "amount": str(payment_data["amount"]),
                    "currency": payment_data.get("currency", "USD")
                },
                metadata={
                    "order_id": payment_data.get("order_id"),
                    "customer_id": payment_data.get("customer_id")
                }
            )
            
            # Record transaction
            self._record_transaction(
                payment_method="crypto",
                provider="coinbase",
                amount=payment_data["amount"],
                currency=payment_data.get("currency", "USD"),
                status="pending",
                transaction_id=charge.id
            )
            
            return {
                "success": True,
                "charge_id": charge.id,
                "hosted_url": charge.hosted_url,
                "addresses": charge.addresses
            }

        except Exception as e:
            logger.error(f"Error creating Coinbase payment: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _create_bitpay_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create BitPay invoice"""
        try:
            invoice = self.bitpay.create_invoice({
                "price": float(payment_data["amount"]),
                "currency": payment_data.get("currency", "USD"),
                "orderId": payment_data.get("order_id"),
                "notificationURL": self.payment_config["bitpay"]["webhook_url"],
                "redirectURL": payment_data.get("redirect_url"),
                "buyer": {
                    "email": payment_data.get("customer_email")
                }
            })
            
            # Record transaction
            self._record_transaction(
                payment_method="crypto",
                provider="bitpay",
                amount=payment_data["amount"],
                currency=payment_data.get("currency", "USD"),
                status="pending",
                transaction_id=invoice["id"]
            )
            
            return {
                "success": True,
                "invoice_id": invoice["id"],
                "payment_url": invoice["url"],
                "status": invoice["status"]
            }

        except Exception as e:
            logger.error(f"Error creating BitPay payment: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def handle_webhook(self, provider: str, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment webhook from various providers"""
        try:
            if provider == "stripe":
                return await self._handle_stripe_webhook(webhook_data)
            elif provider == "coinbase":
                return await self._handle_coinbase_webhook(webhook_data)
            elif provider == "bitpay":
                return await self._handle_bitpay_webhook(webhook_data)
            else:
                raise ValueError(f"Unsupported webhook provider: {provider}")

        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_stripe_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Stripe webhook"""
        try:
            event = stripe.Event.construct_from(webhook_data, stripe.api_key)
            
            if event.type == "payment_intent.succeeded":
                payment_intent = event.data.object
                self._update_transaction_status(
                    transaction_id=payment_intent.id,
                    new_status="completed"
                )
                return {"success": True, "status": "completed"}
                
            elif event.type == "payment_intent.payment_failed":
                payment_intent = event.data.object
                self._update_transaction_status(
                    transaction_id=payment_intent.id,
                    new_status="failed"
                )
                return {"success": True, "status": "failed"}
            
            return {"success": True, "status": "unhandled"}

        except Exception as e:
            logger.error(f"Error handling Stripe webhook: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_coinbase_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Coinbase Commerce webhook"""
        try:
            event = webhook_data["event"]
            
            if event["type"] == "charge:confirmed":
                charge = event["data"]
                self._update_transaction_status(
                    transaction_id=charge["id"],
                    new_status="completed"
                )
                return {"success": True, "status": "completed"}
                
            elif event["type"] == "charge:failed":
                charge = event["data"]
                self._update_transaction_status(
                    transaction_id=charge["id"],
                    new_status="failed"
                )
                return {"success": True, "status": "failed"}
            
            return {"success": True, "status": "unhandled"}

        except Exception as e:
            logger.error(f"Error handling Coinbase webhook: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _handle_bitpay_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle BitPay webhook"""
        try:
            if webhook_data["status"] == "confirmed":
                self._update_transaction_status(
                    transaction_id=webhook_data["id"],
                    new_status="completed"
                )
                return {"success": True, "status": "completed"}
                
            elif webhook_data["status"] in ["invalid", "expired"]:
                self._update_transaction_status(
                    transaction_id=webhook_data["id"],
                    new_status="failed"
                )
                return {"success": True, "status": "failed"}
            
            return {"success": True, "status": "unhandled"}

        except Exception as e:
            logger.error(f"Error handling BitPay webhook: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    def _record_transaction(self, payment_method: str, provider: str, amount: Decimal,
                          currency: str, status: str, transaction_id: str) -> None:
        """Record payment transaction"""
        self.transaction_history.append({
            "timestamp": datetime.now().isoformat(),
            "payment_method": payment_method,
            "provider": provider,
            "amount": str(amount),
            "currency": currency,
            "status": status,
            "transaction_id": transaction_id
        })

    def _update_transaction_status(self, transaction_id: str, new_status: str) -> None:
        """Update transaction status"""
        for transaction in self.transaction_history:
            if transaction["transaction_id"] == transaction_id:
                transaction["status"] = new_status
                transaction["updated_at"] = datetime.now().isoformat()
                break

    async def get_transaction_history(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get transaction history with optional filters"""
        try:
            history = self.transaction_history
            
            if filters:
                if "payment_method" in filters:
                    history = [t for t in history if t["payment_method"] == filters["payment_method"]]
                if "provider" in filters:
                    history = [t for t in history if t["provider"] == filters["provider"]]
                if "status" in filters:
                    history = [t for t in history if t["status"] == filters["status"]]
                if "start_date" in filters:
                    start = datetime.fromisoformat(filters["start_date"])
                    history = [t for t in history if datetime.fromisoformat(t["timestamp"]) >= start]
                if "end_date" in filters:
                    end = datetime.fromisoformat(filters["end_date"])
                    history = [t for t in history if datetime.fromisoformat(t["timestamp"]) <= end]
            
            return history

        except Exception as e:
            logger.error(f"Error getting transaction history: {str(e)}")
            capture_exception(e)
            return []

    async def get_transaction_stats(self) -> Dict[str, Any]:
        """Get transaction statistics"""
        try:
            stats = {
                "total_transactions": len(self.transaction_history),
                "total_amount": {},
                "by_payment_method": {
                    "credit_card": 0,
                    "crypto": 0
                },
                "by_status": {
                    "completed": 0,
                    "pending": 0,
                    "failed": 0
                }
            }
            
            for transaction in self.transaction_history:
                # Update total amount by currency
                currency = transaction["currency"]
                amount = Decimal(transaction["amount"])
                if currency not in stats["total_amount"]:
                    stats["total_amount"][currency] = amount
                else:
                    stats["total_amount"][currency] += amount
                
                # Update payment method counts
                stats["by_payment_method"][transaction["payment_method"]] += 1
                
                # Update status counts
                stats["by_status"][transaction["status"]] += 1
            
            return stats

        except Exception as e:
            logger.error(f"Error getting transaction stats: {str(e)}")
            capture_exception(e)
            return {
                "error": str(e)
            }
