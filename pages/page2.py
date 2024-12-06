import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_extras.stylable_container import stylable_container


st.title('Organic Tracker')

# Read data from jsonl file
df = pd.read_json('https://storage.googleapis.com/social-data-public/sports_reddit_posts.jsonl', lines=True)

# Add author filter
authors = sorted(df['author'].unique())
selected_author = st.selectbox('Select Author', authors, index=authors.index('nba'))

subreddit_mapping = {
    'nba': 'nba',
    'nfl': 'nfl', 
    'nhl': 'hockey',
    'MLBOfficial': 'baseball'
}
df = df[(df['subreddit'] == subreddit_mapping.get(selected_author, 'nba')) & 
        (df['author'] == selected_author)]

# Data preprocessing
df['created_utc'] = pd.to_datetime(df['created_utc'], unit='s').dt.tz_localize('UTC').dt.tz_convert('US/Eastern')
df['week'] = df['created_utc'].dt.isocalendar().week
df['week_date'] = df['created_utc'].dt.to_period('W-SUN').apply(lambda x: x.start_time.strftime('%Y-%m-%d'))
df['week_end_date'] = df['created_utc'].dt.to_period('W-SUN').apply(lambda x: x.end_time.strftime('%Y-%m-%d'))
df['year'] = df['created_utc'].dt.year

# Page header with styling
with stylable_container(
            key="header_container",
            css_styles="""
                    {
                    background-color: #1e41e8;
                    color: white !important;
                    border-radius: 10px;
                    padding: 15px
                    }
                """,
        ):
    st.markdown(f"""
        This page tracks organic engagement metrics for posts in the r/{subreddit_mapping.get(selected_author, 'NBA')} subreddit by the u/{selected_author.upper()} account over time.
        It provides insights into community activity patterns and popular discussion topics.
    """)

# Overview metrics
metric_cols = st.columns(4)
with metric_cols[0]:
    st.metric("Total Posts", len(df))
with metric_cols[1]:
    st.metric("Avg Comments/Post", int(df['num_comments'].mean()))
with metric_cols[2]:
    st.metric("Avg Score/Post", int(df['score'].mean()))
with metric_cols[3]:
    st.markdown('Date Range')
    st.markdown(f"{df['created_utc'].dt.date.min()} to {df['created_utc'].dt.date.max()}")

# Weekly engagement metrics table
st.subheader("Weekly Engagement Metrics")
weekly_metrics = df.groupby(['week_date', 'week_end_date']).agg({
    'num_comments': ['count', 'mean', 'sum'],
    'score': ['mean', 'sum']
}).round(1)

weekly_metrics.columns = ['Post Count', 'Avg Comments', 'Total Comments',
                         'Avg Score', 'Total Score']
weekly_metrics = weekly_metrics.reset_index()

# Format week date
# weekly_metrics['week_date'] = pd.to_datetime(weekly_metrics['week_date'])
weekly_metrics = weekly_metrics.sort_values('week_date', ascending=False)

st.dataframe(weekly_metrics, use_container_width=True)
# Engagement trends visualization
st.subheader("Engagement Trends")

# Add year selector
years = sorted(df['year'].unique())
c1,_ = st.columns([1,2])
with c1:
    selected_years = st.multiselect('Select Years', years, default=[2024])

# Filter data by selected years
filtered_metrics = weekly_metrics[weekly_metrics['week_date'].str[:4].isin([str(year) for year in selected_years])]

col1, col2 = st.columns(2)
with col1:
    # Create figure with secondary y-axis
    comments_fig = px.line(filtered_metrics, 
                          x='week_date',
                          y='Avg Score',
                          title='Average Engagement per Post by Week',
                          template='plotly_white')
    
    # Add second trace on secondary y-axis
    comments_fig.add_scatter(x=filtered_metrics['week_date'],
                           y=filtered_metrics['Avg Comments'],
                           name='Avg Comments',
                           yaxis='y2')
    
    # Update layout for secondary axis
    comments_fig.update_layout(
        height=400,
        yaxis2=dict(
            title='Avg Comments',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        yaxis=dict(showgrid=False),
        xaxis=dict(showgrid=False,title='Week'),
        yaxis_title='Avg Score',
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    st.plotly_chart(comments_fig, use_container_width=True)

with col2:
    volume_fig = px.line(filtered_metrics,
                        x='week_date',
                        y='Post Count',
                        title='Post Volume by Week',
                        template='plotly_white')
    volume_fig.update_layout(
        height=400,
        yaxis=dict(showgrid=False),
        xaxis=dict(showgrid=False,title='Week')
    )
    st.plotly_chart(volume_fig, use_container_width=True)
