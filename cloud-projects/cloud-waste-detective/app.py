import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

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
st.markdown("**AI-Powered Cloud Cost Optimization Platform**")
st.markdown("---")

# Sidebar
st.sidebar.header("🔧 Configuration")
cloud_provider = st.sidebar.selectbox(
    "Select Cloud Provider",
    ["AWS (Demo)", "Azure (Coming Soon)", "GCP (Coming Soon)", "Multi-Cloud"]
)

def generate_demo_data():
    """Generate realistic demo data showing clear business value"""
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
st.header("🔍 AWS Resource Analysis Dashboard")

df = generate_demo_data()

# Calculate key metrics
total_monthly_cost = df['monthly_cost'].sum()
total_savings = df['potential_savings'].sum()
annual_savings = total_savings * 12
savings_percentage = (total_savings / total_monthly_cost) * 100

# Key Metrics Row
st.subheader("📊 Executive Summary")
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
        help="Return on investment"
    )

# Highlight the key finding
st.markdown(f"""
<div class="savings-highlight">
<h3>💡 Key Finding</h3>
<p><strong>Your infrastructure could save ${annual_savings:,.0f} annually</strong> through automated optimization. 
This represents a {savings_percentage:.1f}% reduction in cloud costs with minimal risk.</p>
</div>
""", unsafe_allow_html=True)

# Savings Breakdown
st.subheader("💸 Waste Category Analysis")

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
        }
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    # Savings summary
    savings_summary = waste_df.groupby('status').agg({
        'potential_savings': ['sum', 'count']
    }).round(2)
    savings_summary.columns = ['Monthly ($)', 'Count']
    savings_summary = savings_summary.reset_index()
    savings_summary['Annual ($)'] = savings_summary['Monthly ($)'] * 12
    
    st.markdown("**Optimization Opportunities:**")
    st.dataframe(savings_summary, use_container_width=True)

# Detailed recommendations
st.subheader("🔧 Specific Recommendations")

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

# Format display
display_df = df[['name', 'type', 'monthly_cost', 'cpu_util', 'status', 'recommendation', 'potential_savings']].copy()
display_df.columns = ['Resource', 'Type', 'Monthly Cost ($)', 'CPU %', 'Status', 'Recommendation', 'Monthly Savings ($)']
display_df['Monthly Cost ($)'] = display_df['Monthly Cost ($)'].apply(lambda x: f"${x:.2f}")
display_df['Monthly Savings ($)'] = display_df['Monthly Savings ($)'].apply(lambda x: f"${x:.2f}" if x > 0 else "-")

styled_df = display_df.style.applymap(highlight_status, subset=['Status'])
st.dataframe(styled_df, use_container_width=True)

# Action items
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

# Business impact
st.subheader("📈 Business Impact")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Before Optimization")
    st.markdown(f"""
    - 💸 **Wasted Spend:** ${total_savings * 12:,.0f}/year
    - 📊 **Visibility:** Manual quarterly reviews
    - ⏱️ **Analysis Time:** 40+ hours/month
    - 🎯 **Actions:** Reactive, inconsistent
    """)

with col2:
    st.markdown("### After Implementation")
    st.markdown(f"""
    - 💰 **Recovered Costs:** ${annual_savings:,.0f}/year
    - 📊 **Visibility:** Real-time dashboards
    - ⏱️ **Analysis Time:** 2 hours/month
    - 🎯 **Actions:** Proactive, automated
    """)

# Footer
st.markdown("---")
st.markdown("### 🚀 About This Demo")
st.markdown("""
This is a demonstration of an AI-powered Cloud Waste Detective platform. The data shown represents realistic scenarios 
commonly found in enterprise cloud environments. 

**Key Features:**
- ✅ Multi-cloud resource discovery and analysis
- ✅ Machine learning-powered waste classification  
- ✅ Executive dashboards with ROI calculations
- ✅ Integration with Slack, Jira, and enterprise tools
- ✅ GDPR/SOC2 compliant data handling

**Built with:** Python, Streamlit, Plotly, pandas
""")

col1, col2 = st.columns(2)
with col1:
    st.markdown("🔗 **[View on GitHub](https://github.com/ambekadeshmukh/the-devops-crossroads)**")
with col2:
    st.markdown("📧 **Contact:** ambekadeshmukh@gmail.com")

# Sidebar metrics
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Demo Statistics")
st.sidebar.metric("Resources Analyzed", len(df))
st.sidebar.metric("Waste Opportunities", len(df[df['potential_savings'] > 0]))
st.sidebar.metric("Total Annual Savings", f"${annual_savings:,.0f}")