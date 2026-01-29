import pandas as pd
import streamlit as st
import plotly.express as px


st.title('Comparative Analysis')

# Read data from jsonl file
df = pd.read_json('https://storage.googleapis.com/social-data-public/sports_reddit_posts.jsonl', lines=True)


# Data preprocessing
df['created_utc'] = pd.to_datetime(df['created_utc'], unit='s').dt.tz_localize('UTC').dt.tz_convert('US/Eastern')
df['month'] = df['created_utc'].dt.to_period('M')

# Page header with styling
css_style = """
    background-color: #1e41e8;
    color: white !important;
    border-radius: 10px;
    padding: 10px 5px;
"""
st.html(f"""
<style>
    .st-header_container-container {{{css_style}}}
</style>
""")
with st.container(key='header_container'):
    st.markdown("""
        This page tracks posting patterns and engagement metrics across different sports subreddits for four major spotrs acconuts NBA, NFL, NHL, MLBOfficial.
        Compare how different authors perform across communities and identify top performers.
    """)

# Overview metrics
total_authors = df['author'].nunique()
total_posts = len(df)
avg_engagement = df['score'].mean()

metric_cols = st.columns(4)
with metric_cols[0]:
    st.metric("Total Authors", total_authors)
with metric_cols[1]:
    st.metric("Total Posts", total_posts)
with metric_cols[2]:
    st.metric("Avg Score/Post", int(avg_engagement))
with metric_cols[3]:
    st.markdown('Date Range')
    st.markdown(f"{df['created_utc'].dt.date.min()} to {df['created_utc'].dt.date.max()}")

with st.popover('Data', width='stretch'):
    st.write(df)

# Author Performance Analysis
st.subheader("Top Authors by Subreddit")

# Calculate author metrics by subreddit
author_metrics = df.groupby(['subreddit', 'author']).agg({
    'score': ['count', 'mean', 'sum'],
    'num_comments': ['mean', 'sum']
}).round(1)

author_metrics.columns = ['Post Count', 'Avg Score', 'Total Score', 
                         'Avg Comments', 'Total Comments']
author_metrics = author_metrics.reset_index()
# Show top authors table
top_authors = author_metrics.sort_values('Total Score', ascending=False)
st.dataframe(top_authors, width='stretch', hide_index=True)
# Visualization section
st.subheader("Engagement Analysis")

# Add log scale toggle
c1, c2 = st.columns([2,3])
with c1:
    log_scale = False

col1, col2 = st.columns(2)
with col1:
    # Create stacked bar chart for posts by author and subreddit
    author_subreddit_posts = df.groupby(['author', 'subreddit']).size().reset_index(name='post_count')
    
    # Get top 10 subreddits by total post count
    top_10_subreddits = df.groupby('subreddit').size().nlargest(10).index
    
    # Filter for only top 10 subreddits
    author_subreddit_posts = author_subreddit_posts[author_subreddit_posts['subreddit'].isin(top_10_subreddits)]
    # Sort by post count within each author
    author_subreddit_posts = author_subreddit_posts.sort_values(['author', 'post_count'], ascending=[True, False])
    
    # Get unique authors for color mapping
    unique_authors = pd.concat([
        author_subreddit_posts['author'],
        author_metrics['author']
    ]).unique()
    
    # Create consistent color mapping
    color_sequence = px.colors.qualitative.Plotly
    author_colors = {author: color_sequence[i % len(color_sequence)] 
                    for i, author in enumerate(unique_authors)}
    
    bar_fig = px.bar(
        author_subreddit_posts,
        x='subreddit',
        y='post_count',
        color='author',
        title='Posts by Subreddit',
        template='plotly_white',
        color_discrete_map=author_colors
    )
    
    bar_fig.update_layout(
        height=400,
        xaxis_title="Author",
        yaxis_title="Number of Posts",
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )
    
    st.plotly_chart(bar_fig, width='stretch')

with col2:
    top_10_subreddits = df.groupby('subreddit').size().nlargest(10).index
    author_metrics = author_metrics[author_metrics['subreddit'].isin(['nfl','nba','hockey','baseball'])]
    scatter_fig = px.scatter(
        author_metrics,
        x='Avg Score',
        y='Avg Comments', 
        size='Post Count',
        color='author',
        hover_name='author',
        title='Author Engagement',
        template='plotly_white',
        log_x=log_scale,
        log_y=log_scale,
        color_discrete_map=author_colors
    )
    
    scatter_fig.update_layout(
        height=400,
        xaxis_title="Average Score per Post",
        yaxis_title="Average Comments per Post",
        showlegend=True,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )
    
    st.plotly_chart(scatter_fig, width='stretch')



# Posting frequency analysis
st.subheader("Posting Patterns Over Time")

# Calculate monthly post counts by subreddit
monthly_posts = df.groupby(['month', 'author']).size().reset_index(name='posts')
monthly_posts['month'] = monthly_posts['month'].astype(str)

# Create line chart
line_fig = px.line(
    monthly_posts,
    x='month',
    y='posts',
    color='author',
    title='Monthly Posting Activity by Author',
    template='plotly_white',
    color_discrete_map=author_colors
)

line_fig.update_layout(
    height=400,
    xaxis_title="Month",
    yaxis_title="Number of Posts",
    showlegend=True
)

st.plotly_chart(line_fig, width='stretch')
