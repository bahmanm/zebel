# Introduction #
"ZEBEL" (pronounced like "rebel") is an intelligent IRC bot.

_Its primary goal is gathering intelligence and secrets through contextual
analysis of the conversations on IRC._ I almost got you! Didn't I!? :-)

Jokes aside, Zebel is a simple IRC bot that whenever you talk to him, tries
to reply with a relatively relevant message.
If you're curious, drop by in _#zebel_ on _irc.freenode.org_ and have a chat
with him.

# Design #
When someone in an IRC channel, talks to Zebel, e.g. sends out a public message
like `zebel: greetings`, Zebel tries to make sense of your message as below:

  1. It first sanitises the message; removing stop words, punctuations and 
     unimportant words.
  2. The sanitised text is fed into natural language processing to find the most
     important words in the text.
  3. Performs a full-text search on the DB for the most important words.
  4. If anything relevant enough is found, returns it.
  5. If there's no relevant enough answer in the database, it tries a fuzzy
     search for the same words.
  6. If fuzzy search finds a good enough answer, it is returned.
  7. Even if fuzzy search can't help, Zebel simply gives up on finding a
     reasonable answer and instead just picks up a message from the "confused"
     category.


# Implementation #
Zebel, developed with Python 3.4+, is composed of 3 main parts:

 1. The IRC client ([irc library](https://bitbucket.org/jaraco/irc/))
 2. The database ([ElasticSearch](http://elasticsearch.org/))
 3. The text and natural language processing unit ([nltk library](http://nltk.org/))

# How To Run #
If you plan to run your own Zebel instance:
  
  1. Install Python 3.4
  2. Create a virtual environment for Zebel, e.g. `pyvenv-3.4 .venv`
  3. Activate the venv, e.g. `source .venv/bin/activate`
  4. Clone Zebel.
  5. Install required packages, e.g. `cd zebel && pip install -r requirements.txt`
  6. Install nltk data, e.g. `python -m nltk.downloader all`. Warning: this
     downloads quite a bit of data.
  7. Edit `zebel.ini` to your needs.
  8. Install and run [ElasticSearch](http://elasticsearch.org/).
  9. Import Zebel's quotes and messages into ElasticSearch, 
     e.g. `data/drop-import-all.sh`
  10. Run Zebel, e.g. `cd zebel && python main.py`

# Notes #
* The bot named "vandusen" in #chicken on FreeNode was a great inspiration to me.