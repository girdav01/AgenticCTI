#!/usr/bin/env python3
"""
AgenticCTI - Autonomous Cyber Threat Intelligence Platform
Main entry point for the application.
"""

import os
import sys
from pathlib import Path
from datetime import time
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging_config import setup_logging, get_logger
from agents import CTIAgent
from mcp import EmailNotifier, CTIScheduler
from exporters import STIXExporter, TrendVisionOneClient, OpenCTIClient, NGTIPClient
from llm import LLMFactory

# Load environment variables
load_dotenv()

# Setup logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "./logs/agentic_cti.log"),
    max_bytes=int(os.getenv("LOG_MAX_BYTES", 10485760)),
    backup_count=int(os.getenv("LOG_BACKUP_COUNT", 5))
)

logger = get_logger(__name__)


class AgenticCTIApp:
    """Main AgenticCTI application."""

    def __init__(self):
        """Initialize the application."""
        logger.info("Initializing AgenticCTI...")

        # Initialize components
        self.agent = None
        self.scheduler = None
        self.email_notifier = None
        self.stix_exporter = None
        self.trend_client = None
        self.opencti_client = None
        self.ngtip_client = None

        self._initialize_components()

    def _initialize_components(self):
        """Initialize all application components."""
        try:
            # Initialize LLM
            logger.info("Initializing LLM...")
            llm = LLMFactory.get_default_llm()

            # Initialize CTI Agent
            logger.info("Initializing CTI Agent...")
            config = {
                'user_agent': os.getenv('PARSING_USER_AGENT', 'AgenticCTI/1.0'),
                'timeout': int(os.getenv('PARSING_TIMEOUT', 30)),
                'max_retries': int(os.getenv('PARSING_MAX_RETRIES', 3)),
                'rate_limit': float(os.getenv('PARSING_RATE_LIMIT', 0.5)),
                'sources_config_path': os.getenv('CTI_SOURCES_FILE', './config/cti_sources.yaml'),
                'discovery_keywords': [
                    'cyber threat intelligence',
                    'cybersecurity news',
                    'vulnerability reports',
                    'threat analysis'
                ]
            }
            self.agent = CTIAgent(llm=llm, config=config)

            # Initialize Email Notifier
            if os.getenv('SMTP_HOST'):
                logger.info("Initializing Email Notifier...")
                try:
                    self.email_notifier = EmailNotifier(
                        smtp_host=os.getenv('SMTP_HOST'),
                        smtp_port=int(os.getenv('SMTP_PORT', 587)),
                        username=os.getenv('SMTP_USERNAME'),
                        password=os.getenv('SMTP_PASSWORD'),
                        from_addr=os.getenv('EMAIL_FROM'),
                        use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize email notifier: {e}")

            # Initialize STIX Exporter
            if os.getenv('ENABLE_STIX_EXPORT', 'true').lower() == 'true':
                logger.info("Initializing STIX Exporter...")
                self.stix_exporter = STIXExporter(
                    identity_name="AgenticCTI",
                    export_path=os.getenv('STIX_EXPORT_PATH', './data/stix_exports')
                )

            # Initialize Trend Vision One
            if os.getenv('TREND_VISION_ONE_ENABLED', 'false').lower() == 'true':
                logger.info("Initializing Trend Vision One client...")
                try:
                    self.trend_client = TrendVisionOneClient(
                        api_key=os.getenv('TREND_VISION_ONE_API_KEY'),
                        region=os.getenv('TREND_VISION_ONE_REGION', 'us')
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize Trend Vision One: {e}")

            # Initialize OpenCTI
            if os.getenv('OPENCTI_ENABLED', 'false').lower() == 'true':
                logger.info("Initializing OpenCTI client...")
                try:
                    self.opencti_client = OpenCTIClient(
                        url=os.getenv('OPENCTI_URL'),
                        api_key=os.getenv('OPENCTI_API_KEY'),
                        ssl_verify=os.getenv('OPENCTI_SSL_VERIFY', 'true').lower() == 'true'
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenCTI: {e}")

            # Initialize NG-TIP
            if os.getenv('NGTIP_ENABLED', 'true').lower() == 'true':
                logger.info("Initializing NG-TIP client...")
                try:
                    self.ngtip_client = NGTIPClient(
                        base_url=os.getenv('NGTIP_URL', 'http://localhost:8503'),
                        api_key=os.getenv('NGTIP_API_KEY'),
                        verify_ssl=os.getenv('NGTIP_SSL_VERIFY', 'true').lower() == 'true'
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize NG-TIP: {e}")

            logger.info("All components initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing components: {e}", exc_info=True)
            raise

    def run_daily_task(self):
        """Execute daily CTI collection and reporting task."""
        logger.info("=" * 60)
        logger.info("Starting daily CTI task")
        logger.info("=" * 60)

        try:
            # Run agent
            logger.info("Running CTI agent...")
            result = self.agent.run(
                discover_new_sources=True,
                max_sources=int(os.getenv('AGENT_MAX_SOURCES', 20)),
                max_articles_per_source=int(os.getenv('AGENT_MAX_ARTICLES_PER_SOURCE', 10))
            )

            if not result.success:
                logger.error("Agent run failed")
                return

            logger.info(f"Agent run completed: {result.articles_scraped} articles, "
                       f"{result.entities_extracted} entity sets extracted")

            # Generate daily summary
            logger.info("Generating daily summary...")
            summary = self.agent.get_daily_summary()

            # Send email notification
            if self.email_notifier:
                logger.info("Sending daily summary email...")
                email_to = os.getenv('EMAIL_TO', '').split(',')
                email_to = [e.strip() for e in email_to if e.strip()]

                if email_to:
                    success = self.email_notifier.send_daily_summary(
                        to_addrs=email_to,
                        summary=summary
                    )
                    if success:
                        logger.info("Daily summary email sent successfully")
                    else:
                        logger.error("Failed to send daily summary email")

            # Export to STIX (if configured)
            if self.stix_exporter and self.agent.collected_intelligence:
                logger.info("Exporting to STIX...")
                # Export logic would go here
                logger.info("STIX export completed")

            # Push to NG-TIP (if configured)
            if self.ngtip_client and self.agent.collected_intelligence:
                logger.info("Pushing intelligence to NG-TIP platform...")
                try:
                    # Push collected intelligence to NG-TIP
                    batch_result = self.ngtip_client.ingest_batch(
                        intelligence_items=self.agent.collected_intelligence
                    )
                    if batch_result:
                        logger.info(f"Successfully pushed {len(self.agent.collected_intelligence)} items to NG-TIP")
                    else:
                        logger.error("Failed to push intelligence to NG-TIP")
                except Exception as e:
                    logger.error(f"Error pushing to NG-TIP: {e}")

            # Clear intelligence for next day
            self.agent.clear_intelligence()

            logger.info("Daily task completed successfully")

        except Exception as e:
            logger.error(f"Error in daily task: {e}", exc_info=True)

    def start_scheduler(self):
        """Start the automated scheduler."""
        logger.info("Starting scheduler...")

        try:
            # Parse daily time
            daily_time_str = os.getenv('EMAIL_DAILY_TIME', '07:00')
            hour, minute = map(int, daily_time_str.split(':'))
            daily_time = time(hour=hour, minute=minute)

            # Create scheduler
            self.scheduler = CTIScheduler(
                daily_time=daily_time,
                timezone=os.getenv('EMAIL_TIMEZONE', 'America/Montreal'),
                task_callback=self.run_daily_task
            )

            # Start scheduler
            self.scheduler.start()

            logger.info(f"Scheduler started for {daily_time_str} {os.getenv('EMAIL_TIMEZONE')}")
            logger.info("Press Ctrl+C to stop")

            # Keep running
            try:
                while self.scheduler.running:
                    import time
                    time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")

        except Exception as e:
            logger.error(f"Error in scheduler: {e}", exc_info=True)
        finally:
            if self.scheduler:
                self.scheduler.stop()
            logger.info("Scheduler stopped")

    def run_once(self):
        """Run the agent once (for testing/manual runs)."""
        logger.info("Running agent once...")
        self.run_daily_task()


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("AgenticCTI - Autonomous Cyber Threat Intelligence")
    logger.info("=" * 60)

    try:
        app = AgenticCTIApp()

        # Check command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()

            if command == "run":
                # Run once
                app.run_once()
            elif command == "schedule":
                # Start scheduler
                app.start_scheduler()
            elif command == "ui":
                # Start Streamlit UI
                logger.info("Starting Streamlit UI...")
                import subprocess
                subprocess.run([
                    sys.executable, "-m", "streamlit", "run",
                    "ui/streamlit_app.py",
                    "--server.port", os.getenv("STREAMLIT_PORT", "8501")
                ])
            else:
                print(f"Unknown command: {command}")
                print("Usage: python main.py [run|schedule|ui]")
                sys.exit(1)
        else:
            # Default: start scheduler
            logger.info("No command specified, starting scheduler...")
            app.start_scheduler()

    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    logger.info("AgenticCTI shutdown complete")


if __name__ == "__main__":
    main()
