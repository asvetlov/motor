# Copyright 2012-2014 MongoDB, Inc.
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
import asyncio
import time
import unittest


import test
from test.asyncio_tests import AsyncIOTestCase, asyncio_test


class MotorTailTest(AsyncIOTestCase):
    @asyncio.coroutine
    def _reset(self):
        yield from self.db.capped.drop()
        # autoIndexId catches test bugs that try to insert duplicate _id's
        yield from self.db.create_collection(
            'capped', capped=True, size=1000, autoIndexId=True)

        yield from self.db.uncapped.drop()
        yield from self.db.uncapped.insert({})

    def setUp(self):
        super(MotorTailTest, self).setUp()
        self.loop.run_until_complete(self._reset())

    def start_insertion_thread(self, pauses):
        """A thread that gradually inserts documents into a capped collection
        """
        sync_db = test.env.sync_cx.motor_test

        i = 0
        for pause in pauses:
            time.sleep(pause)
            sync_db.capped.insert({'_id': i})
            i += 1

    # Need at least one pause > 4.5 seconds to ensure we recover when
    # getMore times out
    tail_pauses = (0, 1, 0, 1, 0, 5, 0, 0)
    expected_duration = sum(tail_pauses) + 10  # Add 10 sec of fudge

    @asyncio_test(timeout=expected_duration)
    def test_tail(self):
        expected = [{'_id': i} for i in range(len(self.tail_pauses))]
        waiter = self.loop.run_in_executor(None, self.start_insertion_thread,
                                           self.tail_pauses)
        capped = self.db.capped
        results = []
        time = self.loop.time
        start = time()
        cursor = capped.find(tailable=True, await_data=True)

        while (results != expected and
               time() - start < MotorTailTest.expected_duration):

            while (yield from cursor.fetch_next):
                doc = cursor.next_object()
                results.append(doc)

            # If cursor was created while capped collection had no documents
            # (i.e., before the thread inserted first doc), it dies
            # immediately. Just restart it.
            if not cursor.alive:
                cursor = capped.find(tailable=True, await_data=True)

        yield from waiter
        self.assertEqual(expected, results)


if __name__ == '__main__':
    unittest.main()
