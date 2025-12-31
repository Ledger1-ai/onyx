import random
from requests_oauthlib import OAuth1Session
import os
import json
import time
import openai
from openai import OpenAI

client = OpenAI(api_key="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")
import requests
import sched, datetime
import sqlite3
from PIL import Image
# TODO: The 'openai.organization' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(organization="org-PoypM7cnDzK7Qarl4MXPZAR6")'
# openai.organization = "org-PoypM7cnDzK7Qarl4MXPZAR6"

# Connect to the database (or create it if it doesn't exist)
conn = sqlite3.connect('tucquiz_data.db')

# Create the quiz_questions table
conn.execute('''CREATE TABLE IF NOT EXISTS quiz_questions (
                    id INTEGER PRIMARY KEY,
                    quiz_id TEXT,
                    question TEXT
                )''')

# Create the reply_authors table
conn.execute('''CREATE TABLE IF NOT EXISTS reply_authors (
                    id INTEGER PRIMARY KEY,
                    username TEXT
                    quiz_id TEXT
                )''')

# Create the correct_replies table
conn.execute('''CREATE TABLE IF NOT EXISTS correct_replies (
                    id INTEGER PRIMARY KEY,
                    author_un TEXT,
                    reply_id TEXT,
                    quiz_id TEXT
                )''')

conn.execute('''CREATE TABLE IF NOT EXISTS quiz_winners (
                    id INTEGER PRIMARY KEY,
                    author_un TEXT,
                    winning_reply_id TEXT,
                    quiz_id TEXT
                )''')

# Commit the changes and close the connection
conn.commit()
conn.close()

consumer_key = ('bF00XpfzerEL98kNNuiJz4hAa')
consumer_secret = ('UOBD9vvZhI4PeuapjEdsSurlNy4BnXdHSKbcYbKIVDc1bvfMkv')

# Get request token
request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

try:
    fetch_response = oauth.fetch_request_token(request_token_url)
except ValueError:
    print(
        "There may have been an issue with the consumer_key or consumer_secret you entered."
    )

resource_owner_key = fetch_response.get("oauth_token")
resource_owner_secret = fetch_response.get("oauth_token_secret")
print("Got OAuth token: %s" % resource_owner_key)

# Get authorization
base_authorization_url = "https://api.twitter.com/oauth/authorize"
authorization_url = oauth.authorization_url(base_authorization_url)
print("Please go here and authorize: %s" % authorization_url)
verifier = input("Paste the PIN here: ")

# Get the access token
access_token_url = "https://api.twitter.com/oauth/access_token"
oauth = OAuth1Session(
    consumer_key,
    client_secret=consumer_secret,
    resource_owner_key=resource_owner_key,
    resource_owner_secret=resource_owner_secret,
    verifier=verifier,
)
oauth_tokens = oauth.fetch_access_token(access_token_url)

access_token = oauth_tokens["oauth_token"]
access_token_secret = oauth_tokens["oauth_token_secret"]

# Make the request
oauth = OAuth1Session(
    consumer_key,
    client_secret=consumer_secret,
    resource_owner_key=access_token,
    resource_owner_secret=access_token_secret,
)

#TUCQuiz Bot

def generate_q():
  prompt = "Generate a random interesting question requiring an anecdotal response as a short tweet."

  # Generate text using OpenAI's GPT-3 model
  completions = client.completions.create(engine="text-davinci-003",
  prompt=prompt,
  max_tokens=140,
  n=1,
  stop=None,
  temperature=0.8)
  message = completions.choices[0].text
  return message

def generate_a(message):
  prompt = f"Generate an answer to the following quiz question: {message}."

  # Generate text using OpenAI's GPT-3 model
  completions = client.completions.create(engine="text-davinci-003",
  prompt=prompt,
  max_tokens=140,
  n=1,
  stop=None,
  temperature=0.5)
  message = completions.choices[0].text
  return message

def check_answer(question, answer, username):
#   prompt = f"Reference Tweet: '{answer}'. Determine definitively if the reference tweet contains the correct answer to the following quiz question: '{question}'. Generate a tweet reply to inform '@{username}' of the results. If correct, inform them that they have been entered into a drawing for a tier 1 whitelist spot. If incorrect, do not enter them in the whitelist and let them know they can only try once and that they can try again in the next quiz. Use a formal english tone and sign the tweet 'The Observer, TUC Concierge'."

    prompt = f"If '{answer}' contains any response, even loosely, to the following prompt tweet: '{question}', generate a tweet reply to inform the author of the answer, '@{username}', that they have been entered into a drawing for a tier 1 whitelist spot for the @lochnesssociety satellite project and add a light-hearted comment about the response. Use a formal english tone and sign the tweet 'The Observer, TUC Concierge'."

  # Generate text using OpenAI's GPT-3 model
    completions = client.completions.create(engine="text-davinci-003",
    prompt=prompt,
    max_tokens=280,
    n=1,
    stop=None,
    temperature=0.5)
    message = completions.choices[0].text
    return message

