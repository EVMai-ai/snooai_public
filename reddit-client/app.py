from models.llama_3_1_70B import llama_3_1_70B
from tools.reddit_scrapper import reddit_scrapper
from tools.reddit_commenter import reddit_commenter
from termcolor import colored
import json
from datetime import datetime
import os
import schedule
import time
import logging

# Configure logging
logging.basicConfig(
    filename='db/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)


def prepare_system_prompts():
    with open("prompts/sentiment_analyzer.md", "r") as file:
        system_prompt_sentiment_analyzer = file.read()
    with open("prompts/writer.md", "r") as file:
        system_prompt_writer = file.read()
    return system_prompt_sentiment_analyzer, system_prompt_writer


def chain_of_action(model, system_prompt_sentiment_analyzer, system_prompt_writer):
    # If you want to try it out with your own text, comment the block of code below
    # (from reddit_scrape =, to post_id =) and uncomment this:

    #post = "life is getting more and more expensive"

    try:

        # Scrape reddit posts for questions
        reddit_scrape = reddit_scrapper(["unpopularopinion", "1"])
        post = json.loads(reddit_scrape)
        print(type(post))
        print(colored("Somebody in reddit has this question:", "magenta"))
        print(f"Title: {post['Title']}\nBody: {post['Body']}")
        post_id = post["id"]


        # Give post to sentiment analyzer
        plan_prompt = f"""
        {{
        "post": "{post}"
        }}
        """

        analysis = model.answer(
            system_prompt=system_prompt_sentiment_analyzer, prompt=plan_prompt, json=True)
        print(analysis)
        analysis = json.loads(analysis)
        print(colored("\nWhat I've extracted from this post:",
                      "magenta") + "\nDefending points: ")
        for point in analysis["defending_points"]:
            print(point)
        print(
            "\n- - - - - - - - - -\n\n" + colored("My counterarguments:", "magenta") + f"""\n{analysis["argument1"]}\n\n{analysis["argument2"]}\n\n{analysis["argument3"]}\nRage-baiter: {analysis["offend"]}""")

        # Use the writer to write the comment
        write_prompt = f"""
        {{
        "post": {post},
        "defending_points": {analysis["defending_points"]},
        "argument1": {analysis["argument1"]},
        "argument2": {analysis["argument2"]},
        "argument3": {analysis["argument3"]},
        "offend": {analysis["offend"]}
        }}
        """
        writer = model.answer(
            system_prompt=system_prompt_writer, prompt=write_prompt, json=False)
        print(writer)
        print("My answer:")
        print(colored(f"""\n\n{writer}""", "cyan"))
        
        save_output_to_file(post, analysis, writer)

        reddit_commenter([post_id, writer])

    except Exception as e:
        print(colored("There was an error parsing the JSON object, probably, the model outputted a wrongly formatted JSON object. Try to run the program again :)", "green"))
        print(e)


def save_output_to_file(post_info, analysis, writer_response):
    """Save the terminal output to a file with timestamp in the db directory"""
    
    db_dir = "db"
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(db_dir, f"output_{timestamp}.txt")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("=== POST INFORMATION ===\n")
        f.write(f"Title: {post_info['Title']}\n")
        f.write(f"Body: {post_info['Body']}\n\n")
        
        f.write("=== AI ANALYSIS ===\n")
        f.write("Defending points:\n")
        for point in analysis["defending_points"]:
            f.write(f"- {point}\n")
        
        f.write("\nCounterarguments:\n")
        f.write(f"1. {analysis['argument1']}\n")
        f.write(f"2. {analysis['argument2']}\n")
        f.write(f"3. {analysis['argument3']}\n")
        f.write(f"Rage-baiter: {analysis['offend']}\n\n")
        
        f.write("=== AI RESPONSE ===\n")
        f.write(writer_response)


def run_bot():
    max_retries = 3  # Maximum number of attempts
    retry_delay = 10  # Seconds between attempts
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Starting scheduled execution (attempt {attempt + 1}/{max_retries})")
            print(f"Executing script - {datetime.now()}")
            
            model_instance = llama_3_1_70B()
            system_prompt_sentiment_analyzer, system_prompt_writer = prepare_system_prompts()
            
            chain_of_action(
                model_instance,
                system_prompt_sentiment_analyzer=system_prompt_sentiment_analyzer,
                system_prompt_writer=system_prompt_writer
            )
            
            logging.info("Execution completed successfully")
            break  
        except json.JSONDecodeError as e:
            logging.error(f"JSON Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
            print(colored(f"JSON Error. Retrying in {retry_delay} seconds...", "yellow"))
            if attempt < max_retries - 1:  
                time.sleep(retry_delay)
            else:
                logging.error("Maximum retry attempts reached")
                print(colored("Maximum retry attempts reached", "red"))
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            print(colored(f"Unexpected error: {str(e)}", "red"))
            break 


if __name__ == "__main__":
    print("Starting Reddit bot...")
    logging.info("Bot started")
    
    # Schedule job to run every 4 hours
    schedule.every(4).hours.do(run_bot)
    
    # Run immediately the first time
    run_bot()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
        print("Bot active - Waiting for next execution...", end='\r')
