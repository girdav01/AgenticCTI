"""
Scheduler for automated CTI tasks.
Handles daily scheduled runs at specified times with timezone support.
"""

import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime, time
from threading import Thread, Event
import time as time_module
import pytz

logger = logging.getLogger(__name__)


class CTIScheduler:
    """Scheduler for automated CTI agent runs."""

    def __init__(
        self,
        daily_time: time,
        timezone: str = "America/Montreal",
        task_callback: Optional[Callable] = None
    ):
        """
        Initialize scheduler.

        Args:
            daily_time: Time to run daily task (datetime.time object)
            timezone: Timezone name (e.g., 'America/Montreal')
            task_callback: Function to call when task triggers

        Raises:
            ValueError: If timezone is invalid
        """
        try:
            self.timezone = pytz.timezone(timezone)
        except pytz.UnknownTimeZoneError:
            logger.error(f"Unknown timezone: {timezone}")
            raise ValueError(f"Invalid timezone: {timezone}")

        self.daily_time = daily_time
        self.task_callback = task_callback
        self.running = False
        self.stop_event = Event()
        self.thread: Optional[Thread] = None
        self.last_run: Optional[datetime] = None

        logger.info(f"CTIScheduler initialized for {daily_time.strftime('%H:%M')} {timezone}")

    def start(self) -> None:
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return

        logger.info("Starting scheduler...")
        self.running = True
        self.stop_event.clear()

        self.thread = Thread(target=self._run_loop, daemon=True)
        self.thread.start()

        logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.running:
            return

        logger.info("Stopping scheduler...")
        self.running = False
        self.stop_event.set()

        if self.thread:
            self.thread.join(timeout=5)

        logger.info("Scheduler stopped")

    def _run_loop(self) -> None:
        """Main scheduler loop."""
        logger.info("Scheduler loop started")

        while not self.stop_event.is_set():
            try:
                # Get current time in configured timezone
                now = datetime.now(self.timezone)
                current_time = now.time()

                # Calculate next run time
                next_run = self._calculate_next_run(now)

                # Check if it's time to run
                if self._should_run(now):
                    logger.info(f"Triggering scheduled task at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    self._execute_task()
                    self.last_run = now

                # Sleep until next check (1 minute)
                self.stop_event.wait(60)

            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                self.stop_event.wait(60)

        logger.info("Scheduler loop ended")

    def _should_run(self, now: datetime) -> bool:
        """
        Check if task should run now.

        Args:
            now: Current datetime

        Returns:
            True if should run
        """
        current_time = now.time()

        # Check if current time matches scheduled time (within 1 minute window)
        target_minutes = self.daily_time.hour * 60 + self.daily_time.minute
        current_minutes = current_time.hour * 60 + current_time.minute

        # Allow 1-minute window
        time_match = abs(target_minutes - current_minutes) <= 1

        if not time_match:
            return False

        # Check if already ran today
        if self.last_run:
            last_run_date = self.last_run.date()
            current_date = now.date()

            if last_run_date == current_date:
                logger.debug("Task already ran today")
                return False

        return True

    def _calculate_next_run(self, now: datetime) -> datetime:
        """Calculate next run time."""
        next_run = now.replace(
            hour=self.daily_time.hour,
            minute=self.daily_time.minute,
            second=0,
            microsecond=0
        )

        # If time has passed today, schedule for tomorrow
        if next_run <= now:
            next_run = next_run.replace(day=next_run.day + 1)

        return next_run

    def _execute_task(self) -> None:
        """Execute the scheduled task."""
        if not self.task_callback:
            logger.warning("No task callback configured")
            return

        try:
            logger.info("Executing scheduled task...")
            self.task_callback()
            logger.info("Scheduled task completed")

        except Exception as e:
            logger.error(f"Error executing scheduled task: {e}", exc_info=True)

    def set_task_callback(self, callback: Callable) -> None:
        """
        Set the task callback function.

        Args:
            callback: Function to call when task triggers
        """
        self.task_callback = callback
        logger.info("Task callback updated")

    def get_next_run(self) -> Optional[datetime]:
        """
        Get next scheduled run time.

        Returns:
            Next run datetime or None
        """
        if not self.running:
            return None

        now = datetime.now(self.timezone)
        return self._calculate_next_run(now)

    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status.

        Returns:
            Dictionary with scheduler status
        """
        next_run = self.get_next_run()

        return {
            'running': self.running,
            'daily_time': self.daily_time.strftime('%H:%M'),
            'timezone': str(self.timezone),
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': next_run.isoformat() if next_run else None
        }

    def run_now(self) -> None:
        """Manually trigger task execution."""
        logger.info("Manually triggering task...")
        self._execute_task()
