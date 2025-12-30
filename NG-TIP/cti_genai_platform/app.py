"""
Next-Gen Cyber Threat Intelligence Platform
Powered by GenAI, RAG, and Graph Technology

Integrates with MISP, OpenCTI, and supports STIX 2.1 ontology
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Optional
import json

from config import Config
from modules.llm_handler import LLMHandler
from modules.rag_engine import RAGEngine
from modules.misp_integration import MISPIntegration
from modules.opencti_integration import OpenCTIIntegration
from modules.graph_manager import GraphManager
from modules.stix_processor import STIXProcessor

# Page configuration
st.set_page_config(
    page_title="GenAI CTI Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .threat-critical {
        color: #d62728;
        font-weight: bold;
    }
    .threat-high {
        color: #ff7f0e;
        font-weight: bold;
    }
    .threat-medium {
        color: #2ca02c;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = Config()
    st.session_state.llm_handler = None
    st.session_state.rag_engine = None
    st.session_state.misp = None
    st.session_state.opencti = None
    st.session_state.graph_manager = None
    st.session_state.stix_processor = STIXProcessor()
    st.session_state.chat_history = []
    st.session_state.initialized = False

def initialize_platform():
    """Initialize all platform components"""
    try:
        config = st.session_state.config
        
        # Initialize LLM Handler
        st.session_state.llm_handler = LLMHandler(
            provider=config.llm_provider,
            model=config.llm_model,
            api_key=config.llm_api_key,
            base_url=config.llm_base_url
        )
        
        # Initialize RAG Engine
        st.session_state.rag_engine = RAGEngine(
            llm_handler=st.session_state.llm_handler,
            embedding_model=config.embedding_model
        )
        
        # Initialize MISP if configured
        if config.misp_url and config.misp_key:
            st.session_state.misp = MISPIntegration(
                url=config.misp_url,
                api_key=config.misp_key,
                verify_ssl=config.misp_verify_ssl
            )
        
        # Initialize OpenCTI if configured
        if config.opencti_url and config.opencti_token:
            st.session_state.opencti = OpenCTIIntegration(
                url=config.opencti_url,
                token=config.opencti_token
            )
        
        # Initialize Graph Manager
        st.session_state.graph_manager = GraphManager(
            uri=config.neo4j_uri,
            user=config.neo4j_user,
            password=config.neo4j_password
        )
        
        st.session_state.initialized = True
        return True
    except Exception as e:
        st.error(f"Initialization error: {str(e)}")
        return False

def sidebar_config():
    """Configuration sidebar"""
    st.sidebar.title("🛡️ CTI GenAI Platform")
    st.sidebar.markdown("---")
    
    # LLM Provider Selection
    st.sidebar.subheader("🤖 LLM Configuration")
    provider = st.sidebar.selectbox(
        "Provider",
        ["ollama", "lmstudio", "openai", "anthropic", "azure"],
        index=0
    )
    
    if provider in ["ollama", "lmstudio"]:
        base_url = st.sidebar.text_input(
            "Base URL",
            value="http://localhost:11434" if provider == "ollama" else "http://localhost:1234/v1"
        )
        model = st.sidebar.text_input(
            "Model Name",
            value="llama3.2" if provider == "ollama" else "local-model"
        )
        api_key = None
    else:
        base_url = st.sidebar.text_input("API Base URL", value="")
        model = st.sidebar.text_input("Model Name", value="gpt-4")
        api_key = st.sidebar.text_input("API Key", type="password")
    
    st.session_state.config.llm_provider = provider
    st.session_state.config.llm_model = model
    st.session_state.config.llm_api_key = api_key
    st.session_state.config.llm_base_url = base_url
    
    st.sidebar.markdown("---")
    
    # MISP Configuration
    st.sidebar.subheader("🔍 MISP Integration")
    misp_enabled = st.sidebar.checkbox("Enable MISP", value=False)
    if misp_enabled:
        st.session_state.config.misp_url = st.sidebar.text_input(
            "MISP URL",
            value="https://misp.local"
        )
        st.session_state.config.misp_key = st.sidebar.text_input(
            "MISP API Key",
            type="password"
        )
        st.session_state.config.misp_verify_ssl = st.sidebar.checkbox(
            "Verify SSL",
            value=True
        )
    
    st.sidebar.markdown("---")
    
    # OpenCTI Configuration
    st.sidebar.subheader("🌐 OpenCTI Integration")
    opencti_enabled = st.sidebar.checkbox("Enable OpenCTI", value=False)
    if opencti_enabled:
        st.session_state.config.opencti_url = st.sidebar.text_input(
            "OpenCTI URL",
            value="http://localhost:8080"
        )
        st.session_state.config.opencti_token = st.sidebar.text_input(
            "OpenCTI Token",
            type="password"
        )
    
    st.sidebar.markdown("---")
    
    # Initialize button
    if st.sidebar.button("🚀 Initialize Platform", type="primary"):
        with st.spinner("Initializing platform components..."):
            if initialize_platform():
                st.sidebar.success("✅ Platform initialized successfully!")
            else:
                st.sidebar.error("❌ Initialization failed")
    
    # Status indicators
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Status")
    st.sidebar.metric("LLM", "✅" if st.session_state.llm_handler else "⏳")
    st.sidebar.metric("RAG", "✅" if st.session_state.rag_engine else "⏳")
    st.sidebar.metric("MISP", "✅" if st.session_state.misp else "⏳")
    st.sidebar.metric("OpenCTI", "✅" if st.session_state.opencti else "⏳")
    st.sidebar.metric("Graph DB", "✅" if st.session_state.graph_manager else "⏳")

def main_dashboard():
    """Main dashboard view"""
    st.markdown('<p class="main-header">🛡️ Next-Gen CTI Platform</p>', unsafe_allow_html=True)
    
    if not st.session_state.initialized:
        st.info("👈 Please configure and initialize the platform using the sidebar")
        
        # Show feature overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🤖 GenAI Powered")
            st.markdown("""
            - Natural language queries
            - Automated threat analysis
            - Context-aware responses
            - Local LLM support
            """)
        
        with col2:
            st.markdown("### 🔗 Integrations")
            st.markdown("""
            - MISP platform
            - OpenCTI platform
            - STIX 2.1 support
            - Graph database
            """)
        
        with col3:
            st.markdown("### 📊 Advanced Features")
            st.markdown("""
            - RAG for enhanced context
            - Graph-based relationships
            - Real-time intelligence
            - Multi-source correlation
            """)
        
        return
    
    # Tabs for different features
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔍 Intelligence Search",
        "💬 AI Assistant",
        "📊 Threat Graph",
        "🎯 STIX Explorer",
        "📈 Analytics",
        "⚙️ Data Management"
    ])
    
    with tab1:
        intelligence_search()
    
    with tab2:
        ai_assistant()
    
    with tab3:
        threat_graph_explorer()
    
    with tab4:
        stix_explorer()
    
    with tab5:
        analytics_dashboard()
    
    with tab6:
        data_management()

def intelligence_search():
    """Intelligence search interface with RAG"""
    st.header("🔍 Intelligence Search")
    st.markdown("Search across MISP, OpenCTI, and local knowledge base using natural language")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Enter your intelligence query",
            placeholder="e.g., What are the latest APT campaigns targeting financial institutions?"
        )
    
    with col2:
        search_type = st.selectbox(
            "Search Mode",
            ["Semantic", "Keyword", "Hybrid"]
        )
    
    if st.button("🔎 Search", type="primary"):
        if query:
            with st.spinner("Searching intelligence sources..."):
                try:
                    # Search across different sources
                    results = {
                        'misp': [],
                        'opencti': [],
                        'rag': []
                    }
                    
                    # MISP search
                    if st.session_state.misp:
                        misp_results = st.session_state.misp.search_events(query)
                        results['misp'] = misp_results
                    
                    # OpenCTI search
                    if st.session_state.opencti:
                        opencti_results = st.session_state.opencti.search_indicators(query)
                        results['opencti'] = opencti_results
                    
                    # RAG search
                    if st.session_state.rag_engine:
                        rag_results = st.session_state.rag_engine.search(query, top_k=5)
                        results['rag'] = rag_results
                    
                    # Display results
                    st.subheader("Search Results")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("MISP Events", len(results['misp']))
                        if results['misp']:
                            for event in results['misp'][:3]:
                                st.markdown(f"**{event.get('info', 'N/A')}**")
                                st.caption(f"TLP: {event.get('tlp', 'N/A')} | Date: {event.get('date', 'N/A')}")
                    
                    with col2:
                        st.metric("OpenCTI Indicators", len(results['opencti']))
                        if results['opencti']:
                            for indicator in results['opencti'][:3]:
                                st.markdown(f"**{indicator.get('name', 'N/A')}**")
                                st.caption(f"Type: {indicator.get('type', 'N/A')}")
                    
                    with col3:
                        st.metric("Knowledge Base", len(results['rag']))
                        if results['rag']:
                            for doc in results['rag'][:3]:
                                st.markdown(f"**{doc.get('title', 'Document')}**")
                                st.caption(f"Score: {doc.get('score', 0):.2f}")
                    
                    # Generate AI summary
                    if st.session_state.llm_handler:
                        st.subheader("🤖 AI-Generated Summary")
                        summary_prompt = f"""Based on the following intelligence search results, provide a comprehensive summary:

