import pytest
import stripe
import paypalrestsdk
from unittest.mock import Mock, patch
from datetime import datetime
from modules.payment_gateway import PaymentGateway

@pytest.fixture
def config():
    return {
        "plugins": {
            "payment_gateway": {
                "stripe": {
                    "enabled": True,
                    "secret_key": "test_stripe_key",
                    "webhook_secret": "test_webhook_secret"
                },
                "paypal": {
                    "enabled": True,
                    "mode": "sandbox",
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret"
                }
            }
        }
    }

@pytest.fixture
def payment_gateway(config):
    return PaymentGateway(config)

@pytest.fixture
def stripe_payment_data():
    return {
        "gateway": "stripe",
        "amount": 100.00,
        "currency": "usd",
        "payment_method": "pm_card_visa",
        "customer_id": "cust_123",
        "order_id": "order_123",
        "return_url": "https://example.com/return"
    }

@pytest.fixture
def paypal_payment_data():
    return {
        "gateway": "paypal",
        "amount": 100.00,
        "currency": "USD",
        "customer_id": "cust_123",
        "order_id": "order_123",
        "description": "Test payment",
        "return_url": "https://example.com/return",
        "cancel_url": "https://example.com/cancel"
    }

@pytest.mark.asyncio
async def test_process_stripe_payment_success(payment_gateway, stripe_payment_data):
    # Mock Stripe PaymentIntent
    mock_intent = Mock()
    mock_intent.id = "pi_123"
    mock_intent.status = "succeeded"
    mock_intent.client_secret = "secret_123"

    with patch.object(stripe.PaymentIntent, 'create', return_value=mock_intent):
        result = await payment_gateway._process_stripe_payment(stripe_payment_data)
        
        assert result["success"] is True
        assert result["payment_id"] == "pi_123"
        assert result["status"] == "succeeded"
        assert result["client_secret"] == "secret_123"

@pytest.mark.asyncio
async def test_process_stripe_payment_failure(payment_gateway, stripe_payment_data):
    with patch.object(stripe.PaymentIntent, 'create', side_effect=stripe.error.CardError(
        "Card declined", "card_declined", "error_code"
    )):
        result = await payment_gateway._process_stripe_payment(stripe_payment_data)
        
        assert result["success"] is False
        assert "error" in result

@pytest.mark.asyncio
async def test_process_paypal_payment_success(payment_gateway, paypal_payment_data):
    # Mock PayPal Payment
    mock_payment = Mock()
    mock_payment.id = "PAY-123"
    mock_payment.state = "approved"
    mock_payment.links = [
        Mock(rel="approval_url", href="https://paypal.com/approve")
    ]
    mock_payment.create = Mock(return_value=True)

    with patch.object(paypalrestsdk, 'Payment', return_value=mock_payment):
        result = await payment_gateway._process_paypal_payment(paypal_payment_data)
        
        assert result["success"] is True
        assert result["payment_id"] == "PAY-123"
        assert result["status"] == "approved"
        assert "approval_url" in result

@pytest.mark.asyncio
async def test_process_paypal_payment_failure(payment_gateway, paypal_payment_data):
    # Mock PayPal Payment failure
    mock_payment = Mock()
    mock_payment.create = Mock(return_value=False)
    mock_payment.error = "Payment failed"

    with patch.object(paypalrestsdk, 'Payment', return_value=mock_payment):
        result = await payment_gateway._process_paypal_payment(paypal_payment_data)
        
        assert result["success"] is False
        assert result["error"] == "Payment failed"

@pytest.mark.asyncio
async def test_get_payment_status_stripe(payment_gateway):
    mock_payment = Mock()
    mock_payment.status = "succeeded"
    mock_payment.amount = 10000  # cents
    mock_payment.currency = "usd"
    mock_payment.metadata = {"order_id": "123"}

    with patch.object(stripe.PaymentIntent, 'retrieve', return_value=mock_payment):
        result = await payment_gateway.get_payment_status("pi_123", "stripe")
        
        assert result["success"] is True
        assert result["status"] == "succeeded"
        assert result["amount"] == 100.00
        assert result["currency"] == "usd"
        assert "metadata" in result

