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

""" A data access layer over ElasticSearch."""
import json

from elasticsearch import Elasticsearch


__author__ = 'Bahman Movaqar'


class Quotes(object):
    """Handles different kind of search on the quote database. Currently
    it's implemented using ElasticSearch as the backend."""

    def __init__(self):
        self.client = Elasticsearch()


    def _match_query_string(self, input, support):
        """ Builds the query string for a 'match' query based on a given input
        string.

        :param input: the given input
        :param support: a list of words to support the accuracy
        :return: a query string in Elastic's syntax
        """
        qs = input
        if len(input.split(' ')) > 1:
            words = input.split(' ')
            qs = '^4 OR '.join(words) + '^4 '
            if support:
                qs += ' OR '.join(support)
        return 'text:(' + qs + ')'


    def match_fetch_general_quotes(self, input, support, minscore=0.8):
        """ Performs a 'match' query on the 'general' database.

        :param input: a free-form input string
        :param support: a list of words to support the accuracy
        :param minscore: minimum score for a result to be returned; defaults to
                0.8
        :return: an array of quotes
        """
        qs = self._match_query_string(input, support)
        q = {'min_score': minscore,
             'query': {'query_string':
                           {'default_field': 'text',
                            'query': qs}},
             'filter': {'type': {'value': 'general'}}}
        qjson = json.dumps(q)
        results = self.client.search(index='zebel_quotes', body=qjson)
        return self._extract_texts(results)


    def fuzzy_fetch_general_quotes(self, input, minscore=0.8):
        """ Performs a 'flt' query on the 'general' database.

        :param input: a free-form input string
        :param minscore: minimum score for a result to be returned; defaults to
                         0.8
        :return: an array of quotes
        """
        q = {'min_score': minscore,
             'query': {'fuzzy_like_this':
                           {'like_text': input,
                            'ignore_tf': 'true',
                            'max_query_terms': 12,
                            'prefix_length': 2,
                            'fuzziness': 1}},
             'filter': {'type': {'value': 'general'}}}
        qs = json.dumps(q)
        results = self.client.search(index='zebel_quotes', body=qs)
        return self._extract_texts(results)


    def fetch_confused_quotes(self):
        """ Performs a simple fetch on the 'confused' database.

        :return: an array of quotes
        """
        q = {'size': 50, 'filter': {'type': {'value': 'confused'}}}
        qs = json.dumps(q)
        results = self.client.search(index='zebel_quotes', body=qs)
        return self._extract_texts(results)


    def fetch_annoyed_quotes(self):
        """ Performs a simple fetch on the 'annoyed' database.

        :return: an array of quotes
        """
        q = {'size': 50, 'filter': {'type': {'value': 'annoyed'}}}
        qs = json.dumps(q)
        results = self.client.search(index='zebel_quotes', body=qs)
        return self._extract_texts(results)


    def fetch_bored_quotes(self):
        """ Performs a simple fetch on the 'bored' database.

        :return: an array of quotes
        """
        q = {'size': 50, 'filter': {'type': {'value': 'bored'}}}
        qs = json.dumps(q)
        results = self.client.search(index='zebel_quotes', body=qs)
        return self._extract_texts(results)


    def _extract_texts(self, resultset):
        """ Extracts the 'text' field from the result set.

        :param resultset: the result set returned by Elastic
        :return: an array of quotes.
        """
        hits = resultset['hits']['hits']
        return [hit['_source']['text'] for hit in hits]

