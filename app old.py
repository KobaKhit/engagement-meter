import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np

# Page configuration
st.set_page_config(
    page_title="NBA Reddit AMA Analysis",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 1rem 1rem;
    }
    .stTitle {
        font-size: 3rem !important;
        padding-bottom: 2rem;
    }
    .plot-container {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Data loading and preprocessing
@st.cache_data
def load_and_process_data():
    df = pd.read_csv('nba-ama.csv')
    
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Handle outliers
    def remove_outliers(df, column):
        Q1 = df[column].quantile(0.05)
        Q3 = df[column].quantile(0.95)
        IQR = Q3 - Q1
        df_filtered = df[
            (df[column] >= Q1 - 1.5 * IQR) & 
            (df[column] <= Q3 + 1.5 * IQR)
        ]
        return df_filtered
    
    df_clean = df.copy()
    df_clean = remove_outliers(df_clean, 'num_comments')
    df_clean = remove_outliers(df_clean, 'score')
    
    return df, df_clean

# Load data
df_raw, df_clean = load_and_process_data()

# Sidebar
with st.sidebar:
    st.title("📊 Analysis Options")
    show_raw_data = st.checkbox('Show Raw Data Sample')
    include_outliers = st.checkbox('Include Outliers in Analysis', value=False)
    
    # Date range filter
    st.subheader("Date Range Filter")
    min_date = df_raw['date'].min().date()
    max_date = df_raw['date'].max().date()
    
    start_date = st.date_input(
        "Start Date",
        value=min_date,
        min_value=min_date,
        max_value=max_date
    )
    
    end_date = st.date_input(
        "End Date",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )

# Main content
st.title("🏀 Reddit r/NBA AMA Analysis")

# Data selection based on user preferences
df = df_raw if include_outliers else df_clean
df = df[
    (df['date'].dt.date >= start_date) &
    (df['date'].dt.date <= end_date)
]

# Raw data display
if show_raw_data:
    st.subheader("Raw Data Sample")
    st.dataframe(
        df[['title', 'name', 'category', 'num_comments', 'score', 'date']]
        .head(10)
        .style.highlight_max(axis=0, subset=['num_comments', 'score'])
    )

# Key metrics
st.subheader("📈 Key Metrics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total AMAs", len(df))
with col2:
    st.metric("Average Comments", int(df['num_comments'].mean()))
with col3:
    st.metric("Average Score", int(df['score'].mean()))
with col4:
    st.metric("Unique Categories", df['category'].nunique())

# Scatter plot
st.subheader("Comments vs Upvotes Analysis")
scatter_fig = px.scatter(
    df,
    x='num_comments',
    y='score',
    color='category',
    size='num_comments',
    hover_data=['title', 'name', 'date'],
    title='Number of Comments vs Upvotes',
    log_x=True,
    log_y=True,
    template='plotly_white'
)
scatter_fig.update_layout(
    height=600,
    showlegend=True,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    )
)
st.plotly_chart(scatter_fig, use_container_width=True)

# Category analysis
st.subheader("Category Analysis")
col1, col2 = st.columns(2)

with col1:
    comments_box = px.box(
        df,
        x='category',
        y='num_comments',
        title='Comments Distribution by Category',
        points="outliers"
    )
    comments_box.update_layout(height=500)
    st.plotly_chart(comments_box, use_container_width=True)

with col2:
    score_box = px.box(
        df,
        x='category',
        y='score',
        title='Score Distribution by Category',
        points="outliers"
    )
    score_box.update_layout(height=500)
    st.plotly_chart(score_box, use_container_width=True)

# Timeline analysis
st.subheader("Timeline Analysis")
timeline_fig = px.scatter(
    df,
    x='date',
    y='score',
    color='category',
    size='num_comments',
    hover_data=['title', 'name'],
    title='AMA Performance Over Time'
)
timeline_fig.update_layout(height=500)
st.plotly_chart(timeline_fig, use_container_width=True)

# Top contributors analysis
st.subheader("Top Contributors Analysis")
top_contributors = df.groupby('name').agg({
    'num_comments': ['count', 'mean'],
    'score': 'mean'
}).round(2)

top_contributors.columns = ['Number of AMAs', 'Avg Comments', 'Avg Score']
top_contributors = top_contributors.sort_values('Number of AMAs', ascending=False)
top_contributors = top_contributors.head(10)

fig_contributors = px.bar(
    top_contributors.reset_index(),
    x='name',
    y='Number of AMAs',
    title='Top 10 AMA Contributors',
    text='Number of AMAs'
)
fig_contributors.update_layout(
    height=500,
    xaxis_tickangle=-45
)
st.plotly_chart(fig_contributors, use_container_width=True)

# Detailed contributor stats
st.subheader("Top Contributors Statistics")
st.dataframe(
    top_contributors
    .style.background_gradient(cmap='YlOrRd', subset=['Number of AMAs'])
    .bar(subset=['Avg Comments', 'Avg Score'], color='#90CAF9')
)

# Category distribution
st.subheader("Category Distribution")
category_dist = px.pie(
    df,
    names='category',
    title='Distribution of AMA Categories',
    hole=0.4
)
category_dist.update_layout(height=500)
st.plotly_chart(category_dist, use_container_width=True)