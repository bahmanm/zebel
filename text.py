# Copyright 2015 Bahman Movaqar <Bahman AT BahmanM.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" The text processing heart of zebel; this is HAL's brain. """
import string
from itertools import chain
from collections import deque
import time

import nltk
from nltk.corpus import stopwords
from nltk.collocations import BigramCollocationFinder
import random
import re

from config import conf
from db import Quotes


__author__ = 'Bahman Movaqar'

_db = Quotes()
_MIN_SCORE = conf['QUERY']['min-score']
# regex for matching all punctuations
_PUNCT_RE = '([' + '|'.join([r'\%s' % p for p in string.punctuation]) + '])+'
_history = dict() # A dictionary of nick->NickHistory


def time_in_sec():
    return int(round(time.time()))


class NickHistory:
    """
    Represents a nick's history in a channel. For each nick, a certain
    number of most recent important words is stored (as a queue) and a certain
    number of timestamps for each message directed at zebel is kept.
    """

    _TS_THRESHOLD = int(conf['ZEBEL']['annoy-time'])

    def __init__(self, nick, words=()):
        self.nick = nick
        self.words = deque(words, maxlen=int(conf['ZEBEL']['history-words']))
        self.timestamps = deque([], maxlen=int(conf['ZEBEL']['annoy-count']))

    def add_words(self, words):
        for w in words:
            self.words.append(w)

    def add_timestamp(self, ts):
        self.timestamps.append(ts)

    def threshold_ok(self):
        if len(self.timestamps) < 3:
            return True
        delta = self.timestamps[2] - self.timestamps[0]
        return delta >= NickHistory._TS_THRESHOLD


def _count_words(input):
    """Counts the number of words in a given input string.

    :param input: the given free-form input string
    :return: number of words
    """
    return len(nltk.tokenize.word_tokenize(input))


def _sanitise(input):
    """ Sanitises an input string by removing punctuations and stop words.

    :param input: the given input string
    :return: an array of important words in the given input
    """
    trivials = ['what', 'who', 'why', 'when', 'how', 'me', 'you', 'his', 'her',
                'they', 'their', 'your', 'mine', 'she', 'he', 'it', 'its',
                "'re", "'s", "it's", 'know', 'tell', 'say', 'sure', "'m", "'ll",
                "'t"]
    def _keep(w):
        return (w not in stop_words) and (w not in string.punctuation) \
               and (not w.isnumeric()) and (len(w) > 1)
    def _no_punct(w):
        return re.sub(_PUNCT_RE, '', w)

    stop_words = [w.lower() for w in set(stopwords.words('english') + trivials)]
    words = [_no_punct(w.lower()) for w in nltk.tokenize.word_tokenize(input)]
    return [w for w in words if _keep(w)]


def _n_important_words(n_words):
    """ Calculates the number of most important words based on a given number of
     (sanitised) words. It's no rocket science. Just a dumb if-else.

    :param n_words: the given number of words
    :return: number of most important words
    """
    if 0 < n_words <= 5:
        return 3
    elif 6 <= n_words <= 10:
        return 4
    else:
        return 5


def _important_words(words):
    """ Extracts important words out of a given array of words.

    :param words: the given array of words; e.g. out of _filter_stopwords()
    :return: an array of most important words
    """
    if len(words) < 2:
        return words
    n = _n_important_words(len(words))
    finder = BigramCollocationFinder.from_words(words)
    all_words = list(
        chain.from_iterable(
            [[w] * n for (w, n) in finder.word_fd.most_common()]))
    if len(all_words) <= n:
        return all_words
    else:
        return all_words[0:n]


def _build_query(input):
    """Builds the query string of the most important words based on a given raw
    input.

    :param input: the given input
    :return: a tuple;
        0 -> query string of the most important words in the given input
        1 -> a list of important words
    """
    query = ''
    query_words = _sanitise(input)
    important_words = []
    if len(query_words) >= 2:
        important_words = _important_words(query_words)
        query = ' '.join(important_words)
    else:
        query = ' '.join(query_words)
    return (query, important_words)


def reply(nick, input):
    """Prepares a proper reply to an input msg.
    First it tries to find a relevant quote using 'match' search. If none is
    found it attempts a 'fuzzy' search. If 'fuzzy' fails as well, it falls back
    to a randomly selected quote from the 'confused' category.

    :param nick: IRC nick to reply to
    :param input: input msg
    :return: a reply quote
    """
    global _history
    nick_hist = _history.get(nick, NickHistory(nick))
    nick_hist.add_timestamp(time_in_sec())
    if nick_hist.threshold_ok():
        _reply = ''
        (query, important_words) = _build_query(input)
        if query:
            match_results = _db.match_fetch_general_quotes(
                query, list(nick_hist.words), _MIN_SCORE)
            if match_results:
                _reply = random.choice(match_results)
            else:
                fuzzy_results = _db.fuzzy_fetch_general_quotes(query, _MIN_SCORE)
                if fuzzy_results:
                    _reply = random.choice(fuzzy_results)
                else:
                    _reply = random.choice(_db.fetch_confused_quotes())
        else:
            _reply = random.choice(_db.fetch_confused_quotes())
        nick_hist.add_words(important_words)
    else:
        _reply = random.choice(_db.fetch_annoyed_quotes())
    _history[nick] = nick_hist
    return '%s: %s' % (nick, _reply)


def bored_msg():
    """Prepares a message that shows zebel is bored.
    :return: a quote
    """
    return random.choice(_db.fetch_bored_quotes())
