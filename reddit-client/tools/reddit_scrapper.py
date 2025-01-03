from dotenv import dotenv_values
import praw
import os

def get_posted_ids():
    """Read all IDs abt already commented posts"""
    try:
        if not os.path.exists('db/posted_ids.txt'):
            return set()
        with open('db/posted_ids.txt', 'r') as f:
            return set(line.strip() for line in f)
    except Exception:
        return set()

def add_posted_id(post_id):
    """Agrega un nuevo ID a la lista de posts comentados"""
    try:
        os.makedirs('db', exist_ok=True)
        with open('db/posted_ids.txt', 'a') as f:
            f.write(f"{post_id}\n")
    except Exception as e:
        print(f"Error ID: {e}")

def reddit_scrapper(input_list):
    """
    Scrapes given subreddit's today's top posts for a number of posts.

    Parameters:
    input_list (list): A list containing the name of the subreddit and the number of tweets to scrape.
        - The first element is the name of the subreddit.
        - The second element is the number of posts to scrape.

        Example format: ["cats", "5"]

    Returns:
    (str): The formatted weather or an error message if something goes wrong.
    """
    CONFIG = dotenv_values("config/.env")
    subreddit_name = input_list[0]
    num_posts = int(input_list[1])
    posted_ids = get_posted_ids()

    # Initialize Reddit instance
    reddit = praw.Reddit(
        client_id=CONFIG["CLIENT_ID"],
        client_secret=CONFIG["CLIENT_SECRET"],
        user_agent="script:RddtTest:v1.0.0 (by /u/KeevCH)",
        username=CONFIG["USERNAME"],
        password=CONFIG["PASSWORD"]
    )

    try:
        subreddit = reddit.subreddit(subreddit_name)
        hot_posts = subreddit.hot(limit=5)

        
        for post in hot_posts:
            if not post.stickied and post.id not in posted_ids:
                
                title = post.title.replace('"', '\\"').replace('\n', ' ')
                body = post.selftext.replace('"', '\\"').replace('\n', ' ')
                
                add_posted_id(post.id)
                
                return f'{{"Title": "{title}", "Body": "{body}", "id": "{post.id}"}}'
        
        return '{"Title": "No new posts found", "Body": "All available posts have been commented", "id": "none"}'

    except Exception as e:
        print(f"Error en reddit_scrapper: {str(e)}")
        return '{"Title": "Error", "Body": "An error occurred", "id": "error"}'