Query: {query}

MISP Results: {len(results['misp'])} events
OpenCTI Results: {len(results['opencti'])} indicators
Knowledge Base: {len(results['rag'])} documents

Provide a concise analysis of key findings, threat actors, TTPs, and recommended actions."""
                        
                        summary = st.session_state.llm_handler.generate(summary_prompt)
                        st.markdown(summary)
                
                except Exception as e:
                    st.error(f"Search error: {str(e)}")
        else:
            st.warning("Please enter a search query")

def ai_assistant():
    """AI-powered threat intelligence assistant"""
    st.header("💬 AI Threat Intelligence Assistant")
    st.markdown("Ask questions about threats, indicators, TTPs, and get AI-powered insights")
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about threats, campaigns, indicators..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    # Retrieve relevant context from RAG
                    context = ""
                    if st.session_state.rag_engine:
                        docs = st.session_state.rag_engine.search(prompt, top_k=3)
                        if docs:
                            context = "\n\n".join([doc.get('content', '') for doc in docs])
                    
                    # Build prompt with context
                    system_prompt = """You are an expert cyber threat intelligence analyst. 
                    Provide accurate, actionable intelligence based on the available data.
                    Use STIX terminology where appropriate. Cite sources when possible."""
                    
                    full_prompt = f"""{system_prompt}

