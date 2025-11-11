"""
Streamlit UI for AgenticCTI.
Provides dashboard, reports, manual run, and MCP configuration.
"""

import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime, time
import json
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import CTIAgent
from mcp import EmailNotifier, CTIScheduler
from exporters import STIXExporter, TrendVisionOneClient, OpenCTIClient
from llm import LLMFactory
import logging

# Configure page
st.set_page_config(
    page_title="AgenticCTI Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'scheduler' not in st.session_state:
    st.session_state.scheduler = None


def check_authentication():
    """Check if authentication is required and validate."""
    auth_enabled = os.getenv("STREAMLIT_AUTH_ENABLED", "true").lower() == "true"

    if not auth_enabled:
        return True

    if st.session_state.authenticated:
        return True

    # Show login form
    st.title("🔒 AgenticCTI Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            expected_username = os.getenv("STREAMLIT_USERNAME", "admin")
            expected_password = os.getenv("STREAMLIT_PASSWORD", "changeme")

            if username == expected_username and password == expected_password:
                st.session_state.authenticated = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.info("Default credentials: admin / changeme (change in .env file)")
    st.stop()


def load_agent():
    """Load or create CTI agent instance."""
    if st.session_state.agent is None:
        try:
            config = {
                'user_agent': 'AgenticCTI/1.0',
                'timeout': 30,
                'max_retries': 3,
                'rate_limit': 0.5,
                'sources_config_path': './config/cti_sources.yaml',
                'discovery_keywords': [
                    'cyber threat intelligence',
                    'cybersecurity news',
                    'vulnerability reports'
                ]
            }

            llm = LLMFactory.get_default_llm()
            st.session_state.agent = CTIAgent(llm=llm, config=config)
            return st.session_state.agent
        except Exception as e:
            st.error(f"Failed to initialize agent: {e}")
            return None

    return st.session_state.agent


def main():
    """Main application."""
    check_authentication()

    # Sidebar navigation
    st.sidebar.title("🛡️ AgenticCTI")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Daily Reports", "Manual Run", "MCP Config", "Logs & History"]
    )

    if st.sidebar.button("🔄 Refresh"):
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.info(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load agent
    agent = load_agent()

    # Route to appropriate page
    if page == "Dashboard":
        show_dashboard(agent)
    elif page == "Daily Reports":
        show_daily_reports(agent)
    elif page == "Manual Run":
        show_manual_run(agent)
    elif page == "MCP Config":
        show_mcp_config()
    elif page == "Logs & History":
        show_logs_history()


def show_dashboard(agent):
    """Display main dashboard."""
    st.title("🛡️ AgenticCTI Dashboard")

    if agent is None:
        st.error("Agent not initialized. Check configuration.")
        return

    # Agent status
    st.header("Agent Status")

    status = agent.get_status()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Intelligence Items", status.get('total_intelligence_items', 0))

    with col2:
        source_stats = status.get('source_statistics', {})
        st.metric("Active Sources", source_stats.get('enabled_sources', 0))

    with col3:
        last_run = status.get('last_run_time')
        if last_run:
            last_run_str = datetime.fromisoformat(last_run).strftime('%H:%M %d/%m')
        else:
            last_run_str = "Never"
        st.metric("Last Run", last_run_str)

    with col4:
        # Scheduler status
        scheduler_running = st.session_state.scheduler is not None and \
                           st.session_state.scheduler.running
        st.metric("Scheduler", "Running" if scheduler_running else "Stopped")

    st.markdown("---")

    # Source statistics
    st.header("Source Statistics")

    if source_stats:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("By Category")
            by_category = source_stats.get('by_category', {})
            if by_category:
                st.bar_chart(by_category)
            else:
                st.info("No sources configured")

        with col2:
            st.subheader("By Priority")
            by_priority = source_stats.get('by_priority', {})
            if by_priority:
                st.bar_chart(by_priority)
            else:
                st.info("No sources configured")

    # Recent intelligence
    st.markdown("---")
    st.header("Recent Intelligence")

    if agent.collected_intelligence:
        for item in agent.collected_intelligence[-5:]:
            with st.expander(f"📰 {item.get('title', 'No Title')}"):
                st.markdown(f"**URL:** {item.get('url', 'N/A')}")
                st.markdown(f"**Date:** {item.get('publish_date', 'N/A')}")
                st.markdown(f"**Severity:** {item.get('severity', 'N/A').upper()}")
                st.markdown(f"**Summary:** {item.get('summary', 'N/A')}")

                entities = item.get('entities', {})
                if entities.get('cves'):
                    st.markdown(f"**CVEs:** {', '.join(entities['cves'][:5])}")
                if entities.get('threat_actors'):
                    st.markdown(f"**Threat Actors:** {', '.join(entities['threat_actors'][:5])}")
    else:
        st.info("No intelligence collected yet. Run the agent to gather data.")


def show_daily_reports(agent):
    """Display daily reports."""
    st.title("📊 Daily Reports")

    if agent is None:
        st.error("Agent not initialized. Check configuration.")
        return

    # Generate current summary
    if st.button("Generate Current Summary"):
        with st.spinner("Generating summary..."):
            summary = agent.get_daily_summary()
            st.session_state.current_summary = summary

    if 'current_summary' in st.session_state:
        summary = st.session_state.current_summary

        st.header(f"Summary for {summary.get('date', 'N/A')}")

        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Articles", summary.get('total_articles', 0))
        with col2:
            st.metric("Unique CVEs", summary.get('total_cves', 0))
        with col3:
            st.metric("Threat Actors", summary.get('total_threat_actors', 0))
        with col4:
            st.metric("Malware Families", summary.get('total_malware', 0))

        # Severity distribution
        st.subheader("Severity Distribution")
        severity_dist = summary.get('severity_distribution', {})
        if severity_dist:
            st.bar_chart(severity_dist)

        # Top industries
        st.subheader("Top Targeted Industries")
        industries = summary.get('top_industries_targeted', {})
        if industries:
            st.bar_chart(industries)
        else:
            st.info("No industry data available")

        # Critical findings
        st.subheader("Critical Findings")
        critical_findings = summary.get('critical_findings', [])
        if critical_findings:
            for finding in critical_findings:
                with st.expander(f"⚠️ {finding.get('title', 'N/A')}"):
                    st.markdown(f"**Severity:** {finding.get('severity', 'N/A').upper()}")
                    st.markdown(f"**URL:** {finding.get('url', 'N/A')}")
                    st.markdown(f"**Summary:** {finding.get('summary', 'N/A')}")
        else:
            st.success("No critical findings today")

        # Export options
        st.markdown("---")
        st.subheader("Export Report")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📧 Send Email Report"):
                st.info("Email functionality requires configuration")
        with col2:
            if st.button("💾 Download JSON"):
                json_data = json.dumps(summary, indent=2)
                st.download_button(
                    "Download",
                    json_data,
                    f"cti_summary_{summary.get('date', 'report')}.json",
                    "application/json"
                )


def show_manual_run(agent):
    """Show manual agent run interface."""
    st.title("▶️ Manual Agent Run")

    if agent is None:
        st.error("Agent not initialized. Check configuration.")
        return

    st.markdown("Manually trigger the CTI agent to discover sources, scrape content, and analyze threats.")

    col1, col2 = st.columns(2)

    with col1:
        discover_sources = st.checkbox("Discover New Sources", value=False)
        max_sources = st.number_input("Max Sources", min_value=1, max_value=50, value=10)

    with col2:
        max_articles = st.number_input("Max Articles Per Source", min_value=1, max_value=50, value=10)

    st.markdown("---")

    if st.button("🚀 Start Agent Run", type="primary"):
        with st.spinner("Running CTI agent..."):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                status_text.text("Starting agent...")
                progress_bar.progress(10)

                result = agent.run(
                    discover_new_sources=discover_sources,
                    max_sources=max_sources,
                    max_articles_per_source=max_articles
                )

                progress_bar.progress(100)

                if result.success:
                    st.success("✅ Agent run completed successfully!")

                    # Show results
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Sources Discovered", result.sources_discovered)
                    with col2:
                        st.metric("Articles Scraped", result.articles_scraped)
                    with col3:
                        st.metric("Entities Extracted", result.entities_extracted)

                    if result.errors:
                        st.warning(f"⚠️ {len(result.errors)} errors occurred")
                        with st.expander("View Errors"):
                            for error in result.errors:
                                st.error(error)
                else:
                    st.error("❌ Agent run failed")
                    if result.errors:
                        for error in result.errors:
                            st.error(error)

            except Exception as e:
                st.error(f"Error running agent: {e}")
                progress_bar.empty()


def show_mcp_config():
    """Show MCP configuration page."""
    st.title("⚙️ MCP Configuration")

    tabs = st.tabs(["Email Settings", "STIX Export", "Scheduling", "Sources"])

    # Email Settings
    with tabs[0]:
        st.subheader("Email Notification Settings")

        smtp_host = st.text_input("SMTP Host", value=os.getenv("SMTP_HOST", ""))
        smtp_port = st.number_input("SMTP Port", value=int(os.getenv("SMTP_PORT", 587)))
        smtp_username = st.text_input("SMTP Username", value=os.getenv("SMTP_USERNAME", ""))
        smtp_password = st.text_input("SMTP Password", type="password")
        email_from = st.text_input("From Address", value=os.getenv("EMAIL_FROM", ""))
        email_to = st.text_input("To Address", value=os.getenv("EMAIL_TO", ""))

        if st.button("Test Email Connection"):
            if all([smtp_host, smtp_port, smtp_username, smtp_password]):
                try:
                    notifier = EmailNotifier(
                        smtp_host=smtp_host,
                        smtp_port=smtp_port,
                        username=smtp_username,
                        password=smtp_password,
                        from_addr=email_from,
                        use_tls=True
                    )
                    if notifier.test_connection():
                        st.success("✅ Email connection successful!")
                    else:
                        st.error("❌ Email connection failed")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please fill in all required fields")

    # STIX Export
    with tabs[1]:
        st.subheader("STIX 2.1 Export Settings")

        enable_stix = st.checkbox("Enable STIX Export", value=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Trend Vision One**")
            tvo_enabled = st.checkbox("Enable Trend Vision One")
            tvo_api_key = st.text_input("API Key", type="password", key="tvo_key")
            tvo_region = st.selectbox("Region", ["us", "eu", "au", "sg", "in", "jp"])

            if st.button("Test TVO Connection"):
                if tvo_enabled and tvo_api_key:
                    try:
                        client = TrendVisionOneClient(
                            api_key=tvo_api_key,
                            region=tvo_region
                        )
                        if client.test_connection():
                            st.success("✅ Connected to Trend Vision One")
                        else:
                            st.error("❌ Connection failed")
                    except Exception as e:
                        st.error(f"Error: {e}")

        with col2:
            st.markdown("**OpenCTI**")
            opencti_enabled = st.checkbox("Enable OpenCTI")
            opencti_url = st.text_input("URL", value="http://localhost:8080")
            opencti_api_key = st.text_input("API Key", type="password", key="opencti_key")

            if st.button("Test OpenCTI Connection"):
                if opencti_enabled and opencti_api_key:
                    try:
                        client = OpenCTIClient(
                            url=opencti_url,
                            api_key=opencti_api_key
                        )
                        if client.test_connection():
                            st.success("✅ Connected to OpenCTI")
                        else:
                            st.error("❌ Connection failed")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # Scheduling
    with tabs[2]:
        st.subheader("Scheduling Configuration")

        enable_scheduler = st.checkbox("Enable Automated Scheduling", value=True)

        col1, col2 = st.columns(2)
        with col1:
            schedule_hour = st.number_input("Hour (24h format)", min_value=0, max_value=23, value=7)
        with col2:
            schedule_minute = st.number_input("Minute", min_value=0, max_value=59, value=0)

        timezone = st.selectbox(
            "Timezone",
            ["America/Montreal", "America/New_York", "America/Chicago", "America/Los_Angeles",
             "Europe/London", "Europe/Paris", "Asia/Tokyo"],
            index=0
        )

        if st.button("Start Scheduler"):
            try:
                daily_time = time(hour=schedule_hour, minute=schedule_minute)
                scheduler = CTIScheduler(
                    daily_time=daily_time,
                    timezone=timezone
                )
                # Would set callback here in production
                st.session_state.scheduler = scheduler
                scheduler.start()
                st.success(f"✅ Scheduler started for {schedule_hour:02d}:{schedule_minute:02d} {timezone}")
            except Exception as e:
                st.error(f"Error starting scheduler: {e}")

        if st.session_state.scheduler and st.session_state.scheduler.running:
            st.info("Scheduler is currently running")
            status = st.session_state.scheduler.get_status()
            st.json(status)

            if st.button("Stop Scheduler"):
                st.session_state.scheduler.stop()
                st.success("Scheduler stopped")

    # Sources
    with tabs[3]:
        st.subheader("CTI Sources Configuration")

        sources_file = Path("./config/cti_sources.yaml")
        if sources_file.exists():
            with open(sources_file, 'r') as f:
                sources_config = yaml.safe_load(f)

            sources = sources_config.get('sources', [])
            st.write(f"**Total Sources:** {len(sources)}")
            st.write(f"**Enabled Sources:** {len([s for s in sources if s.get('enabled', True)])}")

            for source in sources:
                with st.expander(f"{source.get('name', 'Unknown')} - {source.get('priority', 'N/A')}"):
                    st.markdown(f"**URL:** {source.get('url', 'N/A')}")
                    st.markdown(f"**Type:** {source.get('type', 'N/A')}")
                    st.markdown(f"**Category:** {source.get('category', 'N/A')}")
                    st.markdown(f"**Enabled:** {'Yes' if source.get('enabled', True) else 'No'}")
        else:
            st.warning("Sources configuration file not found")


def show_logs_history():
    """Show logs and history."""
    st.title("📜 Logs & History")

    tabs = st.tabs(["Application Logs", "Sent Emails", "Agent Runs"])

    with tabs[0]:
        st.subheader("Application Logs")

        log_file = Path("./logs/agentic_cti.log")
        if log_file.exists():
            if st.button("Refresh Logs"):
                st.rerun()

            num_lines = st.slider("Number of lines", 10, 500, 100)

            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-num_lines:]
                    st.text_area("Log Output", "".join(recent_lines), height=400)
            except Exception as e:
                st.error(f"Error reading logs: {e}")
        else:
            st.info("No log file found")

    with tabs[1]:
        st.subheader("Sent Emails History")
        st.info("Email history will appear here after emails are sent")

    with tabs[2]:
        st.subheader("Agent Run History")
        st.info("Agent run history will appear here after runs complete")


if __name__ == "__main__":
    main()
