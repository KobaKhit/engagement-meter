import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_extras.stylable_container import stylable_container
import numpy as np

# Page configuration
st.set_page_config(
    page_title="NBA Reddit AMA Analysis",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 1rem 1rem;
    }
    .stTitle {
        font-size: 3rem !important;
        padding-bottom: 1rem;
    }
    .js-plotly-plot .nsewdrag {
        cursor: pointer;
    }
    /*.plot-container {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }*/
    /*div[data-testid="stHorizontalBlock"] {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }*/
    </style>
""", unsafe_allow_html=True)


# Data loading and preprocessing
@st.cache_data
def load_and_process_data():
    df = pd.read_csv('nba-ama.csv')
    df = df[df.name != 'Unknown']
    df['date'] = pd.to_datetime(df['date'])

    df.title = df.title.str.wrap(30)
    df.title = df.title.apply(lambda x: x.replace('\n', '<br>'))
    
    return df

def remove_outliers(df, column):
    Q1 = df[column].quantile(0.05)
    Q3 = df[column].quantile(0.95)
    IQR = Q3 - Q1
    df_filtered = df[
        (df[column] >= Q1 - 1.5 * IQR) & 
        (df[column] <= Q3 + 1.5 * IQR)
    ]
    return df_filtered

# Load data
df = load_and_process_data()

# Main title
st.title("🏀 Reddit r/NBA AMA Analysis")

# Control panel
st.sidebar.subheader("Analysis Controls")

show_raw_data = st.sidebar.checkbox('Show Raw Data Sample', help="Display a sample of the raw data")
include_outliers = st.sidebar.checkbox('Include Outliers', value=True, help="Include statistical outliers in the plots")

min_date = df['date'].min().date()
max_date = df['date'].max().date()


# Raw data display
if show_raw_data:
    st.subheader("Raw Data Sample")
    st.markdown("""
        Below is a sample of the raw data showing the most recent AMAs. The table includes key information such as titles, 
        participant names, categories, engagement metrics, and dates.
    """)
    st.dataframe(
        df[['title', 'name', 'category', 'num_comments', 'score', 'date']]
        .head(10)
        .style.highlight_max(axis=0, subset=['num_comments', 'score'])
    )

# st.divider()
# Key metrics
# st.subheader("📈 Key Metrics")
# st.markdown("""
#     These metrics provide a high-level overview of the AMA activity and engagement within the selected time period. 
#     They show the total volume of AMAs, average engagement levels, and the diversity of content through unique categories.
# """)


with stylable_container(
            key="intro",
            css_styles="""
                    {
                    background-color: #1e41e8;
                    color: white !important;
                    border-radius: 10px;
                    border-color: red !important;
                    width:105%;
                    padding: 15px
                    
                }
                """,
        ):
    st.markdown("""
        This analysis focuses on measuring engagement in Ask Me Anything (AMA) threads from the <a style='color: white' href = 'https://www.reddit.com/r/nba/' target='_blank'>NBA subreddit</a>. 
        It considers engagement based on the number of comments and upvotes for NBA personalities and affiliated figures. 
        The analysis aims to provide insights into the level of community interaction and the popularity of different AMAs.
    """, unsafe_allow_html = True)
metric_cols = st.columns(4)
with metric_cols[0]:
    st.metric("Total AMAs", len(df))
with metric_cols[1]:
    st.metric("Average Comments", int(df['num_comments'].mean()))
with metric_cols[2]:
    st.metric("Average Upvotes", int(df['score'].mean()))
with metric_cols[3]:
    st.metric("Unique Categories", df['category'].nunique())

# Data filtering based on user selections
if not include_outliers:
    df = remove_outliers(df, 'num_comments')
    df = remove_outliers(df, 'score')

# Scatter plot
st.subheader("Engagement Analysis")
st.markdown("""
    This visualization shows the relationship between comments and upvotes for each AMA, with different colors representing different categories. 
    The logarithmic scales help visualize the wide range of engagement levels, while the size of each point represents the number of comments. 
    This helps identify which AMAs generated the most community interaction and which categories tend to perform better.
""")

c1,c2 = st.columns(2)
with c1:
    st.markdown('**Community Engagement: Comments vs Upvotes**')
with c2:
    # st.write('')
    link_container = st.container()

log_scale_switch = st.toggle('Log Scale', value=True, help='Applying log trasnform to $x$ and $y$ values helps visualize the wide range of engagement levels (comments and upvotes) across different AMAs, making it easier to identify trends and patterns')


xmin, xmax = df['num_comments'].min(), df['num_comments'].max()
ymax = df['score'].max()
if log_scale_switch:
    xmin = np.log1p(df['num_comments']).min()-0.1
    xmax = np.log10(df['num_comments']).max()+0.2
    ymax = np.log10(df['score']).max()+0.2


