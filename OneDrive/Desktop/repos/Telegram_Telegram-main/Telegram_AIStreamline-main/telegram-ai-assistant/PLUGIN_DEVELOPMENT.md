# Plugin Development Guide

This guide explains how to create new plugins for the AI-Powered Telegram Assistant and extend existing functionality.

## Plugin Architecture

Each plugin is a Python module that follows a standard interface and can be dynamically loaded by the system.

### Plugin Structure

```python
class MyNewPlugin:
    def __init__(self, config: Dict[str, Any]):
        """Initialize plugin with configuration"""
        self.config = config
        # Initialize plugin-specific resources

    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process incoming messages"""
        pass

    async def get_status(self) -> Dict[str, Any]:
        """Get plugin status"""
        pass

    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass
```

## Creating a New Plugin

1. **Create Plugin Module**

Create a new file in `backend/modules/` (e.g., `my_plugin.py`):

```python
import logging
from typing import Dict, Any
from sentry_config import capture_exception

logger = logging.getLogger(__name__)

class MyPlugin:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.plugin_config = config["plugins"]["my_plugin"]
        logger.info("MyPlugin initialized")

    async def process_message(self, message: str) -> Dict[str, Any]:
        try:
            # Implement message processing logic
            result = await self._process_logic(message)
            return {
                "success": True,
                "response": result
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }

    async def _process_logic(self, message: str) -> str:
        # Implement your custom logic here
        pass

    async def get_status(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "config": self.plugin_config
        }

    async def cleanup(self) -> None:
        # Cleanup any resources
        pass
```

2. **Add Configuration**

Add plugin configuration to `config.example.json`:

```json
{
    "plugins": {
        "my_plugin": {
            "enabled": true,
            "setting1": "value1",
            "setting2": "value2"
        }
    }
}
```

3. **Register Plugin**

Update `plugins_config.json`:

```json
{
    "enabled_plugins": {
        "my_plugin": true
    }
}
```

4. **Implement Plugin Logic**

Example implementation with API integration:

```python
class APIPlugin:
    def __init__(self, config):
        self.config = config
        self.api_key = config["plugins"]["api_plugin"]["api_key"]
        self.client = APIClient(self.api_key)

    async def process_message(self, message: str) -> Dict[str, Any]:
        try:
            # Call external API
            response = await self.client.make_request(message)
            
            # Process response
            result = self._process_response(response)
            
            return {
                "success": True,
                "response": result
            }
        except Exception as e:
            capture_exception(e)
            return {
                "success": False,
                "error": str(e)
            }
```

## Plugin Best Practices

1. **Error Handling**
```python
try:
    result = await self._process_logic()
except Exception as e:
    logger.error(f"Error: {str(e)}")
    capture_exception(e)
    raise
```

2. **Resource Management**
```python
async def cleanup(self) -> None:
    try:
        await self.client.close()
        if hasattr(self, 'connection'):
            await self.connection.close()
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
```

3. **Configuration Validation**
```python
def _validate_config(self, config: Dict[str, Any]) -> None:
    required_keys = ['api_key', 'endpoint']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config: {key}")
```

4. **Async Support**
```python
async def process_message(self, message: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(self.endpoint, json={'message': message}) as response:
            return await response.json()
```

## Integration Examples

1. **API Integration Plugin**
```python
class APIIntegrationPlugin:
    async def process_message(self, message: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, json={'message': message}) as response:
                result = await response.json()
                return {
                    "success": True,
                    "response": result
                }
```

2. **Database Plugin**
```python
class DatabasePlugin:
    def __init__(self, config):
        self.engine = create_async_engine(config["database_url"])
        self.Session = sessionmaker(self.engine, class_=AsyncSession)

    async def process_message(self, message: str) -> Dict[str, Any]:
        async with self.Session() as session:
            result = await session.execute(select(Model).where(Model.id == message))
            return {
                "success": True,
                "data": result.scalar_one_or_none()
            }
```

3. **Scheduled Task Plugin**
```python
class ScheduledTaskPlugin:
    def __init__(self, config):
        self.scheduler = TaskScheduler(config)
        self.scheduler.add_job(
            self._scheduled_task,
            'interval',
            minutes=30
        )

    async def _scheduled_task(self):
        # Implement scheduled task logic
        pass
```

## Testing Plugins

1. **Create Test File**

```python
import pytest
from your_plugin import YourPlugin

@pytest.fixture
async def plugin():
    config = {
        "plugins": {
            "your_plugin": {
                "setting": "value"
            }
        }
    }
    return YourPlugin(config)

async def test_process_message(plugin):
    result = await plugin.process_message("test")
    assert result["success"] == True
```

2. **Run Tests**

```bash
pytest tests/test_your_plugin.py -v
```

## Monitoring & Logging

1. **Add Metrics**
```python
from prometheus_client import Counter, Histogram

class MetricsPlugin:
    def __init__(self, config):
        self.requests = Counter(
            'plugin_requests_total',
            'Total plugin requests'
        )
        self.processing_time = Histogram(
            'plugin_processing_seconds',
            'Time spent processing requests'
        )
```

2. **Add Logging**
```python
logger = logging.getLogger(__name__)

class LoggingPlugin:
    async def process_message(self, message: str) -> Dict[str, Any]:
        logger.info(f"Processing message: {message}")
        try:
            result = await self._process()
            logger.info(f"Success: {result}")
            return result
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            raise
```

## Deployment

1. **Update Requirements**

Add plugin dependencies to `requirements.txt`:
```txt
your-package==1.0.0
another-package==2.0.0
```

2. **Environment Variables**

Add plugin-specific environment variables to `.env`:
```env
YOUR_PLUGIN_API_KEY=xxx
YOUR_PLUGIN_ENDPOINT=https://api.example.com
```

3. **Documentation**

Update README.md with plugin documentation:
```markdown
## YourPlugin

Description of your plugin functionality.

### Configuration
- `api_key`: API key for external service
- `endpoint`: API endpoint URL

### Usage
Example of how to use your plugin.
```

## Scaling Considerations

1. **Resource Management**
- Implement connection pooling
- Use caching where appropriate
- Implement rate limiting
- Handle backpressure

2. **Performance**
- Optimize database queries
- Implement caching
- Use connection pooling
- Handle concurrent requests

3. **Monitoring**
- Add performance metrics
- Implement health checks
- Set up alerting
- Log important events

Remember to:
- Follow coding standards
- Add comprehensive documentation
- Include tests
- Handle errors gracefully
- Implement proper cleanup
- Add monitoring