def boolean_answer(check):
#   prompt = f"Read this: '{check}'. If it said the answer was correct, reply with the value: True. If it said the answer was incorrect, reply with the value: False."

    prompt = f"Read this: '{check}'. If it said that they have been entered into the whitelist, reply with the value: True. If it said that they should try again, reply with the value: False."  
  # Generate text using OpenAI's GPT-3 model
    completions = client.completions.create(engine="text-davinci-003",
    prompt=prompt,
    max_tokens=280,
    n=1,
    stop=None,
    temperature=0.5)
    boo = completions.choices[0].text
    return boo

def check_replies_to_tweet(tweet_id):
  url = f"https://api.twitter.com/2/tweets/search/recent?query=conversation_id:{tweet_id}&tweet.fields=in_reply_to_user_id,author_id,created_at,conversation_id"
  headers = {'Authorization': f'Bearer AAAAAAAAAAAAAAAAAAAAAPKWlgEAAAAAlkwwXD3w%2B%2Bl2qNErEuftLK1Ekrw%3DG9LlCMjt6DyfN6KghsMocj6m72w8JegHezGINw4zVVGdFbD6sC'}
  response = requests.get(url, headers=headers)
  data = response.json()
  return data


def get_username_from_author_id(author_id):
    url = f"https://api.twitter.com/2/users/{author_id}"
    r = oauth.get(url)
    return r.json()['data']['username']


def post_a_reply(tweet_id, message):
    url = "https://api.twitter.com/2/tweets"
    post_data = {"text": message, "reply": {"in_reply_to_tweet_id": f"{tweet_id}"}}
    response = oauth.post(url, json=post_data)
    if response.status_code != 201:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    #return tweet id
    print("SUCCESS")
    print(response.json().data.id)
    return response.json().data.id

def post_tweet(message, imgid):
    # Post the generated text as a tweet
    url = "https://api.twitter.com/2/tweets"
    if imgid == None:
      post_data = {"text": message}
    else:
        post_data = {"text": message, "media": {"media_ids": [f"{imgid}"]}}
        response = oauth.post(url, json=post_data)
    if response.status_code != 201:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    #return tweet id
    print("SUCCESS")
    print(response.json().data.id)
    return response.json().data.id


log_file_path = "/home/info/K/TwitterAutomations/tucquizlog.txt"
log_file_patha = "/home/info/K/TwitterAutomations/tucquizclog.txt"
log_file_pathq = "/home/info/K/TwitterAutomations/tucquizqlog.txt"
log_file_pathw = "/home/info/K/TwitterAutomations/tucquizwlog.txt"

# Generate TUCQuiz Image
def generate_quizimage_from_dalle():
  # Generate image using DALL-E's model
    response = client.images.generate(prompt="a centered wide shot of a grande, ornate, futuristic stage for a trivia game show. hyerophant, god light, cinematic look, octane render, electric, vibrant, detailed, bloom, nanite",
    n=1,
    size="512x512")
    image_url = response.data[0].url
    print(image_url)
    return image_url

# download the image and store in specified path
def download_quizimage(quiz_image_url):
    path = "/home/info/K/TwitterAutomated/TUCQuizimage.jpg"
    response = requests.get(quiz_image_url)
    file = open(path, "wb")
    file.write(response.content)
    file.close()

def make_TUCQuizspace_image():
    # Load the jpg and png images
    jpg_image = Image.open('/home/info/K/TwitterAutomated/TUCQuizimage.jpg')
    png_image = Image.open('/home/info/K/ASI_Space/TUCQuizCover.png')
    print("Images loaded")
    # Resize the png image to fit within the jpg image
    print("Resizing png image")
    png_image = png_image.resize(jpg_image.size)

    print("Pasting png image onto jpg image")
    # Paste the png image onto the jpg image
    jpg_image.paste(png_image, (0, 0), png_image)

    print("Saving new image")
    # Save the combined image as a new file
    jpg_image.save('/home/info/K/ASI_Space/TUCQuizSpaceFlyer.jpg')
    print("TUCQuizSpaceFlyer.jpg saved")
# Load the jpg and png images

def upload_TUCQuiz_image():
    url = "https://upload.twitter.com/1.1/media/upload.json"
    files = {"media": open("/home/info/K/ASI_Space/TUCQuizSpaceFlyer.jpg", "rb")}
    r = oauth.post(url, files=files)
    print("Image uploaded to Twitter")
    return r.json()['media_id']

s = sched.scheduler(time.time, time.sleep)

def quiz_script():
    print("Generating quiz...\n")
    message = generate_q()
    print(f"Generated the following question:\n{message}\n")
    print("Generating quiz image...\n")
    quiz_image_url = generate_quizimage_from_dalle()
    print(f"Generated the following image:\n{quiz_image_url}\n")
    print("Downloading quiz image...\n")
    download_quizimage(quiz_image_url)
    print("Making quiz space image...\n")
    make_TUCQuizspace_image()
    print("Uploading quiz image...\n")
    imgid = upload_TUCQuiz_image()
    return message, imgid

