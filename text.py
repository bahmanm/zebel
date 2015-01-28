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
from collections import deque
import time
import itertools

import nltk
from nltk.corpus import stopwords
from nltk.tag import UnigramTagger
from nltk.corpus import wordnet
from nltk.corpus import brown
import random
import re

from config import conf
from db import Quotes


__author__ = 'Bahman Movaqar'

_db = Quotes()
_MIN_SCORE = conf['QUERY']['min-score']
_history = dict()  # A dictionary of nick->NickHistory

time_in_sec = lambda: int(round(time.time()))


class TPU:
    """ Text Processing Unit. """

    # Part-of-Speech tagger trained with all treebank sentences
    _tagger = UnigramTagger(brown.tagged_sents())

    # regex of all punctuation symbols
    re_puncts = '([%s])+' % '|'.join([r'\%s' % p for p in string.punctuation])

    # regex of all punctuation symbols that end a sentence
    re_puncts_sent = '([\.|\;|\!|\?|\-\-])+'

    # set of all English stop words all in lower case
    stopwords = [w.lower() for w in set(stopwords.words('english'))]


    @staticmethod
    def is_stopword(w):
        """ Checks if a given word is a stop word.

        :param w: the given word
        :return: True if input is stop word, False otherwise
        """
        return w.lower() in TPU.stopwords


    @staticmethod
    def sentences(text):
        """ Breaks a given input into sentences and returns them in all lower
        case.

        :param text: a free form input string
        :return: an array of sentences sans empty ones
        """
        _result = []
        for sentence in re.split(TPU.re_puncts_sent, text):
            no_punct = re.sub(TPU.re_puncts, '', sentence)
            if len(no_punct):
                _result.append(no_punct.strip().lower())
        return _result

    @staticmethod
    def tag_one(sentence):
        """ Tags a given input sentence and returns it sans stop words.

        :param sentence: the input sentence as a string
        :return: an array of binary tuples (word, type)
        """
        tuples = TPU._tagger.tag(nltk.tokenize.word_tokenize(sentence))
        _result = []
        for t in tuples:
            if len(t[0]) and not TPU.is_stopword(t[0]):
                _result.append(t)
        return _result


    @staticmethod
    def tag_all(text):
        """ Tags all the sentences in a given text.

        :param text: a free form text
        :return: an array with one element per each sentence; each element is
            an array itself of non-stop words tagged
        """
        sentences = TPU.sentences(text)
        return [TPU.tag_one(sentence) for sentence in sentences]


    @staticmethod
    def tag_type(tag):
        """ Maps a tag type from Brown/TreeBank to WordNet.

        :param tag: tag type as string
        :return: a one character type or None if non-mappable
        """
        if not tag:
            return 'v'
        elif re.match(r'VB\w*', tag):
            return 'v'
        elif re.match(r'NN\w*', tag) or re.match(r'PN', tag):
            return 'n'
        elif re.match(r'JJ\w*', tag):
            return 'a'
        elif re.match(r'RB\w*', tag):
            return 'r'
        else:
            return None


    @staticmethod
    def synonyms(word_tag):
        """ Finds all the synonyms of a given word with a given type.

        :param word_tag: a tuple (word, tag)
        :return: an array of all the synonyms of the given word, incl. the word
        """
        _type = TPU.tag_type(word_tag[1])
        root = wordnet.morphy(word_tag[0])
        if not root:
            root = word_tag[0]

        _result = set()
        _result.add(root)
        if _type:
            syn_sets = wordnet.synsets(root, pos=_type)
            for syn_set in syn_sets:
                syn = syn_set.name().split('.')[0]
                if not '_' in syn:
                    _result.add(syn)
        return list(_result)


    @staticmethod
    def all_synonyms(tagged_sentences):
        """ Finds synonyms for all the words in all the already "tagged"
        sentences.

        :param tagged_sentences: an array of tagged sentences (each as an array)
        :return: an array of arrays containing all the synonyms of all the words
        """
        _result = []
        for sent in tagged_sentences:
            for word in sent:
                _result.append(TPU.synonyms(word))
        return _result


    @staticmethod
    def tag_and_synonyms(text):
        """ Tags and finds synonyms for all the sentences in a given text.

        :param text: a free form text
        :return: an array of arrays containing all the synonyms of all the words
        """
        tagged = TPU.tag_all(text)
        return TPU.all_synonyms(tagged)


