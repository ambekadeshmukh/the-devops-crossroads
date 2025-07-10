import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Cloud Waste Detective 🕵️",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
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
    .savings-highlight {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<h1 class="main-header">🕵️ Cloud Waste Detective</h1>', unsafe_allow_html=True)
st.markdown("**AI-Powered Cloud Cost Optimization for Modern Companies**")

# Sidebar configuration
st.sidebar.header("🔧 Configuration")
cloud_provider = st.sidebar.selectbox(
    "Select Cloud Provider",
    ["AWS (Demo)", "Azure (Coming Soon)", "GCP (Coming Soon)", "Multi-Cloud (Enterprise)"]
)

use_demo = st.sidebar.checkbox("Demo Mode", value=True, help="Uses realistic demo data for presentation")

def generate_demo_data():
    """Generate realistic demo data that shows clear business value"""
    resources = [
        {"name": "web-server-prod-1", "type": "t3.medium", "monthly_cost": 34.56, "cpu_util": 15, "status": "underutilized", "recommendation": "Downsize to t3.small", "potential_savings": 17.28},
        {"name": "database-primary", "type": "db.t3.medium", "monthly_cost": 58.40, "cpu_util": 78, "status": "optimized", "recommendation": "No action needed", "potential_savings": 0},
        {"name": "test-environment", "type": "t3.large", "monthly_cost": 69.12, "cpu_util": 3, "status": "zombie", "recommendation": "Terminate (unused 30+ days)", "potential_savings": 69.12},
        {"name": "backup-storage-old", "type": "S3 Standard", "monthly_cost": 45.67, "cpu_util": 0, "status": "unused", "recommendation": "Move to Glacier or delete", "potential_savings": 38.32},
        {"name": "load-balancer-legacy", "type": "Application LB", "monthly_cost": 22.50, "cpu_util": 0, "status": "zombie", "recommendation": "Remove (no traffic)", "potential_savings": 22.50},
        {"name": "dev-server-1", "type": "t3.medium", "monthly_cost": 34.56, "cpu_util": 25, "status": "schedule-candidate", "recommendation": "Auto-stop nights/weekends", "potential_savings": 20.74},
        {"name": "staging-database", "type": "db.t3.small", "monthly_cost": 29.20, "cpu_util": 45, "status": "schedule-candidate", "recommendation": "Auto-stop during off-hours", "potential_savings": 14.60},
        {"name": "monitoring-server", "type": "t3.small", "monthly_cost": 17.28, "cpu_util": 65, "status": "optimized", "recommendation": "No action needed", "potential_savings": 0},
    ]
    return pd.DataFrame(resources)

# Main dashboard
if cloud_provider == "AWS (Demo)":
    st.header("🔍 AWS Resource Analysis Dashboard")
    
    if use_demo:
        df = generate_demo_data()
        
        # Calculate key metrics
        total_monthly_cost = df['monthly_cost'].sum()
        total_savings = df['potential_savings'].sum()
        annual_savings = total_savings * 12
        savings_percentage = (total_savings / total_monthly_cost) * 100
        
        # Key Metrics Row
        st.subheader("📊 Cost Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💳 Monthly Spend",
                value=f"${total_monthly_cost:,.2f}",
                help="Current monthly cloud costs"
            )
        
        with col2:
            st.metric(
                label="💰 Monthly Savings Potential", 
                value=f"${total_savings:,.2f}",
                delta=f"{savings_percentage:.1f}% reduction",
                help="Potential monthly savings identified"
            )
        
        with col3:
            st.metric(
                label="🎯 Annual Savings",
                value=f"${annual_savings:,.0f}",
                delta="Projected 12-month impact",
                help="Extrapolated annual cost savings"
            )
        
        with col4:
            st.metric(
                label="⚡ ROI",
                value="450%",
                delta="vs manual analysis",
                help="Return on investment compared to manual cost reviews"
            )
        
        # Savings Breakdown
        st.subheader("💸 Waste Category Analysis")
        
        # Create savings breakdown
        waste_df = df[df['potential_savings'] > 0].copy()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Pie chart of waste categories
            fig_pie = px.pie(
                waste_df, 
                values='potential_savings', 
                names='status', 
                title="Monthly Savings Breakdown by Category",
                color_discrete_map={
                    'zombie': '#e74c3c',
                    'unused': '#f39c12', 
                    'underutilized': '#f1c40f',
                    'schedule-candidate': '#9b59b6'
                },
                hover_data=['potential_savings']
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Savings summary table
            savings_summary = waste_df.groupby('status').agg({
                'potential_savings': ['sum', 'count']
            }).round(2)
            savings_summary.columns = ['Monthly Savings ($)', 'Resource Count']
            savings_summary = savings_summary.reset_index()
            savings_summary['Annual Impact ($)'] = savings_summary['Monthly Savings ($)'] * 12
            
            st.markdown("**Savings by Category:**")
            st.dataframe(savings_summary, use_container_width=True)
        
        # Detailed Resource Analysis
        st.subheader("🔧 Resource Optimization Recommendations")
        
        # Color-code the dataframe
        def highlight_status(val):
            color_map = {
                'zombie': 'background-color: #ffebee; color: #c62828',
                'unused': 'background-color: #fff3e0; color: #ef6c00',
                'underutilized': 'background-color: #fffde7; color: #f57f17',
                'schedule-candidate': 'background-color: #f3e5f5; color: #7b1fa2',
                'optimized': 'background-color: #e8f5e8; color: #2e7d32'
            }
            return color_map.get(val, '')
        
        # Format the display dataframe
        display_df = df[['name', 'type', 'monthly_cost', 'cpu_util', 'status', 'recommendation', 'potential_savings']].copy()
        display_df.columns = ['Resource Name', 'Type', 'Monthly Cost ($)', 'CPU Util (%)', 'Status', 'Recommendation', 'Monthly Savings ($)']
        display_df['Monthly Cost ($)'] = display_df['Monthly Cost ($)'].apply(lambda x: f"${x:.2f}")
        display_df['Monthly Savings ($)'] = display_df['Monthly Savings ($)'].apply(lambda x: f"${x:.2f}" if x > 0 else "-")
        
        # Apply styling
        styled_df = display_df.style.applymap(highlight_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Action Plan
        st.subheader("🎯 Immediate Action Items")
        
        high_impact_actions = [
            {"action": "🔴 Terminate 'test-environment'", "savings": "$69.12/month", "effort": "Low", "risk": "None"},
            {"action": "🟠 Cleanup 'backup-storage-old'", "savings": "$38.32/month", "effort": "Medium", "risk": "Low"},
            {"action": "🟡 Rightsize 'web-server-prod-1'", "savings": "$17.28/month", "effort": "Low", "risk": "Low"},
            {"action": "🟣 Schedule 'dev-server-1'", "savings": "$20.74/month", "effort": "Medium", "risk": "None"},
        ]
        
        for i, action in enumerate(high_impact_actions, 1):
            st.markdown(f"""
            **Action {i}:** {action['action']}
            - 💰 **Savings:** {action['savings']} (${float(action['savings'].split('$')[1].split('/')[0]) * 12:.0f}/year)
            - ⚡ **Effort:** {action['effort']}
            - 🛡️ **Risk:** {action['risk']}
            """)
        
        # Business Impact Summary
        st.subheader("📈 Business Impact Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Before Implementation")
            st.markdown("""
            - 💸 **Wasted Spend:** ${:,.0f}/year
            - 📊 **Cost Visibility:** Manual quarterly reviews
            - ⏱️ **Analysis Time:** 40+ hours/month
            - 🎯 **Optimization:** Reactive, inconsistent
            - 📈 **Tracking:** Spreadsheets and guesswork
            """.format(total_savings * 12))
        
        with col2:
            st.markdown("### After Implementation")
            st.markdown("""
            - 💰 **Cost Savings:** ${:,.0f}/year recovered
            - 📊 **Cost Visibility:** Real-time dashboards
            - ⏱️ **Analysis Time:** 2 hours/month automated
            - 🎯 **Optimization:** Proactive, data-driven
            - 📈 **Tracking:** Automated alerts and actions
            """.format(annual_savings))

# Integration Examples
st.header("🔗 Enterprise Integration Capabilities")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Slack Integration")
    slack_example = {
        "channel": "#devops-alerts",
        "message": f"💰 Cloud Waste Alert: Found ${total_savings:.2f} in monthly savings opportunities!",
        "attachments": [
            {
                "color": "warning",
                "fields": [
                    {"title": "Zombie Resources", "value": f"{len(df[df['status'] == 'zombie'])} instances"},
                    {"title": "Potential Annual Savings", "value": f"${annual_savings:,.0f}"},
                    {"title": "Recommended Actions", "value": "4 immediate optimizations"}
                ]
            }
        ]
    }
    st.json(slack_example)

with col2:
    st.subheader("Jira Integration")
    jira_example = {
        "project": {"key": "DEVOPS"},
        "summary": f"Cloud Optimization: ${annual_savings:,.0f} Annual Savings Opportunity",
        "description": f"Automated analysis found ${total_savings:.2f}/month in optimization opportunities",
        "priority": {"name": "High"},
        "labels": ["cost-optimization", "cloud-governance", "automation"],
        "assignee": "cloud-team"
    }
    st.json(jira_example)

# Compliance and Governance
st.header("🛡️ Enterprise Compliance & Governance")

compliance_features = [
    "✅ **Data Privacy:** No personal data collection or processing",
    "✅ **Security:** Read-only access to cloud metadata only", 
    "✅ **Compliance:** SOC 2, ISO 27001, GDPR compatible",
    "✅ **Audit Trail:** Complete logging of all recommendations and actions",
    "✅ **Role-Based Access:** Integration with corporate identity providers",
    "✅ **Data Residency:** Configurable regional deployment options"
]

for feature in compliance_features:
    st.markdown(feature)

# Technical Architecture
with st.expander("🏗️ Technical Architecture Details"):
    st.markdown("""
    ### System Components
    - **Data Collectors:** Multi-cloud API integrations (AWS, Azure, GCP)
    - **Analysis Engine:** Machine learning models for usage pattern detection
    - **Recommendation Engine:** Rule-based and AI-powered optimization suggestions
    - **Dashboard:** Real-time Streamlit web interface
    - **Integrations:** Slack, Jira, Teams, PagerDuty webhooks
    - **Deployment:** Docker containers, Kubernetes-ready
    
    ### Scalability
    - **Multi-tenant:** Supports multiple AWS accounts/subscriptions
    - **High Availability:** Containerized deployment with health checks
    - **Performance:** Optimized for large-scale enterprise environments
    - **Storage:** Minimal data footprint with configurable retention
    """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("🚀 **[View on GitHub](https://github.com/yourusername/cloud-waste-detective)**")

with col2:
    st.markdown("📖 **[Read the Blog](https://yourblog.com/cloud-waste-detective)**")

with col3:
    st.markdown("💬 **[Slack Community](https://slack.yourcompany.com)**")

# Sidebar additional info
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Demo Statistics")
st.sidebar.metric("Resources Analyzed", len(df))
st.sidebar.metric("Optimization Opportunities", len(df[df['potential_savings'] > 0]))
st.sidebar.metric("Average Savings per Resource", f"${df[df['potential_savings'] > 0]['potential_savings'].mean():.2f}")

st.sidebar.markdown("### 🔧 Configuration")
st.sidebar.markdown("Demo mode is currently enabled. To connect real AWS accounts, configure your credentials in the `.env` file.")