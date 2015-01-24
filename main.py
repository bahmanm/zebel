# Copyright 2015 Bahman Movaqar <Bahman AT BahmanM.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from bot import ZebelBot
from config import conf
import time
import text
import threading

__author__ = 'Bahman Movaqar'

_BORE_TIME = int(conf['ZEBEL']['bore-time'])


def bored_zebel(bot):
    """ Checks if zebel is bored and sends a bored message in case it is!

    :param bot: zebel instance
    """
    if (int(time.time()) - bot.last_msg_ts) > _BORE_TIME:
        msg = text.bored_msg()
        bot.say(msg)
    threading.Timer(5.0, bored_zebel, [bot]).start()


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s',
                        level=logging.INFO)
    zebel = ZebelBot(conf['IRC']['server'],
                 int(conf['IRC']['port']),
                 conf['IRC']['nickname'],
                 conf['IRC']['password'],
                 conf['IRC']['channel'])
    threading.Timer(5.0, bored_zebel, [zebel]).start()
    zebel.connect().start()