class NickHistory:
    """
    Represents a nick's history in a channel. For each nick, a certain
    number of most recent important words is stored (as a queue) and a certain
    number of timestamps for each message directed at zebel is kept.
    """

    _TS_THRESHOLD = int(conf['ZEBEL']['annoy-time'])
    _HISTORY_VALID = int(conf['ZEBEL']['history-valid'])

    def __init__(self, nick, words=()):
        self._nick = nick
        self._words = deque(words, maxlen=int(conf['ZEBEL']['history-words']))
        self.ـtimestamps = deque([], maxlen=int(conf['ZEBEL']['annoy-count']))

    def add_words(self, words):
        for w in words:
            self._words.append(w)

    def add_timestamp(self, ts):
        self.ـtimestamps.append(ts)

    def threshold_ok(self, timestamp):
        n_ts = len(self.ـtimestamps)
        if n_ts < 2:
            return True
        else:
            delta = timestamp - self.ـtimestamps[n_ts-1]
            return delta >= NickHistory._TS_THRESHOLD

    def history_valid(self, timestamp):
        """ Checks if the history words are valid for a given timestamp.

        :param timestamp: the given timestamp
        :return: True if history is valid, False otherwise (obviously!)
        """
        n_ts = len(self.ـtimestamps)
        if not n_ts:
            return True
        else:
            last = self.ـtimestamps[n_ts-1]
            return timestamp - last < NickHistory._HISTORY_VALID

    def nick(self): return self._nick

    def timestamps(self): return tuple(self.ـtimestamps)

    def words(self):
        """ Returns history words. If more than "history-valid" seconds have
        passed since the last interaction, resets history words.

        :return: a tuple of history words
        """
        if self.history_valid(time_in_sec()):
            return tuple(self._words)
        else:
            self._words.clear()
            return ()


def reply(nick, text):
    """Prepares a proper reply to an input msg.
    First it tries to find a relevant quote using 'match' search. If none is
    found it attempts a 'fuzzy' search. If 'fuzzy' fails as well, it falls back
    to a randomly selected quote from the 'confused' category.

    :param nick: IRC nick to reply to
    :param text: input msg
    :return: a reply quote
    """
    global _history
    nick_hist = _history.get(nick, NickHistory(nick))
    if nick_hist.threshold_ok(time_in_sec()):
        _reply = ''
        all_synonyms = TPU.tag_and_synonyms(text)
        important_words = list(itertools.chain(*all_synonyms))
        query = ' '.join(important_words)
        if query:
            match_results = _db.match_fetch_general_quotes(
                query, list(nick_hist.words()), _MIN_SCORE)
            if match_results:
                _reply = random.choice(match_results)
            else:
                fuzzy_results = _db.fuzzy_fetch_general_quotes(text,
                                                               _MIN_SCORE)
                if fuzzy_results:
                    _reply = random.choice(fuzzy_results)
                else:
                    _reply = random.choice(_db.fetch_confused_quotes())
        else:
            _reply = random.choice(_db.fetch_confused_quotes())
        nick_hist.add_words(important_words)
    else:
        _reply = random.choice(_db.fetch_annoyed_quotes())
    nick_hist.add_timestamp(time_in_sec())
    _history[nick] = nick_hist
    return '%s: %s' % (nick, _reply)


def bored_msg():
    """Prepares a message that shows zebel is bored.
    :return: a quote
    """
    return random.choice(_db.fetch_bored_quotes())