def post_quiz_tweet(message, imgid):
    conn = sqlite3.connect('tucquiz_data.db')
    print("Posting quiz tweet...\n")
    quiz_id = post_tweet(message, imgid)
    print(f"Quiz tweet posted with ID: {quiz_id}\n")
    print("Writing quiz info to log file...\n")
    conn.execute("INSERT INTO quiz_questions (quiz_id, question) VALUES (?, ?)", (quiz_id, message.strip()))
    conn.commit()
    conn.close()
    return quiz_id

def response_script(quiz_id, message):
    print("Checking for replies...\n")
    print(f"Quiz ID: {quiz_id}\n")
    replies = check_replies_to_tweet(quiz_id)
    print(f"Response script replies: {replies}\n")
    if replies['meta']['result_count'] == 0:
        print("No replies found")
    else:
        rng = len(replies["data"])
        print(f"Replies found: {rng} \n")
        for index, reply in enumerate(replies["data"]):
            conn = sqlite3.connect('tucquiz_data.db')
            # if not os.path.exists(log_file_path):
            #         open(log_file_path, 'w').close()
            # if not os.path.exists(log_file_patha):
            #         open(log_file_patha, 'w').close()
            # with open(log_file_path, "r") as log_file:
                # log_data = log_file.readlines()
                # Query the reply_authors table for the specified username
            reply_id = reply['id']
            print(f"Reply ID: {reply_id}\n")
            author_id = reply['author_id']
            print(f"Author ID: {author_id}\n")
            reply_username = get_username_from_author_id(author_id).strip()
            cursor = conn.execute("SELECT * FROM reply_authors WHERE username = ?", (reply_username,))
            if f'{author_id}' == "1598217280604631040":
                print("The user: " + reply_username + " is one of ours, skipping...")
                print(f"Waiting 15 seconds before checking for new replies...")
                for i in range(15, 0, -1):
                    print(f"{i} seconds remaining...")
                    time.sleep(1)
                print("\n")
                continue
            if f'{author_id}' == "1510295708439515138":
                print("The user: " + reply_username + " is one of ours, skipping...")
                print(f"Waiting 15 seconds before checking for new replies...")
                for i in range(15, 0, -1):
                    print(f"{i} seconds remaining...")
                    time.sleep(1)
                print("\n")
                continue
            if f'{author_id}' == "1527491418096140288":
                print("The user: " + reply_username + " is one of ours, skipping...")
                print(f"Waiting 15 seconds before checking for new replies...")
                for i in range(15, 0, -1):
                    print(f"{i} seconds remaining...")
                    time.sleep(1)
                print("\n")
                continue
            cursor = conn.execute("SELECT * FROM reply_authors WHERE username = ? AND quiz_id = ?", (reply_username, quiz_id))
            #check if the reply is from one of our company accounts
            if cursor.fetchone() is not None:
                if f'{author_id}' != "1598217280604631040":
                # If the reply has already been addressed, skip it
                    print(f"{reply_username} has already been addressed, skipping...")
                    print(f"Waiting 15 seconds before checking for new replies...")
                    for i in range(15, 0, -1):
                        print(f"{i} seconds remaining...")
                        time.sleep(1)
                    print("\n")
                    continue
            if cursor.fetchone() is None: 
                if f"{author_id}" != "1598217280604631040" or "1510295708439515138" or "1527491418096140288":
                    try:
                        print("Valid reply found, processing...")
                        print("Current Value of i:\n")
                        #get index value of current reply in the loop
                        print(f"{index}\n")
                        answer = reply['text']
                        print(f"Reply found from {reply_username}:\n{reply['text']}\n")
                        print(message)
                        print("Checking answer...\n")
                        check = check_answer(message.strip(), answer.strip(), reply_username.strip())
                        print(f"Answer checked, result:\n{check}\n")
                        print("Converting answer to boolean...\n")
                        boo = boolean_answer(check).strip()
                        print(f"Answer converted to boolean, result:\n{boo}\n")
                        print("Posting reply...\n")
                        post_a_reply(reply_id, check) # run your script
                        print(f"Reply posted to {reply_username}\n")
                    except Exception as e:
                        print(e)
                        print("Error occurred, retrying in 30 seconds...")
                        time.sleep(15)
                        print("Valid reply found, processing...")
                        print("Current Value of i:\n")
                        print(f"{index}\n")
                        answer = reply['text']
                        print(f"Reply found from {reply_username}:\n{reply['text']}\n")
                        print("Checking answer...\n")
                        check = check_answer(message, answer, reply_username).strip()
                        print(f"Answer checked, result:\n{check}\n")
                        print("Converting answer to boolean...\n")
                        boo = boolean_answer(check).strip()
                        print(f"Answer converted to boolean, result:\n{boo}\n")
                        print("Posting reply...\n")
                        post_a_reply(reply_id, check) # run your script
                        print(f"Reply posted to {reply_username}\n")  # retry your script      
                # Update the log file with the posted tweet's id
                # with open(log_file_path, "a") as log_file:
                #     log_file.write(f"{reply_username}\n")
                # Write to the reply_authors table
                conn.execute("INSERT INTO reply_authors (username, quiz_id) VALUES (?, ?)", (reply_username, quiz_id))
                conn.commit()
                if boo == "True":
                    # with open(log_file_patha, "a") as log_file:
                    #     log_file.write(f"{reply_username}\n{reply_id}\n")
                    # Write to the correct_replies table
                    print(f"Reply from {reply_username} was correct, writing to database...\n")
                    conn.execute("INSERT INTO correct_replies (author_un, reply_id, quiz_id) VALUES (?, ?, ?)", (reply_username, reply_id, quiz_id))
                    conn.commit()
                    print("Reply written to database\n")
                print(f"Waiting 15 seconds before checking for new replies...")
                for i in range(15, 0, -1):
                    print(f"{i} seconds remaining...")
                    time.sleep(1)
                print("\n")
                continue