scatter_fig = px.scatter(
    df,
    x='num_comments',
    y='score',
    color='category',
    size='num_comments',
    hover_data=['title', 'name', 'date','link'],
    # title='Community Engagement: Comments vs Upvotes',
    labels={
        'num_comments': 'Number of Comments',
        'score': 'Number of Upvotes',
        'category': 'AMA Category',
        'name': 'Participant Name',
        'date': 'Date'
    },
    log_x=log_scale_switch,
    log_y=log_scale_switch,
    template='plotly_white',
    hover_name='title'
)
scatter_fig.update_traces(
    marker=dict(sizemin=2),
    hovertemplate='<b>Title:</b> %{hovertext}<br>'+
                   '<b>Participant:</b> %{customdata[1]}<br>'+
                   '<b>Date:</b> %{customdata[2]}<br>'+
                   '<b>Number of Comments:</b> %{x}<br>'+
                   '<b>Number of Upvotes:</b> %{y}')
scatter_fig.update_layout(
    height=600,
    dragmode=False,
    showlegend=True,
    xaxis=dict(autorange=False),
    yaxis=dict(autorange=False, showgrid = False),
    xaxis_range=(xmin, xmax*1.1),
    yaxis_range=(0.1,ymax*1.1),
    legend=dict(
        yanchor="top",
        y=0.60,
        xanchor="left",
        x=0.85,
        bgcolor='rgba(0,0,0,0)',
        itemclick="toggleothers",
    ),
    legend_title_text='AMA Category',
    template={
        "layout": {
            "hovermode": "closest",
            "hoverlabel": {"bgcolor": "white"},
            "xaxis": {"showspikes": False},
            "yaxis": {"showspikes": False},
        }
    }
)
config = {'modeBarButtonsToRemove': ['zoom', 'pan', 'zoomIn', 'zoomOut', 'autoScale','lasso2d','select2d'],
          'modeBarButtonsToAdd': ['drawopenpath']}
st.plotly_chart(scatter_fig,on_select="rerun", key="scatter", config=config, use_container_width=True)
if st.session_state.scatter is not None and st.session_state.scatter['selection']['points'] != []:
    with link_container:
        selected_points = st.session_state.scatter
        link = selected_points['selection']['points'][0]['customdata'][3]
        st.write(f'**Link**: {link}')
    # selected_df = pd.DataFrame(selected_points)
    # st.dataframe(selected_df)

# Category analysis
st.subheader("Category Analysis")
st.markdown("""
    These box plots show the distribution of comments and upvotes across different AMA categories. 
    The boxes show the median and quartile ranges, while points indicate outliers. 
    This helps identify which categories consistently generate higher engagement and which ones have more variable performance.
""")
col1, col2 = st.columns(2)

with col1:
    comments_box = px.box(
        df,
        x='category',
        y='num_comments',
        title='Comment Distribution by Category',
        hover_data=['title', 'name', 'date','link'],
        labels={
            'category': 'AMA Category',
            'num_comments': 'Number of Comments'
        },
        points="outliers"
    )
    comments_box.update_traces(
        hovertemplate='<b>Title:</b> %{customdata[0]}<br>'+
                    '<b>Participant:</b> %{customdata[1]}<br>'+
                   '<b>Date:</b> %{customdata[2]}<br>'+
                   '<b>Number of Comments:</b> %{x}<br>'+
                   '<b>Number of Upvotes:</b> %{y}')
    comments_box.update_layout(
        dragmode=False,
        height=500,
        xaxis_tickangle=-45,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )
    st.plotly_chart(comments_box, config = config, use_container_width=True)

with col2:
    score_box = px.box(
        df,
        x='category',
        y='score',
        title='Upvote Distribution by Category',
        hover_data=['title', 'name', 'date','link'],
        labels={
            'category': 'AMA Category',
            'score': 'Number of Upvotes'
        },
        points="outliers"
    )
    score_box.update_traces(
        hovertemplate='<b>Title:</b> %{customdata[0]}<br>'+
                    '<b>Participant:</b> %{customdata[1]}<br>'+
                   '<b>Date:</b> %{customdata[2]}<br>'+
                   '<b>Number of Comments:</b> %{x}<br>'+
                   '<b>Number of Upvotes:</b> %{y}')
    score_box.update_layout(
        dragmode=False,
        height=500,
        xaxis_tickangle=-45,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )
    st.plotly_chart(score_box, config = config, use_container_width=True)

# Timeline analysis
st.subheader("Timeline Analysis")


with stylable_container(
            key="timeline",
            css_styles="""
                    {
                    background-color: #d93900;
                    color: white !important;
                    border-radius: 10px;
                    border-color: red !important;
                    width:105%;
                    padding: 15px
                    
                }
                """,
        ):
    st.markdown("""
        This timeline visualization tracks AMA performance over time, showing how engagement patterns have evolved. 
        The size of each point represents the number of comments, while the vertical position shows upvotes. 
        This helps identify trends, seasonal patterns, and whether certain categories perform better during specific time periods.
    """)

c1,c2 = st.columns(2)
with c1:
    st.markdown('**AMA Performance Over Time**')
with c2:
    link_timeline_container = st.container()