@pytest.mark.asyncio
async def test_get_payment_status_paypal(payment_gateway):
    mock_payment = Mock()
    mock_payment.state = "completed"
    mock_payment.transactions = [
        Mock(amount=Mock(total="100.00", currency="USD"))
    ]

    with patch.object(paypalrestsdk.Payment, 'find', return_value=mock_payment):
        result = await payment_gateway.get_payment_status("PAY-123", "paypal")
        
        assert result["success"] is True
        assert result["status"] == "completed"
        assert result["amount"] == "100.00"
        assert result["currency"] == "USD"

@pytest.mark.asyncio
async def test_refund_payment_stripe(payment_gateway):
    mock_refund = Mock()
    mock_refund.id = "re_123"
    mock_refund.status = "succeeded"
    mock_refund.amount = 10000  # cents

    with patch.object(stripe.Refund, 'create', return_value=mock_refund):
        result = await payment_gateway.refund_payment("pi_123", "stripe", 100.00)
        
        assert result["success"] is True
        assert result["refund_id"] == "re_123"
        assert result["status"] == "succeeded"
        assert result["amount"] == 100.00

@pytest.mark.asyncio
async def test_refund_payment_paypal(payment_gateway):
    mock_payment = Mock()
    mock_payment.transactions = [
        Mock(related_resources=[Mock(sale=Mock(id="SALE-123"))])
    ]
    
    mock_sale = Mock()
    mock_sale.id = "SALE-123"
    
    mock_refund = Mock()
    mock_refund.id = "REFUND-123"
    mock_refund.state = "completed"
    mock_refund.amount = Mock(total="100.00")

    with patch.object(paypalrestsdk.Payment, 'find', return_value=mock_payment), \
         patch.object(paypalrestsdk.Sale, 'find', return_value=mock_sale), \
         patch.object(mock_sale, 'refund', return_value=mock_refund):
        result = await payment_gateway.refund_payment("PAY-123", "paypal", 100.00)
        
        assert result["success"] is True
        assert result["refund_id"] == "REFUND-123"
        assert result["status"] == "completed"
        assert result["amount"] == 100.00

@pytest.mark.asyncio
async def test_get_payment_history(payment_gateway):
    # Add some test payments to history
    payment_gateway.payment_history = [
        {
            "gateway": "stripe",
            "amount": 100.00,
            "currency": "usd",
            "status": "succeeded",
            "payment_id": "pi_123",
            "customer_id": "cust_123",
            "timestamp": datetime.now().isoformat()
        },
        {
            "gateway": "paypal",
            "amount": 50.00,
            "currency": "USD",
            "status": "completed",
            "payment_id": "PAY-123",
            "customer_id": "cust_456",
            "timestamp": datetime.now().isoformat()
        }
    ]

    # Test filtering by customer
    history = await payment_gateway.get_payment_history(customer_id="cust_123")
    assert len(history) == 1
    assert history[0]["customer_id"] == "cust_123"

    # Test filtering by gateway
    history = await payment_gateway.get_payment_history(gateway="paypal")
    assert len(history) == 1
    assert history[0]["gateway"] == "paypal"

    # Test limit
    history = await payment_gateway.get_payment_history(limit=1)
    assert len(history) == 1

@pytest.mark.asyncio
async def test_get_analytics(payment_gateway):
    # Add some test payments to history
    payment_gateway.payment_history = [
        {
            "gateway": "stripe",
            "amount": 100.00,
            "currency": "usd",
            "status": "succeeded",
            "payment_id": "pi_123",
            "timestamp": datetime.now().isoformat()
        },
        {
            "gateway": "paypal",
            "amount": 50.00,
            "currency": "USD",
            "status": "completed",
            "payment_id": "PAY-123",
            "timestamp": datetime.now().isoformat()
        }
    ]

    analytics = await payment_gateway.get_analytics()
    
    assert analytics["total_payments"] == 2
    assert analytics["total_amount"] == 150.00
    assert analytics["by_gateway"]["stripe"]["count"] == 1
    assert analytics["by_gateway"]["stripe"]["amount"] == 100.00
    assert analytics["by_gateway"]["paypal"]["count"] == 1
    assert analytics["by_gateway"]["paypal"]["amount"] == 50.00
    assert len(analytics["recent_payments"]) == 2