def random_drawing_script():
    # if not os.path.exists(log_file_patha):
    #     open(log_file_patha, 'w').close()
    # if not os.path.exists(log_file_pathw):
    #     open(log_file_pathw, 'w').close()
    print("Random drawing script started\n")
    # Connect to the database
    print("Connecting to database...\n")
    conn = sqlite3.connect('tucquiz_data.db')
    print("Connected to database\n")
    # Load the list of users who have answered correctly
    print("Loading list of users who have answered correctly...\n")
    cursor = conn.execute(f"SELECT * FROM correct_replies WHERE quiz_id = '{quiz_id}'")
    correct_replies = cursor.fetchall()
    print("List loaded\n")
    # Select a random user from the list
    print("Selecting a random user from the list...\n")
    winner = random.choice(correct_replies)
    wuser = winner[1]
    tweet_id = winner[2]
    print("User selected\n User: " + f"{wuser}" + "\n Tweet ID: " + f"{tweet_id}" + "\n")
    # Post a tweet congratulating the winner
    print("Posting a tweet congratulating the winner...\n")
    post_a_random_drawing_tweet(wuser, tweet_id)
    # Print Tweet Info
    print(f"Tweet posted to {wuser}\n Tweet ID: {tweet_id}\n")
    # Update the quiz_winner table
    print("Updating the quiz_winner table...\n")
    conn.execute("INSERT INTO quiz_winners (author_un, winning_reply_id, quiz_id) VALUES (?, ?, ?)", (winner[1], winner[2], quiz_id))
    conn.commit()
    print("Table updated\n")
    # with open(log_file_patha, "r") as log_file:
    #     log_data = log_file.readlines()
    #     # Select a random user from the odd line in the list
    #     winner = random.choice(log_data[::2]).strip()
    #     if not bool(f"{winner}"):
    #         winner = random.choice(log_data[::2]).strip()
    #     index_of_odd_line = log_data.index(f"{winner}\n")
    #     tweet_id = log_data[index_of_odd_line + 1].strip()
    #     # Post a tweet congratulating the winner
    #     with open(log_file_pathw, "w") as log_file:
    #         log_file.write(f"{winner}\n{tweet_id}\n")
    # post_a_random_drawing_tweet(winner, tweet_id)
    return winner, tweet_id


def get_author_id_from_username(username):
    print("Getting author ID from username...\n")
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    r = oauth.get(url)
    print("Author ID retrieved\n")
    return r.json()['data']['id']

def post_a_random_drawing_tweet(winner, tweet_id):
    # Post a tweet congratulating the winner
    print("Generating congratulations post...\n")
    def generate_congratulations_post_from_openai(winner):
        prompt = f"Write a tweet similar to the following: 'Congratulations to @{winner} for winning a @lochnesssociety WL position! We will be contacting you shortly to arrange your prize. To all the other participants, thank you for playing and good luck next time!' Use a formal english tone and sign the tweet 'The Observer, TUC Concierge'."
    # Generate text using OpenAI's GPT-3 model
        completions = client.completions.create(engine="text-davinci-003",
        prompt=prompt,
        max_tokens=140,
        n=1,
        stop=None,
        temperature=0.5)
        message = completions.choices[0].text
        print("Congratulations post generated\n")
        return message
    print("Preparing congratulations tweet...\n")
    message = generate_congratulations_post_from_openai(winner)
    print("Congratulations tweet generated!\n Tweet: " + f"{message}" + "\n Tweet ID: " + f"{tweet_id}" + "\n Tweet Author: " + f"{winner}" + "\n")
    def post_main(tweet_id, message):
        try:
            print("Posting tweet...\n")
            post_a_reply(tweet_id, message)
            print("Tweet posted!\n")
        except Exception as e:
            print(e)
            print("Error occurred, retrying in 30 seconds...")
            time.sleep(30)
            print("Tweet was too long, generating a new one...\n")
            message = generate_congratulations_post_from_openai(winner)
            post_main(tweet_id, message)
    post_main(tweet_id, message)

