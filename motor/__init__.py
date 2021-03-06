# Copyright 2011-2014 MongoDB, Inc.
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

from __future__ import unicode_literals, absolute_import

"""Motor, an asynchronous driver for MongoDB."""

import warnings

import pymongo

version_tuple = (0, 5, 'dev0')


def get_version_string():
    return '.'.join(str(v) for v in version_tuple)

version = get_version_string()
"""Current version of Motor."""

expected_pymongo_version = '2.8'
if pymongo.version != expected_pymongo_version:
    msg = (
        "Motor %s requires PyMongo at exactly version %s. "
        "You have PyMongo %s. "
        "Do pip install pymongo==2.8.0"
    ) % (version, expected_pymongo_version, pymongo.version)

    raise ImportError(msg)

from . import core, motor_gridfs, motor_py3_compat, util
from .frameworks import tornado as tornado_framework
from .metaprogramming import create_class_with_framework
from .motor_common import callback_type_error

# TODO: move this to a tornado_motor module, conditionally import here.

__all__ = ['MotorClient', 'MotorReplicaSetClient', 'Op']


def create_motor_class(cls):
    return create_class_with_framework(cls, tornado_framework, 'motor')


MotorClient = create_motor_class(core.AgnosticClient)


MotorReplicaSetClient = create_motor_class(core.AgnosticReplicaSetClient)


MotorDatabase = create_motor_class(core.AgnosticDatabase)


MotorCollection = create_motor_class(core.AgnosticCollection)


MotorCursor = create_motor_class(core.AgnosticCursor)


MotorCommandCursor = create_motor_class(core.AgnosticCommandCursor)


MotorBulkOperationBuilder = create_motor_class(core.AgnosticBulkOperationBuilder)


MotorGridFS = create_motor_class(motor_gridfs.AgnosticGridFS)


MotorGridIn = create_motor_class(motor_gridfs.AgnosticGridIn)


MotorGridOut = create_motor_class(motor_gridfs.AgnosticGridOut)


MotorGridOutCursor = create_motor_class(motor_gridfs.AgnosticGridOutCursor)


def Op(fn, *args, **kwargs):
    """Obsolete; here for backwards compatibility with Motor 0.1.

    Op had been necessary for ease-of-use with Tornado 2 and @gen.engine. But
    Motor 0.2 is built for Tornado 3, @gen.coroutine, and Futures, so motor.Op
    is deprecated.
    """
    msg = "motor.Op is deprecated, simply call %s and yield its Future." % (
        fn.__name__)

    warnings.warn(msg, DeprecationWarning, stacklevel=2)
    result = fn(*args, **kwargs)
    assert tornado_framework.is_future(result)
    return result