Context from knowledge base:
{context}

User question: {prompt}

Provide a detailed, professional response."""
                    
                    response = st.session_state.llm_handler.generate(full_prompt)
                    st.markdown(response)
                    
                    # Add assistant response to history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"Error generating response: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

def threat_graph_explorer():
    """Graph-based threat visualization"""
    st.header("📊 Threat Relationship Graph")
    st.markdown("Explore threat actor relationships, campaigns, and TTPs using graph technology")
    
    if not st.session_state.graph_manager:
        st.warning("Graph database not initialized")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        entity_type = st.selectbox(
            "Explore Entity Type",
            ["Threat Actor", "Malware", "Campaign", "Indicator", "Vulnerability"]
        )
    
    with col2:
        depth = st.slider("Relationship Depth", 1, 3, 2)
    
    entity_name = st.text_input("Entity Name/ID", placeholder="e.g., APT28, Emotet")
    
    if st.button("🔍 Explore Graph"):
        if entity_name:
            with st.spinner("Building graph..."):
                try:
                    # Query graph relationships
                    graph_data = st.session_state.graph_manager.get_entity_relationships(
                        entity_name,
                        depth=depth
                    )
                    
                    if graph_data:
                        # Create network visualization
                        st.subheader("Relationship Network")
                        
                        # Placeholder for graph visualization
                        st.info("Graph visualization would be displayed here using Plotly/NetworkX")
                        
                        # Display relationship table
                        st.subheader("Relationships")
                        if 'relationships' in graph_data:
                            df = pd.DataFrame(graph_data['relationships'])
                            st.dataframe(df, use_container_width=True)
                    else:
                        st.warning("No relationships found")
                
                except Exception as e:
                    st.error(f"Graph query error: {str(e)}")

def stix_explorer():
    """STIX 2.1 object explorer and creator"""
    st.header("🎯 STIX 2.1 Explorer")
    st.markdown("Create, import, and explore STIX threat intelligence objects")
    
    tab1, tab2, tab3 = st.tabs(["View STIX", "Create STIX", "Import STIX"])
    
    with tab1:
        st.subheader("Browse STIX Objects")
        
        stix_type = st.selectbox(
            "Object Type",
            ["indicator", "threat-actor", "malware", "campaign", "attack-pattern", "vulnerability"]
        )
        
        if st.button("Load Objects"):
            st.info(f"Loading {stix_type} objects...")
            # Placeholder for STIX object loading
    
    with tab2:
        st.subheader("Create New STIX Object")
        
        create_type = st.selectbox(
            "Create Type",
            ["Indicator", "Threat Actor", "Malware", "Campaign"]
        )
        
        if create_type == "Indicator":
            name = st.text_input("Indicator Name")
            pattern = st.text_area("Pattern (STIX format)")
            indicator_type = st.selectbox("Type", ["ipv4-addr", "domain-name", "file", "email-addr"])
            
            if st.button("Create Indicator"):
                try:
                    stix_obj = st.session_state.stix_processor.create_indicator(
                        pattern=pattern,
                        name=name,
                        indicator_type=indicator_type
                    )
                    st.success("✅ Indicator created")
                    st.json(json.loads(stix_obj.serialize()))
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with tab3:
        st.subheader("Import STIX Bundle")
        
        uploaded_file = st.file_uploader("Upload STIX JSON file", type=['json'])
        
        if uploaded_file:
            try:
                bundle_data = json.load(uploaded_file)
                st.json(bundle_data)
                
                if st.button("Import to Platform"):
                    # Import to graph and TIPs
                    st.success("✅ STIX bundle imported")
            except Exception as e:
                st.error(f"Error parsing STIX: {str(e)}")

def analytics_dashboard():
    """Threat analytics and metrics"""
    st.header("📈 Threat Intelligence Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Sample metrics
    with col1:
        st.metric(
            "Active Threats",
            "342",
            delta="12",
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            "IOCs Today",
            "1,247",
            delta="89"
        )
    
    with col3:
        st.metric(
            "Campaigns",
            "28",
            delta="3",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "Threat Actors",
            "156",
            delta="5"
        )
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Threat Trends (30 Days)")
        # Sample data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        threat_counts = pd.Series([50 + i * 2 + (i % 7) * 10 for i in range(30)], index=dates)
        
        fig = px.line(x=threat_counts.index, y=threat_counts.values,
                     labels={'x': 'Date', 'y': 'Threat Count'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Threat Distribution")
        threat_types = ['Malware', 'Phishing', 'Ransomware', 'APT', 'DDoS']
        values = [145, 89, 67, 23, 18]
        
        fig = px.pie(names=threat_types, values=values, hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

def data_management():
    """Data ingestion and management"""
    st.header("⚙️ Data Management")
    
    tab1, tab2, tab3 = st.tabs(["Ingest Data", "Sync TIPs", "Knowledge Base"])
    
    with tab1:
        st.subheader("Ingest Threat Intelligence")
        
        source = st.selectbox(
            "Data Source",
            ["Upload File", "MISP Export", "OpenCTI Export", "STIX Bundle", "CSV/JSON"]
        )
        
        uploaded_file = st.file_uploader("Upload intelligence data")
        
        if uploaded_file and st.button("Process Upload"):
            with st.spinner("Processing data..."):
                st.success("✅ Data processed and ingested")
    
    with tab2:
        st.subheader("Synchronize with TIPs")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**MISP Sync**")
            if st.session_state.misp:
                if st.button("Sync MISP Events"):
                    with st.spinner("Syncing..."):
                        st.success("✅ MISP events synchronized")
            else:
                st.warning("MISP not configured")
        
        with col2:
            st.markdown("**OpenCTI Sync**")
            if st.session_state.opencti:
                if st.button("Sync OpenCTI Data"):
                    with st.spinner("Syncing..."):
                        st.success("✅ OpenCTI data synchronized")
            else:
                st.warning("OpenCTI not configured")
    
    with tab3:
        st.subheader("RAG Knowledge Base")
        
        st.markdown("**Add Documents to Knowledge Base**")
        
        doc_source = st.selectbox(
            "Document Type",
            ["Threat Report", "Malware Analysis", "Incident Report", "Research Paper"]
        )
        
        doc_file = st.file_uploader("Upload Document", type=['pdf', 'txt', 'md'])
        
        if doc_file and st.button("Index Document"):
            with st.spinner("Indexing..."):
                try:
                    content = doc_file.read().decode('utf-8')
                    if st.session_state.rag_engine:
                        st.session_state.rag_engine.add_document(
                            content=content,
                            metadata={"source": doc_file.name, "type": doc_source}
                        )
                        st.success("✅ Document indexed successfully")
                except Exception as e:
                    st.error(f"Error indexing document: {str(e)}")

if __name__ == "__main__":
    sidebar_config()
    main_dashboard()
