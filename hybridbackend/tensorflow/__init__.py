# Copyright 2021 Alibaba Group Holding Limited. All Rights Reserved.
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
# =============================================================================

r'''HybridBackend for TensorFlow.
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from hybridbackend.libhybridbackend import buildinfo
from hybridbackend.tensorflow.embedding.scope import embedding_scope
from hybridbackend.tensorflow.feature_column.dense_features import \
  dense_features
from hybridbackend.tensorflow.framework.context import Context
from hybridbackend.tensorflow.framework.context import context
from hybridbackend.tensorflow.framework.context import context_scope
from hybridbackend.tensorflow.training.function import function
from hybridbackend.tensorflow.training.function import scope
from hybridbackend.tensorflow.wraps import wraps

from . import data
from . import distribute
from . import embedding
from . import estimator
from . import feature_column
from . import keras
from . import layers
from . import metrics
from . import saved_model
from . import training as train
