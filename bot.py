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

""" This is where the IRC side of Zebel the Wise is implemented."""
from irc.client import SimpleIRCClient
import re
import logging as log

from db import Quotes
import text
import time

__author__ = 'Bahman Movaqar'


class ZebelBot(SimpleIRCClient):
    """ The IRC client implementation behind Zebel."""

    def __init__(self, server, port, nick, password, target):
        super().__init__()
        self.server = server
        self.port = port
        self.nick = nick
        self.password = password
        self.target = target
        self.elastic = Quotes()
        self.last_msg_ts = int(time.time())


    def connect(self, *args, **kwargs):
        super().connect(self.server, self.port, self.nick, self.password)
        return self


    def on_welcome(self, conn, evt):
        conn.join(self.target)


    def on_join(self, conn, evt):
        if evt.source.nick == self.nick:
            self._update_ts()
            conn.privmsg(
                self.target,
                '\001ACTION the wise has just entered the channel.\001')


    def on_pubmsg(self, conn, evt):
        self._update_ts()
        full_msg = evt.arguments[0]
        pattern = '%s[\:\,\>]\s+(.+)' % self.nick
        match = re.match(pattern, full_msg)
        if match:
            msg = match.group(1)
            sender = evt.source.nick
            log.info('MSG %s > %s' % (sender, full_msg))
            conn.privmsg(self.target, text.reply(sender, msg))


    def say(self, msg):
        self._update_ts()
        self.connection.privmsg(self.target, msg)


    def _update_ts(self):
        self.last_msg_ts = int(time.time())