timeline_fig = px.scatter(
    df,
    x='date',
    y='score',
    color='category',
    size='num_comments',
    hover_data=['title', 'name','num_comments','link'],
    # title='AMA Performance Over Time',
    labels={
        'date': 'Date',
        'score': 'Number of Upvotes',
        'category': 'AMA Category',
        'num_comments': 'Number of Comments',
        'name': 'Participant Name'
    }
)

timeline_fig.update_traces(
    hovertemplate='<b>Title:</b> %{customdata[0]}<br>'+
                   '<b>Participant:</b> %{customdata[1]}<br>'+
                   '<b>Date:</b> %{x}<br>'+
                   '<b>Number of Comments:</b> %{customdata[2]}<br>'+
                   '<b>Number of Upvotes:</b> %{y}'
)

timeline_fig.update_layout(
    dragmode=False,
    height=600,
    legend_title_text='AMA Category',
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=False),
    xaxis_range = (df.date.min()- pd.Timedelta(days=30), df.date.max()+ pd.Timedelta(days=30)),
    yaxis_range = (0,df.score.max()*1.1),
    legend=dict(
        yanchor="top",
        y=1,
        xanchor="left",
        x=0.85,
        bgcolor='rgba(0,0,0,0)',
        itemclick="toggleothers",
    ),
)
st.plotly_chart(timeline_fig,on_select="rerun", key="timeline", config=config, use_container_width=True)
if st.session_state.timeline is not None and st.session_state.timeline['selection']['points'] != []:
    with link_timeline_container:
        selected_points = st.session_state.timeline
        link = selected_points['selection']['points'][0]['customdata'][3]
        st.write(f'**Link**: {link}')

# Top contributors analysis
st.subheader("Top Contributors Analysis")
st.markdown("""
    This bar chart highlights the most frequent AMA participants on r/NBA. 
    The chart focuses on participants who have conducted multiple AMAs, showing their total contribution to the community. 
    The accompanying table provides detailed statistics about their average engagement metrics.
""")
top_contributors = df.groupby('name').agg({
    'num_comments': ['count', 'mean'],
    'score': 'mean'
}).round(2)

# Add link to AMA
top_contributors['link'] = df.groupby('name')['title'].apply(lambda x: x.iloc[0])


top_contributors.columns = ['Number of AMAs', 'Average Comments', 'Average Upvotes', 'Link']
top_contributors = top_contributors.sort_values('Number of AMAs', ascending=False)
top_contributors_bar = top_contributors.head(10)

fig_contributors = px.bar(
    top_contributors_bar.reset_index(),
    x='name',
    y='Number of AMAs',
    title='Top 10 AMA Contributors',
    text='Number of AMAs',
    labels={
        'name': 'Participant Name',
        'Number of AMAs': 'Number of AMAs Conducted'
    }
)

fig_contributors.update_traces(textposition='outside')

fig_contributors.update_layout(
    dragmode=False,
    height=500,
    xaxis_tickangle=-45,
    yaxis_range = (0,top_contributors_bar['Number of AMAs'].max()*1.2),
    xaxis_title='Participant Name',
    yaxis_title='Number of AMAs Conducted',
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=False),
    font=dict(size=16)
)
st.plotly_chart(fig_contributors, config = config, use_container_width=True)

c1,c2 = st.columns([2,3])
with c1:
    # Detailed contributor stats
    st.subheader("Top Contributors Statistics")
    # st.markdown("""
    #     This table highlights top contributors with a gradient for "Number of AMAs" and bar charts for "Average Comments" and "Average Upvotes," enabling quick identification of top performers.
    # """)
    st.dataframe(
        top_contributors
        .rename(columns={'Average Comments': 'Avg Comments', 'Average Upvotes': 'Avg Upvotes'})
        .style.background_gradient(cmap='YlOrRd', subset=['Number of AMAs'])
        .format({'Number of AMAs': '{:.0f}', 'Avg Comments': '{:.0f}', 'Avg Upvotes': '{:.0f}'})
        .bar(subset=['Avg Comments', 'Avg Upvotes'], color='#90CAF9')
        .set_caption('Top Contributors Statistics')
        .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}])
        .set_properties(**{'text-align': 'center'})
        .set_properties(subset=['Number of AMAs'], **{'font-weight': 'bold'})
        .set_properties(subset=['Avg Comments', 'Avg Upvotes'], **{'font-style': 'italic'})
    )
with c2:
    # Category distribution
    st.subheader("Category Distribution")
    # st.markdown("""
    #     This donut chart shows the relative proportion of different AMA categories in the dataset. 
    #     The visualization helps understand the diversity of AMAs and which categories are more frequently represented. 
    # """)
    category_dist = px.pie(
        df,
        names='category',
        # title='Distribution of AMA Categories',
        labels={'category': 'AMA Category'},
        hole=0.4
    )
    category_dist.update_layout(
        height=500,
        legend_title_text='AMA Category',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.1,
            bgcolor='rgba(0,0,0,0)'
        ),
    )
    st.plotly_chart(category_dist, use_container_width=True)