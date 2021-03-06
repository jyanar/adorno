#!/bin/python3

import os
import tweepy
import random
from secrets import *
from time import gmtime, strftime
random.seed()

# == Bot configuration =========================================================

bot_username = 'adorno_ebooks'
logfile_name = bot_username + '.log'

# ==============================================================================

def get_corpus(file_name):
    """
    Reads a file into memory and parses it into a list of words that
    make up the corpus.
    """
    lines = [l.strip() for l in open(file_name, 'r', encoding='utf-8').readlines()]
    lines = list(filter(None, lines))
    return " ".join(lines).split(" ")

def construct_markov_chain(corpus):
    """
    Receives a list of words that make up the corpus and constructs
    the markov graph.
    """
    markov = {}
    for i in range(len(corpus) - 2):
        state = (corpus[i], corpus[i+1])
        transition = corpus[i+2]
        if state in markov:
            markov[state].append(transition)
        else:
            markov[state] = [transition]
    return markov

def take_step(markov_chain, current_state):
    """
    Takes a single step forward in a markov chain, moving to the next state.
    """
    transition = random.choice(markov_chain[current_state])
    return (current_state[1], transition)

def generate_text(markov_chain, num_words=30):
    """
    Takes a markov graph and generates text.
    1. Choose a random key from the markov chain.
    2. Randomly choose one of the transitions, then move to the corresponding
       state.
    3. goto 2.
    """
    output = ''
    current_state = random.choice(list(markov_chain.keys()))
    while (current_state[1][-1] in ['.', '!', '[', ']', '?', '(', ')'] or
           current_state[0][0].islower() or
	   not current_state[0][0].isalpha()):
        current_state = random.choice(list(markov_chain.keys()))
    # Now we get traverse the graph
    output += current_state[0] + ' ' + current_state[1] + ' '
    while num_words > 0:
        current_state = take_step(markov_chain, current_state)
        current_state = take_step(markov_chain, current_state)
        output += current_state[0] + ' ' + current_state[1] + ' '
        num_words -= 1
    return output

def get_140_chars(text):
    """
    Receives a string that is possibly made up of multiple sentences. Crawls
    through the string and returns however many sentences are in the range
    of 140 characters. If no suitable sentences are found (e.g., if no period
    is found in the first 140 characters) then return an empty string. Note
    that we assume that the string is longer than 140 characters.
    """
    stops = ['.', '?', '!']
    stop_found = False
    for i in range(140):
        if text[140 - i] in stops:
            stop_found = True
            break;
    if stop_found == True:
        return text[:(140 - i + 1)]
    else:
        return ''

def check_tweet(corpus, tweet):
    """
    Checks that generated tweet is good for usage, and is
    not a direct quote from the corpus.
    """
    if tweet == '' or tweet[0].islower() or len(tweet) < 5:
        return False
    # Check that tweet isn't in the corpus.
    split_tweet = tweet.split(' ')
    indices = [i for (i, word) in enumerate(corpus) if split_tweet[0] == word]
    for i in indices:
        if split_tweet == corpus[i : i+len(split_tweet)]:
            return False
    return True

def clean_tweet(tweet):
    """
    Checks that punctuation in the tweet is balanced. If it is not, relevant
    punctuation marks are removed.
    """
    parens = 0
    square = 0
    quotes = 0
    for i in range(len(tweet)):
        if tweet[i] == '(':
            parens += 1
        elif tweet[i] == ')':
            parens -= 1
        elif tweet[i] == '[':
            square += 1
        elif tweet[i] == ']':
            square -= 1
        elif tweet[i] == '“':
            quotes += 1
        elif tweet[i] == '”':
            quotes -= 1
    if parens != 0:
        tweet = ''.join(list(filter(lambda ch: ch not in '()', tweet)))
    if square != 0:
        tweet = ''.join(list(filter(lambda ch: ch not in '[]', tweet)))
    if quotes % 2 != 0:
        tweet = ''.join(list(filter(lambda ch: ch not in '“”',  tweet)))
    return tweet

def create_tweet():
    """ Constructs markov chain from corpus and generates a suitable tweet. """
    #corpus = get_corpus("/home/jorge/adorno/adorno.txt")
    corpus = get_corpus("/Users/jorge/Drive/code/Projects/adorno/adorno.txt")
    markov_chain = construct_markov_chain(corpus)
    tweet = get_140_chars(generate_text(markov_chain))
    while check_tweet(corpus, tweet) == False:
        tweet = get_140_chars(generate_text(markov_chain))
    return clean_tweet(tweet)

def send_tweet(text):
    """ Send out the text as a tweet. """
    # Twitter authentication
    auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
    auth.set_access_token(A_TOKEN, A_TOKEN_SECRET)
    api = tweepy.API(auth)

    # Send the tweet and log success or failure
    try:
        api.update_status(text)
    except tweepy.error.TweepError as e:
        log(e.message)
    else:
        log('Tweeted: ' + text)

def log(message):
    """ Log message to logfile. """
    path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    with open(os.path.join(path, logfile_name), 'a+') as f:
        t = strftime('%d %b %Y %H:%M:%S', gmtime())
        f.write("\n" + t + ' ' + message)

# ==============================================================================

if __name__ == '__main__':
    tweet_text = create_tweet()
    send_tweet(tweet_text)

