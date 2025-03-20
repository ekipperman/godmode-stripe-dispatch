from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Dict, Any
import logging
import redis.asyncio as redis
from datetime import datetime
from sentry_config import capture_exception, set_tag

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self, config: Dict[str, Any], plugin_manager: Any):
        """Initialize the task scheduler"""
        self.config = config
        self.plugin_manager = plugin_manager
        self.redis_client = redis.Redis.from_url(config["database"]["redis_url"])
        
        # Configure job stores
        jobstores = {
            'default': RedisJobStore(
                jobs_key='telegram_assistant_jobs',
                run_times_key='telegram_assistant_running',
                connection=self.redis_client
            )
        }
        
        # Configure executors
        executors = {
            'default': ThreadPoolExecutor(20),
            'processpool': ProcessPoolExecutor(5)
        }
        
        # Configure job defaults
        job_defaults = {
            'coalesce': False,
            'max_instances': 3,
            'misfire_grace_time': 30
        }
        
        # Initialize scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        logger.info("Task scheduler initialized")

    async def start(self):
        """Start the scheduler and add default jobs"""
        try:
            # Add default scheduled tasks
            await self._add_default_jobs()
            
            # Start the scheduler
            self.scheduler.start()
            logger.info("Task scheduler started")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            capture_exception(e)
            raise

    async def _add_default_jobs(self):
        """Add default scheduled jobs"""
        try:
            # Social Media Scheduling
            if self.plugin_manager.is_plugin_active("social_media"):
                self.scheduler.add_job(
                    self._scheduled_social_post,
                    'cron',
                    hour='9,13,17',  # Post at 9 AM, 1 PM, and 5 PM
                    id='social_media_post',
                    replace_existing=True
                )
            
            # Analytics Reports
            if self.plugin_manager.is_plugin_active("analytics"):
                self.scheduler.add_job(
                    self._generate_daily_report,
                    'cron',
                    hour=8,  # Generate report at 8 AM daily
                    id='daily_analytics',
                    replace_existing=True
                )
            
            # CRM Sync
            if self.plugin_manager.is_plugin_active("crm"):
                self.scheduler.add_job(
                    self._sync_crm_data,
                    'interval',
                    minutes=30,  # Sync every 30 minutes
                    id='crm_sync',
                    replace_existing=True
                )
            
            # Lead Nurturing
            if self.plugin_manager.is_plugin_active("lead_nurturing"):
                self.scheduler.add_job(
                    self._process_lead_campaigns,
                    'interval',
                    minutes=15,  # Check campaigns every 15 minutes
                    id='lead_nurturing',
                    replace_existing=True
                )
            
            # System Health Check
            self.scheduler.add_job(
                self._system_health_check,
                'interval',
                minutes=5,  # Check system health every 5 minutes
                id='health_check',
                replace_existing=True
            )
            
            logger.info("Default jobs added to scheduler")
            
        except Exception as e:
            logger.error(f"Failed to add default jobs: {str(e)}")
            capture_exception(e)
            raise

    async def _scheduled_social_post(self):
        """Execute scheduled social media posts"""
        try:
            social_plugin = self.plugin_manager.get_plugin("social_media")
            if social_plugin:
                # Get scheduled posts from Redis
                scheduled_posts = await self.redis_client.hgetall("scheduled_social_posts")
                
                for post_id, post_data in scheduled_posts.items():
                    post = json.loads(post_data)
                    if datetime.fromisoformat(post["scheduled_time"]) <= datetime.now():
                        # Post to social media
                        await social_plugin.post_to_all(post["content"])
                        # Remove posted item
                        await self.redis_client.hdel("scheduled_social_posts", post_id)
                        
        except Exception as e:
            logger.error(f"Error in scheduled social post: {str(e)}")
            capture_exception(e)

    async def _generate_daily_report(self):
        """Generate and send daily analytics report"""
        try:
            analytics_plugin = self.plugin_manager.get_plugin("analytics")
            if analytics_plugin:
                report = await analytics_plugin.generate_report(
                    report_type="daily",
                    start_date=(datetime.now() - timedelta(days=1)).isoformat(),
                    end_date=datetime.now().isoformat()
                )
                
                # Store report in Redis for caching
                await self.redis_client.setex(
                    f"daily_report_{datetime.now().date().isoformat()}",
                    86400,  # Cache for 24 hours
                    json.dumps(report)
                )
                
        except Exception as e:
            logger.error(f"Error generating daily report: {str(e)}")
            capture_exception(e)

    async def _sync_crm_data(self):
        """Synchronize CRM data"""
        try:
            crm_plugin = self.plugin_manager.get_plugin("crm")
            if crm_plugin:
                await crm_plugin.sync_all()
                
        except Exception as e:
            logger.error(f"Error syncing CRM data: {str(e)}")
            capture_exception(e)

    async def _process_lead_campaigns(self):
        """Process lead nurturing campaigns"""
        try:
            nurturing_plugin = self.plugin_manager.get_plugin("lead_nurturing")
            if nurturing_plugin:
                # Process will be handled by the plugin's internal logic
                pass
                
        except Exception as e:
            logger.error(f"Error processing lead campaigns: {str(e)}")
            capture_exception(e)

    async def _system_health_check(self):
        """Perform system health check"""
        try:
            # Check Redis connection
            await self.redis_client.ping()
            
            # Check plugin status
            active_plugins = self.plugin_manager.get_active_plugins()
            
            # Store health metrics in Redis
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "redis_status": "healthy",
                "active_plugins": len(active_plugins),
                "scheduler_running": self.scheduler.running
            }
            
            await self.redis_client.setex(
                "system_health",
                300,  # Cache for 5 minutes
                json.dumps(health_data)
            )
            
            # Set Sentry tag for monitoring
            set_tag("system_health", "healthy")
            
        except Exception as e:
            logger.error(f"Error in system health check: {str(e)}")
            capture_exception(e)
            set_tag("system_health", "unhealthy")

    async def add_job(self, func, trigger, **trigger_args):
        """Add a new job to the scheduler"""
        try:
            job = self.scheduler.add_job(func, trigger, **trigger_args)
            logger.info(f"Added new job: {job.id}")
            return job
            
        except Exception as e:
            logger.error(f"Failed to add job: {str(e)}")
            capture_exception(e)
            raise

    async def remove_job(self, job_id: str):
        """Remove a job from the scheduler"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to remove job: {str(e)}")
            capture_exception(e)
            raise

    async def shutdown(self):
        """Shutdown the scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Task scheduler shutdown complete")
                
        except Exception as e:
            logger.error(f"Error during scheduler shutdown: {str(e)}")
            capture_exception(e)
            raise
