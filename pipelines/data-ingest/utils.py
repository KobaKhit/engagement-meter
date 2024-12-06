import configparser
import pandas as pd
import pathlib
import praw
from pmaw import PushshiftAPI
import logging
import numpy as np
from tqdm import tqdm


# Read Configuration File
parser = configparser.ConfigParser()
script_path = pathlib.Path(__file__).parent.resolve()
config_file = "config.conf"
parser.read(f"{script_path}/{config_file}")
logging.info(f"Reading configuration file: {script_path}/{config_file}")
# Configuration Variables
SECRET = parser.get("reddit_config", "secret").strip('"')
CLIENT_ID = parser.get("reddit_config", "client_id").strip('"')
USER_AGENT = parser.get("reddit_config",'user_agent').strip('"')

# Fields that will be extracted from Reddit.
# Check PRAW documentation for additional fields.
# NOTE: if you change these, you'll need to update the create table
# sql query in the upload_aws_redshift.py file
POST_FIELDS = (
    "id",
    "title",
    "selftext",
    "score",
    "num_comments",
    "author",
    "created_utc",
    "url",
    "upvote_ratio",
    "over_18",
    "edited",
    "spoiler",
    "stickied",
    "subreddit"
)

class GetRedditData:
    """A class to fetch, transform and save Reddit data using PRAW and PMAW APIs.

    This class handles connecting to Reddit's API, fetching posts from a specified subreddit,
    transforming the data into a structured format, and saving it to a file.

    Attributes:
        output_name (str): Name of the output file (without extension)
        subreddit (str): Name of the subreddit to fetch data from
        time_filter (str): Time filter for posts (e.g. 'all', 'year', 'month')
        limit (int): Maximum number of posts to fetch. None means no limit.

    Inspired by https://github.com/modhpranav/reddit-data-pipeline/blob/main/airflow/utils/get_reddit_data.py
    """
    def __init__(self, output_name: str, username: str = None, subreddit: str = None, time_filter: str = None, limit: int = 100):
        self.output_name = output_name
        self.username = username
        self.subreddit = subreddit
        self.time_filter = time_filter
        self.limit = int(limit) if limit else None
        self.reddit_instance, self.pmaw_instance = self.api_connect()
    
    def api_connect(self):
        try:
            instance = praw.Reddit(
                client_id=CLIENT_ID, client_secret=SECRET, user_agent=USER_AGENT
            )
            instance.read_only = True
            api_praw = PushshiftAPI(praw=instance)
            return instance, api_praw
        except Exception as e:
            print(f"Unable to connect to API. Error: {e}")
            logging.error(f"Unable to connect to API. Error: {e}")
            return False
    
    def get_posts(self):
        """Create posts object for Reddit instance by subreddit and/or author
        
        Args:
            subreddit (str, optional): Subreddit name to fetch posts from
            author (str, optional): Reddit username to fetch posts from
            
        At least one of subreddit or author must be provided.
        """
        if not (self.subreddit or self.username):
            raise ValueError("At least one of subreddit or author must be provided")
            
        search_params = {"limit": self.limit}
        if self.subreddit:
            search_params["subreddit"] = self.subreddit
        if self.username:
            search_params["author"] = self.username
            
        self.posts = self.pmaw_instance.search_submissions(**search_params)
        print(len(self.posts))

    def extract_data(self):
        """Extract Data to Pandas DataFrame object"""
        list_of_items = []
        for submission in tqdm(self.posts):
            to_dict = vars(submission)
            sub_dict = {field: to_dict[field] for field in POST_FIELDS}
            list_of_items.append(sub_dict)
        self.extracted_data_df = pd.DataFrame(list_of_items)
    
    def transform_basic(self):
        """Some basic transformation of data. To be refactored at a later point."""

        # Convert epoch to UTC
        df = self.extracted_data_df
        print(df.head())
        # print(df.head())
        df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s")
        # Fields don't appear to return as booleans (e.g. False or Epoch time). Needs further investigation but forcing as False or True for now.
        # TODO: Remove all but the edited line, as not necessary. For edited line, rather than force as boolean, keep date-time of last
        # edit and set all else to None.
        df["over_18"] = np.where(
            (df["over_18"] == "False") | (df["over_18"] == False), False, True
        ).astype(bool)
        df["edited"] = np.where(
            (df["edited"] == "False") | (df["edited"] == False), False, True
        ).astype(bool)
        df["spoiler"] = np.where(
            (df["spoiler"] == "False") | (df["spoiler"] == False), False, True
        ).astype(bool)
        df["stickied"] = np.where(
            (df["stickied"] == "False") | (df["stickied"] == False), False, True
        ).astype(bool)
        self.df = df

    
    def load_to_csv(self):
        """Save extracted data to CSV file in /tmp folder"""
        extracted_data_df = self.df
        extracted_data_df['id'] = extracted_data_df['id'].astype(str)
        extracted_data_df['title'] = extracted_data_df['title'].astype(str)
        extracted_data_df['author'] = extracted_data_df['author'].astype(str)
        
        extracted_data_df.to_json(f"{self.output_name}.json", index=False, lines = True, orient='records')

    def run(self):
        result = {"status": "Failed", "message": "Failed to extract data"}
        try:
            if self.reddit_instance:
                self.get_posts()
                self.extract_data()
                self.transform_basic()
                self.load_to_csv()
                return {"status": "Success", "message": "Data extracted successfully"}
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            print(traceback.format_exc())
            logging.error(f"Error: {e}")
            logging.error(traceback.format_exc())
            return result
        
        

def main():
    reddit_data = GetRedditData(output_name="reddit_data", subreddit="nba", time_filter="all", limit=100)
    reddit_data.run()
    print(reddit_data)

if __name__ == "__main__":
    main()