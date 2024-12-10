import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_extras.stylable_container import stylable_container




st.title('Organic Tracker')
with st.sidebar:
    exclude_ads =  st.checkbox('Exclude ads')

def app_view(author):
    # Read data from jsonl file
    df = pd.read_json('https://storage.googleapis.com/social-data-public/sports_reddit_posts.jsonl', lines=True)
    # Add author filter
    authors = sorted(df['author'].unique())
    selected_author = author # st.selectbox('Select Author', authors, index=authors.index('nba'))

    subreddit_mapping = {
        'nba': 'nba',
        'nfl': 'nfl', 
        'nhl': 'hockey',
        'MLBOfficial': 'baseball'
    }
    if exclude_ads:
        df = df[#(df['subreddit'] == subreddit_mapping.get(selected_author, 'nba')) & 
                ~df['subreddit'].str.contains('u_') &
                (df['author'] == selected_author)]
    else:
        df = df[#(df['subreddit'] == subreddit_mapping.get(selected_author, 'nba')) & 
                (df['author'] == selected_author)]


    # Data preprocessing
    df['created_utc'] = pd.to_datetime(df['created_utc'], unit='s').dt.tz_localize('UTC').dt.tz_convert('US/Eastern')
        # Convert string columns to date/datetime
    df['created_datetime_est'] =  pd.to_datetime(df['created_utc'], unit='s').dt.tz_convert('US/Eastern')
    df['created_date_est'] = df['created_datetime_est'].dt.date
    

    df['week'] = df['created_utc'].dt.isocalendar().week
    df['week_date'] = df['created_utc'].dt.to_period('W-SUN').apply(lambda x: x.start_time.strftime('%Y-%m-%d'))
    df['week_end_date'] = df['created_utc'].dt.to_period('W-SUN').apply(lambda x: x.end_time.strftime('%Y-%m-%d'))
    df['year'] = df['created_utc'].dt.year

    # Page header with styling
    with stylable_container(
                key=f"header_container_{author}",
                css_styles="""
                        {
                        
                        color: white !important;
                        border-radius: 10px;
        
                        }
                    """,
            ):
        st.markdown(f"""
            This page tracks organic engagement metrics for posts in the :blue-background[r/{subreddit_mapping.get(selected_author, 'NBA')}] subreddit by the :orange-background[u/{selected_author.upper()}] account over time.
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
        # st.markdown('Date Range')
        # st.markdown(f"{df['created_utc'].dt.date.min()} to {df['created_utc'].dt.date.max()}")
        # Add date range selector
        c1,c2 = st.columns(2)
        if 'dates' not in st.session_state:
            st.session_state.dates = (df['created_datetime_est'].dt.date.min(), df['created_datetime_est'].dt.date.max())

        with c1:    
            date_range = st.date_input(
                "Date Range",
            value=st.session_state.dates,
            min_value=st.session_state.dates[0],
            max_value=st.session_state.dates[1],
                key=f"date_range_{author}"
            )

        with c2:
            st.write('')
            st.write('')
            def reset_date_filter():
                st.session_state[f'date_range_{author}'] = st.session_state.dates
            st.button('Reset',on_click = reset_date_filter, key=f"reset_{author}")
                
        

    if len(date_range) == 2:
        mask = (df['created_date_est'] > date_range[0]) & (df['created_date_est'] <= date_range[1])
        df = df.loc[mask]

    c1,c2 = st.columns([2,1])
    with c1:
        # Create scatter plot of posts by date
        st.subheader("Post Activity Over Time")
        # Add year selector
        years = sorted(df['year'].unique())
        c1,_ = st.columns([1,2])
        with c1:
            selected_years = st.multiselect('Select Years', years, default=[df['created_date_est'].max().year], key=f"scatter_year_select_{author}")

        # Filter data by selected years
        df_filtered = df[df['year'].isin(selected_years)]
        
        scatter_fig = px.scatter(
            df_filtered,
            x='created_utc',
            y='score',
            size='num_comments',
            # hover_data=['title'],
            # title='Post Activity by Date',
            template='plotly_white'
        )

        scatter_fig.update_layout(
            height=600,
            xaxis_title="Date",
            yaxis_title="Score",
            showlegend=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
        )

        st.plotly_chart(scatter_fig, use_container_width=True)
    with c2: 
        # Display embeds in container
        st.subheader("Recent Posts")
        embed_container = st.container(height=500)
        with embed_container:
            # Display embeds for each URL in the dataframe
            c1,c2 = st.columns(2)
            for i,r in df.sort_values('created_utc', ascending=False).head(10).iterrows():

                with c1:
                    st.markdown(f'''
                                Title: <a href = {r.permalink} target="_blank">{r.title}</a>

                                {'' if r.selftext == '' else r.selftext}

                                on {r.created_datetime_est.strftime('%Y-%m-%d at %H:%M:%S')}
            
                                by u/**{r.author}** in r/**{r.subreddit}**

                                Score: {r.score} | Comments: {r.num_comments}
                                ''', unsafe_allow_html=True)
                    
                with c2:
                    st.write('')
                    st.markdown(f'''
                                
                                ''')
                st.divider()
                c1,c2 = st.columns(2)


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
    with st.expander('View All Posts'):
        st.dataframe(df, 
                     column_config={
                        "permalink": st.column_config.LinkColumn(
                            "permalink",
                            width = 'small',
                            help="The top trending Streamlit apps",
                            # validate=r"^https://[a-z]+\.streamlit\.app$",
                            max_chars=100,
                            display_text="reddit link")
                        },
                     use_container_width=True)




    # Engagement trends visualization
    st.subheader("Engagement Trends")

    # Add year selector
    years = sorted(df['year'].unique())
    c1,_ = st.columns([1,2])
    with c1:
        selected_years = st.multiselect('Select Years', years, default=[df['created_date_est'].max().year], key=f"year_select_{author}")

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

    


tab1, tab2, tab3, tab4 = st.tabs(['NBA', 'NFL', 'NHL', 'MLB'])




with tab1:
    app_view('nba')
    
with tab2:
    app_view('nfl')
    
with tab3:
    app_view('nhl')
    
with tab4:
    app_view('MLBOfficial')