#Set initial values for variables
quiz_id = ""
message = ""
#Calculate and print the time remaining until the next tweet
while True:
    def run_quiz_script():
        # your script logic here with error handling
        try:
            message, imgid = quiz_script()
            quiz_id = post_quiz_tweet(message, imgid)
            return quiz_id, message
        except Exception as e:
            print(e)
            print("Error occurred, retrying in 30 seconds...")
            time.sleep(30)
            run_quiz_script()  # retry your script
    def run_response_script(quiz_id, message):
        # your script logic here with error handling
        try:
            response_script(quiz_id, message)  # run your script
        except Exception as e:
            print(e)
            print("Error occurred, retrying in 30 seconds...")
            time.sleep(30)
            run_response_script(quiz_id, message)  # retry your script
    def run_random_drawing_script():
        # your script logic here with error handling
        winner, tweet_id = random_drawing_script()  # run your script
        print(tweet_id)
        print(winner)
        print("Congratulated the Winner!")
    now = datetime.datetime.now()
    # Preset Times:
    time1 = 14
    time2 = 19
    time3 = 22
    time4 = 3
    time5 = 7
    time6 = 10
    time7 = 13

    def convert24hrtimeto12hrtime(time):
        if time == 0:
            return "12:00 AM"
        elif time == 1:
            return "1:00 AM"
        elif time == 2:
            return "2:00 AM"
        elif time == 3:
            return "3:00 AM"
        elif time == 4:
            return "4:00 AM"
        elif time == 5:
            return "5:00 AM"
        elif time == 6:
            return "6:00 AM"
        elif time == 7:
            return "7:00 AM"
        elif time == 8:
            return "8:00 AM"
        elif time == 9:
            return "9:00 AM"
        elif time == 10:
            return "10:00 AM"
        elif time == 11:
            return "11:00 AM"
        elif time == 12:
            return "12:00 PM"
        elif time == 13:
            return "1:00 PM"
        elif time == 14:
            return "2:00 PM"
        elif time == 15:
            return "3:00 PM"
        elif time == 16:
            return "4:00 PM"
        elif time == 17:
            return "5:00 PM"
        elif time == 18:
            return "6:00 PM"
        elif time == 19:
            return "7:00 PM"
        elif time == 20:
            return "8:00 PM"
        elif time == 21:
            return "9:00 PM"
        elif time == 22:
            return "10:00 PM"
        elif time == 23:
            return "11:00 PM"
        elif time == 24:
            return "12:00 AM"
        else:
            return "Error"

    t1 = convert24hrtimeto12hrtime(time1)
    t2 = convert24hrtimeto12hrtime(time2)
    t3 = convert24hrtimeto12hrtime(time3)
    t4 = convert24hrtimeto12hrtime(time4)
    t5 = convert24hrtimeto12hrtime(time5)
    t6 = convert24hrtimeto12hrtime(time6)
    t7 = convert24hrtimeto12hrtime(time7)

    # time1 = int(input("Enter the time you want to post the first tweet in 24 hour format (H or HH): ").strip())
    post1 = datetime.datetime(now.year, now.month, now.day, time1, 0)
    # time2 = int(input("Enter the time you want to post the second tweet in 24 hour format (H or HH): ").strip())
    post2 = datetime.datetime(now.year, now.month, now.day, time2, 0)
    # time3 = int(input("Enter the time you want to post the third tweet in 24 hour format (H or HH): ").strip())
    post3 = datetime.datetime(now.year, now.month, now.day, time3, 0)
    # time4 = int(input("Enter the time you want to post the fourth tweet in 24 hour format (H or HH): ").strip())
    post4 = datetime.datetime(now.year, now.month, now.day, time4, 0)
    # time5 = int(input("Enter the time you want to post the fifth tweet in 24 hour format (H or HH): ").strip())
    post5 = datetime.datetime(now.year, now.month, now.day, time5, 0)
    # time6 = int(input("Enter the time you want to post the sixth tweet in 24 hour format (H or HH): ").strip())
    post6 = datetime.datetime(now.year, now.month, now.day, time6, 0)
    # time7 = int(input("Enter the time you want to post the seventh tweet in 24 hour format (H or HH): ").strip())
    post7 = datetime.datetime(now.year, now.month, now.day, time7, 0)
    if now.hour >= time1:
        post1 += datetime.timedelta(days=1)
    if now.hour >= time2:
        post2 += datetime.timedelta(days=1)
    if now.hour >= time3:
        post3 += datetime.timedelta(days=1)
    if now.hour >= time4: 
        post4 += datetime.timedelta(days=1)
    if now.hour >= time5:
        post5 += datetime.timedelta(days=1)
    if now.hour >= time6:
        post6 += datetime.timedelta(days=1)
    if now.hour >= time7:
        post7 += datetime.timedelta(days=1)

     # Calculate the time remaining until the next tweet
    delta_post1 = (post1 - now).total_seconds()
    delta_post2 = (post2 - now).total_seconds()
    delta_post3 = (post3 - now).total_seconds()
    delta_post4 = (post4 - now).total_seconds() 
    delta_post5 = (post5 - now).total_seconds()
    delta_post6 = (post6 - now).total_seconds()
    delta_post7 = (post7 - now).total_seconds()

    print(delta_post1)
    print(delta_post2)
    print(delta_post3)
    print(delta_post4)
    print(delta_post5)
    print(delta_post6)
    print(delta_post7)

    if delta_post1 > 15.000000:
        next_event = delta_post1
        #print(delta_post1)
        print("List of times remaining until next tweet:")
        print(f"Time remaining until {t1} reply check tweet: " + "{}".format(datetime.timedelta(seconds=next_event)))
        time.sleep(1)
    if delta_post2 > 15.000000:
        next_event = delta_post2
        #print(delta_post2)
        print(f"Time remaining until {t2} Daily TUC Quiz reply check tweet:" + "{}".format(datetime.timedelta(seconds=next_event)))
        time.sleep(1)
    if delta_post3 > 15.000000:
        next_event = delta_post3
        #print(delta_post3)
        print(f"Time remaining until {t3} tweet: " + "{}".format(datetime.timedelta(seconds=next_event)))
        time.sleep(1)
    if delta_post4 > 15.000000:
        next_event = delta_post4
        #print(delta_post2)
        print(f"Time remaining until {t4} tweet: " + "{}".format(datetime.timedelta(seconds=next_event)))
        time.sleep(1)
    if delta_post5 > 15.000000:
        next_event = delta_post5
       # print(delta_post5)
        print(f"Time remaining until {t5} tweet: " + "{}".format(datetime.timedelta(seconds=next_event)))
        time.sleep(1)
    if delta_post6 > 15.000000:
        next_event = delta_post6
        #print(delta_post6)
        print(f"Time remaining until {t6} tweet: " + "{}".format(datetime.timedelta(seconds=next_event)))
        time.sleep(1)
    if delta_post7 > 15.000000:
        next_event = delta_post7
        #print(delta_post7)
        print(f"Time remaining until {t7} tweet: " + "{}".format(datetime.timedelta(seconds=next_event)))
        time.sleep(1)
    if delta_post1 < 15.000000:
        print(f"{t1} Script running")
        conn = sqlite3.connect('tucquiz_data.db')
        print("Database Connected\n")
        print("Checking for Quiz ID\n")
        if not bool(quiz_id):
            print("No Quiz ID Stored...Searching the database\n")
            # Get the latest quiz ID from the quiz_questions table
            print("Getting the latest quiz ID from the database\n")
            c = conn.cursor()
            c.execute("SELECT quiz_id FROM quiz_questions ORDER BY id DESC LIMIT 1")
            quiz_id = c.fetchone()[0]
            print(f"Quiz ID Found: {quiz_id}\n")
            # Get the corresponding question from the quiz_questions table
            print("Getting the corresponding question from the database\n")
            c.execute(f"SELECT question FROM quiz_questions WHERE quiz_id = '{quiz_id}'")
            question = c.fetchone()[0]
            print(f"Question Found: {question}\n")
            # with open(log_file_pathq, "r") as log_file:
            #     log_data = log_file.readlines()
            #     quiz_id = log_data[-2].strip()
            #     message = log_data[-1].strip()
            #     print(f"Quiz ID Found: {quiz_id}\n")
            conn.commit()
        run_response_script(quiz_id, message)
        conn.commit()
        conn.close()
    if delta_post2 < 15.000000:
        print(f"Daily TUC Quiz Script running - {t2}")
        # if not os.path.exists(log_file_patha):
        #     open(log_file_patha, 'w').close()
        # with open(log_file_patha, 'r') as log_file:
        #     log_data = log_file.readlines()
        # Connect to the database
        conn = sqlite3.connect('tucquiz_data.db')
        print("Database Connected\n")
        if not bool(quiz_id):
            print("No Quiz ID Stored...Searching the database\n")
            # Get the latest quiz ID from the quiz_questions table
            print("Getting the latest quiz ID from the database\n")
            c = conn.cursor()
            c.execute("SELECT quiz_id FROM quiz_questions ORDER BY id DESC LIMIT 1")
            quiz_id = c.fetchone()[0]
            print(f"Quiz ID Found: {quiz_id}\n")
            # Get the corresponding question from the quiz_questions table
            print("Getting the corresponding question from the database\n")
            c.execute(f"SELECT question FROM quiz_questions WHERE quiz_id = '{quiz_id}'")
            question = c.fetchone()[0]
            print(f"Question Found: {question}\n")
            # with open(log_file_pathq, "r") as log_file:
            #     log_data = log_file.readlines()
            #     quiz_id = log_data[-2].strip()
            #     message = log_data[-1].strip()
            #     print(f"Quiz ID Found: {quiz_id}\n")
            conn.commit()
            run_response_script(quiz_id, message)
        else: 
            print("Getting the latest quiz ID from the database\n")
            c = conn.cursor()
            c.execute("SELECT quiz_id FROM quiz_questions ORDER BY id DESC LIMIT 1")
            quiz_id = c.fetchone()[0]
            print(f"Quiz ID Found: {quiz_id}\n")
            # Get the corresponding question from the quiz_questions table
            print("Getting the corresponding question from the database\n")
            c.execute(f"SELECT question FROM quiz_questions WHERE quiz_id = '{quiz_id}'")
            question = c.fetchone()[0]
            print(f"Question Found: {question}\n")
            # with open(log_file_pathq, "r") as log_file:
            #     log_data = log_file.readlines()
            #     quiz_id = log_data[-2].strip()
            #     message = log_data[-1].strip()
            #     print(f"Quiz ID Found: {quiz_id}\n")
            conn.commit()
            run_response_script(quiz_id, message)
        conn.commit()
        # Checking for correct replies in the correct_replies table
        c = conn.cursor()
        c.execute(f"SELECT * FROM correct_replies WHERE quiz_id = '{quiz_id}'")
        print("Checking for correct replies\n")
        # if there are correct replies, run the random drawing script
        if c.fetchall():
            print("Correct replies found\n")
            print("Running random drawing script\n")
            run_random_drawing_script()
        else:
            print("No correct replies found\n")
        #     if bool(log_data):
        #         run_random_drawing_script()
        #     else:
        #         print("No quiz ID found in log file")
        # with open(log_file_path, "r") as log_file:
        #     first_line = log_file.readline()
        # with open(log_file_path, 'w') as log_file:
        #     log_file.write(first_line)  
        # with open(log_file_patha, 'w') as log_file:
        #     log_file.write('')
        print("Running quiz script\n")    
        quiz_id, message = run_quiz_script()
        print("Quiz script complete\n")
        conn.commit()
        conn.close()
    if delta_post3 < 15.000000:
        print(f"{t3} Script running")
        # if not bool(quiz_id):
        #     print("No Quiz ID Stored...Searching\n")
        #     with open(log_file_pathq, "r") as log_file:
        #         log_data = log_file.readlines()
        #         quiz_id = log_data[-2].strip()
        #         message = log_data[-1].strip()
        #         print(f"Quiz ID Found: {quiz_id}\n")
        # run_response_script(quiz_id, message)
        conn = sqlite3.connect('tucquiz_data.db')
        print("Database Connected\n")
        print("Checking for Quiz ID\n")
        if not bool(quiz_id):
            print("No Quiz ID Stored...Searching the database\n")
            # Get the latest quiz ID from the quiz_questions table
            print("Getting the latest quiz ID from the database\n")
            c = conn.cursor()
            c.execute("SELECT quiz_id FROM quiz_questions ORDER BY id DESC LIMIT 1")
            quiz_id = c.fetchone()[0]
            print(f"Quiz ID Found: {quiz_id}\n")
            # Get the corresponding question from the quiz_questions table
            print("Getting the corresponding question from the database\n")
            c.execute(f"SELECT question FROM quiz_questions WHERE quiz_id = '{quiz_id}'")
            question = c.fetchone()[0]
            print(f"Question Found: {question}\n")
            # with open(log_file_pathq, "r") as log_file:
            #     log_data = log_file.readlines()
            #     quiz_id = log_data[-2].strip()
            #     message = log_data[-1].strip()
            #     print(f"Quiz ID Found: {quiz_id}\n")
            conn.commit()
        run_response_script(quiz_id, message)
        conn.commit()
        conn.close()
    if delta_post4 < 15.000000:
        print(f"{t4} Script running")
        # if not bool(quiz_id):
        #     print("No Quiz ID Stored...Searching\n")
        #     with open(log_file_pathq, "r") as log_file:
        #         log_data = log_file.readlines()
        #         quiz_id = log_data[-2].strip()
        #         message = log_data[-1].strip()
        #         print(f"Quiz ID Found: {quiz_id}\n")
        # run_response_script(quiz_id, message)
        conn = sqlite3.connect('tucquiz_data.db')
        print("Database Connected\n")
        print("Checking for Quiz ID\n")
        if not bool(quiz_id):
            print("No Quiz ID Stored...Searching the database\n")
            # Get the latest quiz ID from the quiz_questions table
            print("Getting the latest quiz ID from the database\n")
            c = conn.cursor()
            c.execute("SELECT quiz_id FROM quiz_questions ORDER BY id DESC LIMIT 1")
            quiz_id = c.fetchone()[0]
            print(f"Quiz ID Found: {quiz_id}\n")
            # Get the corresponding question from the quiz_questions table
            print("Getting the corresponding question from the database\n")
            c.execute(f"SELECT question FROM quiz_questions WHERE quiz_id = '{quiz_id}'")
            question = c.fetchone()[0]
            print(f"Question Found: {question}\n")
            # with open(log_file_pathq, "r") as log_file:
            #     log_data = log_file.readlines()
            #     quiz_id = log_data[-2].strip()
            #     message = log_data[-1].strip()
            #     print(f"Quiz ID Found: {quiz_id}\n")
            conn.commit()
        run_response_script(quiz_id, message)
        conn.commit()
        conn.close()
    if delta_post5 < 15.000000:
        print(f"{t5} Script running")
        # if not bool(quiz_id):
        #     print("No Quiz ID Stored...Searching\n")
        #     with open(log_file_pathq, "r") as log_file:
        #         log_data = log_file.readlines()
        #         quiz_id = log_data[-2].strip()
        #         message = log_data[-1].strip()
        #         print(f"Quiz ID Found: {quiz_id}\n")
        # run_response_script(quiz_id, message)
        conn = sqlite3.connect('tucquiz_data.db')
        print("Database Connected\n")
        print("Checking for Quiz ID\n")
        if not bool(quiz_id):
            print("No Quiz ID Stored...Searching the database\n")
            # Get the latest quiz ID from the quiz_questions table
            print("Getting the latest quiz ID from the database\n")
            c = conn.cursor()
            c.execute("SELECT quiz_id FROM quiz_questions ORDER BY id DESC LIMIT 1")
            quiz_id = c.fetchone()[0]
            print(f"Quiz ID Found: {quiz_id}\n")
            # Get the corresponding question from the quiz_questions table
            print("Getting the corresponding question from the database\n")
            c.execute(f"SELECT question FROM quiz_questions WHERE quiz_id = '{quiz_id}'")
            question = c.fetchone()[0]
            print(f"Question Found: {question}\n")
            # with open(log_file_pathq, "r") as log_file:
            #     log_data = log_file.readlines()
            #     quiz_id = log_data[-2].strip()
            #     message = log_data[-1].strip()
            #     print(f"Quiz ID Found: {quiz_id}\n")
            conn.commit()
        run_response_script(quiz_id, message)
        conn.commit()
        conn.close()
    if delta_post6 < 15.000000:
        print(f"{t6} Script running")
        # if not bool(quiz_id):
        #     print("No Quiz ID Stored...Searching\n")
        #     with open(log_file_pathq, "r") as log_file:
        #         log_data = log_file.readlines()
        #         quiz_id = log_data[-2].strip()
        #         message = log_data[-1].strip()
        #         print(f"Quiz ID Found: {quiz_id}\n")
        # run_response_script(quiz_id, message)
        conn = sqlite3.connect('tucquiz_data.db')
        print("Database Connected\n")
        print("Checking for Quiz ID\n")
        if not bool(quiz_id):
            print("No Quiz ID Stored...Searching the database\n")
            # Get the latest quiz ID from the quiz_questions table
            print("Getting the latest quiz ID from the database\n")
            c = conn.cursor()
            c.execute("SELECT quiz_id FROM quiz_questions ORDER BY id DESC LIMIT 1")
            quiz_id = c.fetchone()[0]
            print(f"Quiz ID Found: {quiz_id}\n")
            # Get the corresponding question from the quiz_questions table
            print("Getting the corresponding question from the database\n")
            c.execute(f"SELECT question FROM quiz_questions WHERE quiz_id = '{quiz_id}'")
            question = c.fetchone()[0]
            print(f"Question Found: {question}\n")
            # with open(log_file_pathq, "r") as log_file:
            #     log_data = log_file.readlines()
            #     quiz_id = log_data[-2].strip()
            #     message = log_data[-1].strip()
            #     print(f"Quiz ID Found: {quiz_id}\n")
            conn.commit()
        run_response_script(quiz_id, message)
        conn.commit()
        conn.close()
    if delta_post7 < 15.000000:
        print(f"{t7} Script running")
        # if not bool(quiz_id):
        #     print("No Quiz ID Stored...Searching\n")
        #     with open(log_file_pathq, "r") as log_file:
        #         log_data = log_file.readlines()
        #         quiz_id = log_data[-2].strip()
        #         message = log_data[-1].strip()
        #         print(f"Quiz ID Found: {quiz_id}\n")
        # run_response_script(quiz_id, message)
        conn = sqlite3.connect('tucquiz_data.db')
        print("Database Connected\n")
        print("Checking for Quiz ID\n")
        if not bool(quiz_id):
            print("No Quiz ID Stored...Searching the database\n")
            # Get the latest quiz ID from the quiz_questions table
            print("Getting the latest quiz ID from the database\n")
            c = conn.cursor()
            c.execute("SELECT quiz_id FROM quiz_questions ORDER BY id DESC LIMIT 1")
            quiz_id = c.fetchone()[0]
            print(f"Quiz ID Found: {quiz_id}\n")
            # Get the corresponding question from the quiz_questions table
            print("Getting the corresponding question from the database\n")
            c.execute(f"SELECT question FROM quiz_questions WHERE quiz_id = '{quiz_id}'")
            question = c.fetchone()[0]
            print(f"Question Found: {question}\n")
            # with open(log_file_pathq, "r") as log_file:
            #     log_data = log_file.readlines()
            #     quiz_id = log_data[-2].strip()
            #     message = log_data[-1].strip()
            #     print(f"Quiz ID Found: {quiz_id}\n")
            conn.commit()
        run_response_script(quiz_id, message)
        conn.commit()
        conn.close()