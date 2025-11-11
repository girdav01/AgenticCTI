"""
Email notification system for CTI reports.
Sends daily summaries and alerts via SMTP.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Email notification system with SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_addr: str,
        use_tls: bool = True,
        timeout: int = 30
    ):
        """
        Initialize email notifier.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_addr: From email address
            use_tls: Whether to use TLS
            timeout: Connection timeout in seconds

        Raises:
            ValueError: If required parameters are missing
        """
        if not all([smtp_host, smtp_port, username, password, from_addr]):
            raise ValueError("All SMTP parameters are required")

        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.use_tls = use_tls
        self.timeout = timeout

        # Sent email tracking
        self.sent_emails: List[Dict] = []

        logger.info(f"EmailNotifier initialized with SMTP host: {smtp_host}:{smtp_port}")

    def send_email(
        self,
        to_addrs: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Path]] = None,
        cc_addrs: Optional[List[str]] = None,
        bcc_addrs: Optional[List[str]] = None
    ) -> bool:
        """
        Send email via SMTP.

        Args:
            to_addrs: List of recipient email addresses
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            attachments: Optional list of file paths to attach
            cc_addrs: Optional CC addresses
            bcc_addrs: Optional BCC addresses

        Returns:
            True if sent successfully, False otherwise
        """
        logger.info(f"Sending email to {', '.join(to_addrs)}: {subject}")

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(to_addrs)

            if cc_addrs:
                msg['Cc'] = ', '.join(cc_addrs)

            # Add body
            msg.attach(MIMEText(body, 'plain'))

            if html_body:
                msg.attach(MIMEText(html_body, 'html'))

            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    self._add_attachment(msg, attachment_path)

            # Combine all recipients
            all_recipients = to_addrs.copy()
            if cc_addrs:
                all_recipients.extend(cc_addrs)
            if bcc_addrs:
                all_recipients.extend(bcc_addrs)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.timeout) as server:
                if self.use_tls:
                    server.starttls()

                server.login(self.username, self.password)
                server.send_message(msg, from_addr=self.from_addr, to_addrs=all_recipients)

            logger.info(f"Successfully sent email to {len(all_recipients)} recipients")

            # Track sent email
            self._track_sent_email(to_addrs, subject, success=True)

            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            self._track_sent_email(to_addrs, subject, success=False, error=str(e))
            return False

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            self._track_sent_email(to_addrs, subject, success=False, error=str(e))
            return False

        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}", exc_info=True)
            self._track_sent_email(to_addrs, subject, success=False, error=str(e))
            return False

    def _add_attachment(self, msg: MIMEMultipart, filepath: Path) -> None:
        """Add attachment to email message."""
        try:
            if not filepath.exists():
                logger.warning(f"Attachment not found: {filepath}")
                return

            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())

            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filepath.name}'
            )

            msg.attach(part)
            logger.debug(f"Added attachment: {filepath.name}")

        except Exception as e:
            logger.error(f"Error adding attachment {filepath}: {e}")

    def _track_sent_email(
        self,
        recipients: List[str],
        subject: str,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """Track sent email for history."""
        self.sent_emails.append({
            'timestamp': datetime.now().isoformat(),
            'recipients': recipients,
            'subject': subject,
            'success': success,
            'error': error
        })

    def send_daily_summary(
        self,
        to_addrs: List[str],
        summary: Dict[str, Any]
    ) -> bool:
        """
        Send daily CTI summary email.

        Args:
            to_addrs: Recipient addresses
            summary: Summary data from agent

        Returns:
            True if sent successfully
        """
        logger.info("Sending daily CTI summary email")

        try:
            # Generate email content
            subject = f"AgenticCTI Daily Summary - {summary.get('date', datetime.now().strftime('%Y-%m-%d'))}"

            # Plain text body
            body = self._generate_text_summary(summary)

            # HTML body
            html_body = self._generate_html_summary(summary)

            return self.send_email(
                to_addrs=to_addrs,
                subject=subject,
                body=body,
                html_body=html_body
            )

        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return False

    def _generate_text_summary(self, summary: Dict[str, Any]) -> str:
        """Generate plain text summary."""
        lines = [
            "=" * 60,
            f"AgenticCTI Daily Summary - {summary.get('date', 'N/A')}",
            "=" * 60,
            "",
            "OVERVIEW",
            "-" * 60,
            f"Total Articles Analyzed: {summary.get('total_articles', 0)}",
            f"Unique CVEs Identified: {summary.get('total_cves', 0)}",
            f"Threat Actors Detected: {summary.get('total_threat_actors', 0)}",
            f"Malware Families Found: {summary.get('total_malware', 0)}",
            "",
            "SEVERITY DISTRIBUTION",
            "-" * 60,
        ]

        severity_dist = summary.get('severity_distribution', {})
        for severity, count in severity_dist.items():
            lines.append(f"  {severity.upper()}: {count}")

        lines.extend([
            "",
            "TOP TARGETED INDUSTRIES",
            "-" * 60,
        ])

        industries = summary.get('top_industries_targeted', {})
        for industry, count in list(industries.items())[:5]:
            lines.append(f"  {industry}: {count} mentions")

        lines.extend([
            "",
            "CRITICAL FINDINGS",
            "-" * 60,
        ])

        critical_findings = summary.get('critical_findings', [])
        if not critical_findings:
            lines.append("  No critical findings today")
        else:
            for i, finding in enumerate(critical_findings[:5], 1):
                lines.extend([
                    f"{i}. {finding.get('title', 'N/A')}",
                    f"   Severity: {finding.get('severity', 'N/A').upper()}",
                    f"   URL: {finding.get('url', 'N/A')}",
                    f"   Summary: {finding.get('summary', 'N/A')[:200]}...",
                    ""
                ])

        lines.extend([
            "=" * 60,
            "This is an automated report from AgenticCTI",
            "For more details, visit the AgenticCTI dashboard",
            "=" * 60
        ])

        return "\n".join(lines)

    def _generate_html_summary(self, summary: Dict[str, Any]) -> str:
        """Generate HTML summary."""
        critical_findings = summary.get('critical_findings', [])
        severity_dist = summary.get('severity_distribution', {})
        industries = summary.get('top_industries_targeted', {})

        # Build critical findings HTML
        findings_html = ""
        if not critical_findings:
            findings_html = "<p>No critical findings today</p>"
        else:
            findings_html = "<ul>"
            for finding in critical_findings[:5]:
                severity_color = {
                    'critical': '#dc3545',
                    'high': '#fd7e14',
                    'medium': '#ffc107',
                    'low': '#28a745'
                }.get(finding.get('severity', 'medium').lower(), '#6c757d')

                findings_html += f"""
                <li style="margin-bottom: 15px;">
                    <strong>{finding.get('title', 'N/A')}</strong>
                    <span style="background-color: {severity_color}; color: white; padding: 2px 6px;
                                 border-radius: 3px; font-size: 12px; margin-left: 10px;">
                        {finding.get('severity', 'N/A').upper()}
                    </span>
                    <br>
                    <small><a href="{finding.get('url', '#')}">{finding.get('url', 'N/A')}</a></small>
                    <p style="margin-top: 5px;">{finding.get('summary', 'N/A')[:200]}...</p>
                </li>
                """
            findings_html += "</ul>"

        # Build severity distribution HTML
        severity_html = "<ul>"
        for severity, count in severity_dist.items():
            severity_html += f"<li><strong>{severity.upper()}:</strong> {count}</li>"
        severity_html += "</ul>"

        # Build industries HTML
        industries_html = "<ul>"
        for industry, count in list(industries.items())[:5]:
            industries_html += f"<li><strong>{industry}:</strong> {count} mentions</li>"
        industries_html += "</ul>"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .section {{ margin-bottom: 30px; }}
                .section h2 {{ color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
                .stats {{ display: flex; justify-content: space-around; flex-wrap: wrap; }}
                .stat-box {{ background-color: #f8f9fa; padding: 15px; margin: 10px; border-radius: 5px;
                            min-width: 150px; text-align: center; }}
                .stat-number {{ font-size: 32px; font-weight: bold; color: #007bff; }}
                .stat-label {{ font-size: 14px; color: #6c757d; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px;
                          color: #6c757d; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>AgenticCTI Daily Summary</h1>
                <p>{summary.get('date', 'N/A')}</p>
            </div>

            <div class="content">
                <div class="section">
                    <h2>Overview</h2>
                    <div class="stats">
                        <div class="stat-box">
                            <div class="stat-number">{summary.get('total_articles', 0)}</div>
                            <div class="stat-label">Articles Analyzed</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">{summary.get('total_cves', 0)}</div>
                            <div class="stat-label">Unique CVEs</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">{summary.get('total_threat_actors', 0)}</div>
                            <div class="stat-label">Threat Actors</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">{summary.get('total_malware', 0)}</div>
                            <div class="stat-label">Malware Families</div>
                        </div>
                    </div>
                </div>

                <div class="section">
                    <h2>Severity Distribution</h2>
                    {severity_html}
                </div>

                <div class="section">
                    <h2>Top Targeted Industries</h2>
                    {industries_html}
                </div>

                <div class="section">
                    <h2>Critical Findings</h2>
                    {findings_html}
                </div>
            </div>

            <div class="footer">
                <p>This is an automated report from AgenticCTI</p>
                <p>For more details, visit the AgenticCTI dashboard</p>
            </div>
        </body>
        </html>
        """

        return html

    def test_connection(self) -> bool:
        """
        Test SMTP connection.

        Returns:
            True if connection successful
        """
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)

            logger.info("SMTP connection test successful")
            return True

        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False

    def get_sent_emails_history(self, limit: int = 10) -> List[Dict]:
        """
        Get history of sent emails.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of sent email records
        """
        return self.sent_emails[-limit:]
