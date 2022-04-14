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

r'''Tests for embedding columns upon PAIEV.
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import os
import unittest

from tests.tensorflow.spawn import Spawn
from tests.tensorflow.spawn import register


# pylint: disable=missing-docstring
# pylint: disable=import-outside-toplevel
def _test_get_dense_tensor(_):
  import tensorflow as tf
  from hybridbackend.tensorflow.feature_column.dense_features import \
    DenseFeatures
  from hybridbackend.tensorflow.feature_column.feature_column import \
    embedding_column
  from hybridbackend.tensorflow.feature_column.raw_categorical_column import \
    raw_categorical_column
  from hybridbackend.tensorflow.training.server_lib import device_setter
  from hybridbackend.tensorflow.training.server import Server
  from hybridbackend.tensorflow.framework.context import Context

  # Embedding variable.
  embedding_dimension = 2

  with tf.Graph().as_default():
    server = Server()
    with tf.device(device_setter()):
      # Build columns.
      Context.get().update_params(emb_backend='PAIEV')
      Context.get().update_params(emb_device='/cpu:0')
      categorical_column = raw_categorical_column('aaa')
      emb_col = embedding_column(
        categorical_column,
        embedding_dimension,
        initializer=tf.ones_initializer(tf.float32),
        combiner='mean')

      # Provide sparse input and get dense result.
      sparse_input = tf.sparse.SparseTensor(
        values=[2, 0, 1, 1],
        indices=[[0, 0], [1, 0], [1, 4], [3, 0]],
        dense_shape=[4, 5])
      embedding_lookup = DenseFeatures([emb_col])({'aaa': sparse_input})
      with tf.train.MonitoredTrainingSession(
          server.target, is_chief=True) as sess:
        return sess.run(embedding_lookup)


def _test_get_dense_tensor_sharded(_):
  import tensorflow as tf
  from hybridbackend.tensorflow.feature_column.dense_features import \
    DenseFeatures
  from hybridbackend.tensorflow.feature_column.feature_column import \
    embedding_column
  from hybridbackend.tensorflow.feature_column.raw_categorical_column import \
    raw_categorical_column
  from hybridbackend.tensorflow.training.server_lib import device_setter
  from hybridbackend.tensorflow.training.server import Server
  from hybridbackend.tensorflow.framework.context import Context

  embedding_dimension = 2

  with tf.Graph().as_default():
    server = Server()
    with tf.device(device_setter()):
      Context.get().update_params(emb_backend='PAIEV')
      Context.get().update_params(emb_device='/cpu:0')
      categorical_column = raw_categorical_column('aaa')
      emb_col = embedding_column(
        categorical_column,
        embedding_dimension,
        initializer=tf.ones_initializer(tf.float32),
        combiner='mean')
      # Provide sparse input and get dense result.
      sparse_input = tf.sparse.SparseTensor(
        values=[2, 0, 1, 1],
        indices=[[0, 0], [1, 0], [1, 4], [3, 0]],
        dense_shape=[4, 5])

      embedding_lookup = DenseFeatures([emb_col])({'aaa': sparse_input})
      with tf.train.MonitoredTrainingSession(
          server.target, is_chief=True) as sess:
        return sess.run(embedding_lookup)


def _test_get_dense_tensor_with_varscope(_):
  import tensorflow as tf
  from hybridbackend.tensorflow.feature_column.dense_features import \
    DenseFeatures
  from hybridbackend.tensorflow.feature_column.feature_column import \
    embedding_column
  from hybridbackend.tensorflow.feature_column.raw_categorical_column import \
    raw_categorical_column
  from hybridbackend.tensorflow.training.server_lib import device_setter
  from hybridbackend.tensorflow.training.server import Server
  from hybridbackend.tensorflow.framework.context import Context

  embedding_dimension = 2

  with tf.Graph().as_default():
    server = Server()
    with tf.device(device_setter()):
      partitioner = tf.min_max_variable_partitioner(
        max_partitions=2, min_slice_size=4)
      with tf.variable_scope('test', partitioner=partitioner):
        Context.get().update_params(emb_backend='PAIEV')
        Context.get().update_params(emb_device='/cpu:0')
        categorical_column = raw_categorical_column('aaa')
        emb_col = embedding_column(
          categorical_column,
          embedding_dimension,
          initializer=tf.ones_initializer(tf.float32),
          combiner='mean')
        # Provide sparse input and get dense result.
        sparse_input = tf.sparse.SparseTensor(
          values=[2, 0, 1, 1],
          indices=[[0, 0], [1, 0], [1, 4], [3, 0]],
          dense_shape=[4, 5])

        embedding_lookup = DenseFeatures([emb_col])({'aaa': sparse_input})
        with tf.train.MonitoredTrainingSession(
            server.target, is_chief=True) as sess:
          return sess.run(embedding_lookup)


def _test_embedding_column_with_optimizer(_, lr):
  import tensorflow as tf
  from hybridbackend.tensorflow.feature_column.dense_features import \
    DenseFeatures
  from hybridbackend.tensorflow.feature_column.feature_column import \
    embedding_column
  from hybridbackend.tensorflow.feature_column.raw_categorical_column import \
    raw_categorical_column
  from hybridbackend.tensorflow.training.optimizer import wraps_optimizer
  from hybridbackend.tensorflow.training.server_lib import device_setter
  from hybridbackend.tensorflow.training.server import Server
  from hybridbackend.tensorflow.framework.context import Context

  with tf.Graph().as_default():
    server = Server()
    with tf.device(device_setter()):
      Context.get().update_params(emb_backend='PAIEV')
      Context.get().update_params(emb_device='/cpu:0')
      columns = [
        embedding_column(
          raw_categorical_column('ad0'),
          dimension=20,
          initializer=tf.ones_initializer(tf.float32)),
        embedding_column(
          raw_categorical_column('ad1'),
          dimension=30,
          initializer=tf.ones_initializer(tf.float32)),
        embedding_column(
          raw_categorical_column('ad2'),
          dimension=40,
          initializer=tf.ones_initializer(tf.float32)),
        embedding_column(
          raw_categorical_column('user0'),
          dimension=20,
          initializer=tf.ones_initializer(tf.float32)),
      ]
      features = {
        'ad0': tf.constant([0, 1, 3, 2]),
        'ad1': tf.constant([1, 5, 3, 4]),
        'ad2': tf.constant([5, 2, 7, 4]),
        'user0': tf.constant([2, 5, 4, 7])
      }
      out_emb = DenseFeatures(columns, num_groups=None)(features)
      loss = tf.reduce_mean(out_emb)
      opt = wraps_optimizer(tf.train.AdagradOptimizer)(lr)
      step = tf.train.get_or_create_global_step()
      train_op = opt.minimize(loss, global_step=step)

      final_loss = None
      with tf.train.MonitoredTrainingSession(
          server.target, is_chief=True,
          hooks=[
            opt.make_session_run_hook(),
            tf.train.StopAtStepHook(last_step=100),
            tf.train.NanTensorHook(loss),
            tf.train.LoggingTensorHook(
              tensors={'loss': loss, 'step': step},
              every_n_iter=20)]) as sess:
        while not sess.should_stop():
          final_loss = sess.run(loss)
          sess.run(train_op)
      return final_loss


def _test_get_dense_tensor_disable_concat(_):
  import tensorflow as tf
  from hybridbackend.tensorflow.feature_column.dense_features import \
    DenseFeatures
  from hybridbackend.tensorflow.feature_column.feature_column import \
    embedding_column
  from hybridbackend.tensorflow.feature_column.raw_categorical_column import \
    raw_categorical_column
  from hybridbackend.tensorflow.framework.context import Context
  from hybridbackend.tensorflow.training.server_lib import device_setter
  from hybridbackend.tensorflow.training.server import Server

  Context.get().update_params(emb_enable_concat=False)

  with tf.Graph().as_default():
    server = Server()
    with tf.device(device_setter()):
      Context.get().update_params(emb_backend='PAIEV')
      Context.get().update_params(emb_device='/cpu:0')
      columns = [
        embedding_column(
          raw_categorical_column('ad0'),
          dimension=20,
          initializer=tf.ones_initializer(tf.float32)),
        embedding_column(
          raw_categorical_column('user0'),
          dimension=20,
          initializer=tf.ones_initializer(tf.float32)),
      ]
      features = {
        'ad0': tf.sparse.SparseTensor(
          values=[0, 1, 3, 2],
          indices=[[0, 0], [0, 1], [1, 0], [1, 1]],
          dense_shape=[2, 2]),
        'user0': tf.constant([2, 5, 4, 7])
      }
      embs = DenseFeatures(columns)(features)

      with tf.train.MonitoredTrainingSession(
          server.target, is_chief=True) as sess:
        return sess.run(embs)


def _test_embedding_column_with_coalescing(_, lr):
  os.environ['HYBRIDBACKEND_DEFAULT_COMM'] = 'NCCL'

  import tensorflow as tf
  from hybridbackend.tensorflow.feature_column.dense_features import \
    DenseFeatures
  from hybridbackend.tensorflow.feature_column.feature_column import \
    embedding_column
  from hybridbackend.tensorflow.feature_column.raw_categorical_column import \
    raw_categorical_column
  from hybridbackend.tensorflow.training.optimizer import wraps_optimizer
  from hybridbackend.tensorflow.training.server_lib import device_setter
  from hybridbackend.tensorflow.training.server import Server
  from hybridbackend.tensorflow.framework.context import Context

  with tf.Graph().as_default():
    server = Server()
    with tf.device(device_setter()):
      Context.get().update_params(emb_backend='PAIEV')
      Context.get().update_params(emb_device='/cpu:0')
      columns = [
        embedding_column(
          raw_categorical_column('ad0'),
          dimension=20,
          initializer=tf.ones_initializer(tf.float32)),
        embedding_column(
          raw_categorical_column('ad1'),
          dimension=30,
          initializer=tf.ones_initializer(tf.float32)),
        embedding_column(
          raw_categorical_column('ad2'),
          dimension=40,
          initializer=tf.ones_initializer(tf.float32)),
        embedding_column(
          raw_categorical_column('user0'),
          dimension=20,
          initializer=tf.ones_initializer(tf.float32)),
      ]
      features = {
        'ad0': tf.constant([0, 1, 3, 2]),
        'ad1': tf.constant([1, 5, 3, 4]),
        'ad2': tf.constant([5, 2, 7, 4]),
        'user0': tf.constant([2, 5, 4, 7])
      }
      out_emb = DenseFeatures(columns, num_groups=2)(features)
      loss = tf.reduce_mean(out_emb)
      opt = wraps_optimizer(tf.train.AdagradOptimizer)(lr)
      step = tf.train.get_or_create_global_step()
      train_op = opt.minimize(loss, global_step=step)

      final_loss = None
      with tf.train.MonitoredTrainingSession(
          server.target, is_chief=True,
          hooks=[
            opt.make_session_run_hook(),
            tf.train.StopAtStepHook(last_step=100),
            tf.train.NanTensorHook(loss),
            tf.train.LoggingTensorHook(
              tensors={'loss': loss, 'step': step},
              every_n_iter=20)]) as sess:
        while not sess.should_stop():
          final_loss = sess.run(loss)
          sess.run(train_op)
      return final_loss


def _test_embedding_column_with_function(_, lr):
  os.environ['HYBRIDBACKEND_DEFAULT_COMM'] = 'NCCL'

  import tensorflow as tf
  import hybridbackend.tensorflow as hb

  @hb.function(emb_num_groups=2, emb_backend='PAIEV', emb_device='/cpu:0')
  def train_fn():
    columns = [
      hb.feature_column.embedding_column(
        hb.feature_column.raw_categorical_column('ad0'),
        dimension=20,
        initializer=tf.ones_initializer(tf.float32)),
      hb.feature_column.embedding_column(
        hb.feature_column.raw_categorical_column('ad1'),
        dimension=30,
        initializer=tf.ones_initializer(tf.float32)),
      hb.feature_column.embedding_column(
        hb.feature_column.raw_categorical_column('ad2'),
        dimension=40,
        initializer=tf.ones_initializer(tf.float32)),
      hb.feature_column.embedding_column(
        hb.feature_column.raw_categorical_column('user0'),
        dimension=20,
        initializer=tf.ones_initializer(tf.float32)),
    ]
    features = {
      'ad0': tf.constant([0, 1, 3, 2]),
      'ad1': tf.constant([1, 5, 3, 4]),
      'ad2': tf.constant([5, 2, 7, 4]),
      'user0': tf.constant([2, 5, 4, 7])
    }
    out_emb = hb.feature_column.DenseFeatures(columns)(features)
    loss = tf.reduce_mean(out_emb)
    opt = hb.train.AdagradOptimizer(lr)
    step = tf.train.get_or_create_global_step()
    return loss, opt.minimize(loss, global_step=step)

  server = hb.train.Server()
  with tf.device(hb.train.device_setter()):
    loss, train_op = train_fn()
  final_loss = None
  with hb.train.MonitoredTrainingSession(
      server.target,
      is_chief=True,
      hooks=[
        tf.train.StopAtStepHook(last_step=100),
        tf.train.NanTensorHook(loss),
        tf.train.LoggingTensorHook(
          tensors={'loss': loss},
          every_n_iter=20)]) as sess:
    while not sess.should_stop():
      final_loss = sess.run(loss)
      sess.run(train_op)
  return final_loss


def _test_embedding_column_with_function_unique(_, lr):
  os.environ['HYBRIDBACKEND_DEFAULT_COMM'] = 'NCCL'

  import tensorflow as tf
  import hybridbackend.tensorflow as hb

  @hb.function(emb_num_groups=2, emb_backend='PAIEV',
               emb_device='/cpu:0', emb_unique={'ad0': True})
  def train_fn():
    columns = [
      hb.feature_column.embedding_column(
        hb.feature_column.raw_categorical_column('ad0'),
        dimension=20,
        initializer=tf.ones_initializer(tf.float32)),
      hb.feature_column.embedding_column(
        hb.feature_column.raw_categorical_column('ad1'),
        dimension=30,
        initializer=tf.ones_initializer(tf.float32)),
      hb.feature_column.embedding_column(
        hb.feature_column.raw_categorical_column('ad2'),
        dimension=40,
        initializer=tf.ones_initializer(tf.float32)),
      hb.feature_column.embedding_column(
        hb.feature_column.raw_categorical_column('user0'),
        dimension=20,
        initializer=tf.ones_initializer(tf.float32)),
    ]
    features = {
      'ad0': tf.constant([0, 1, 3, 2]),
      'ad1': tf.constant([1, 5, 3, 4]),
      'ad2': tf.constant([5, 2, 7, 4]),
      'user0': tf.constant([2, 5, 4, 7])
    }
    out_emb = hb.feature_column.DenseFeatures(columns)(features)
    loss = tf.reduce_mean(out_emb)
    opt = hb.train.AdagradOptimizer(lr)
    step = tf.train.get_or_create_global_step()
    return loss, opt.minimize(loss, global_step=step)

  server = hb.train.Server()
  with tf.device(hb.train.device_setter()):
    loss, train_op = train_fn()
  final_loss = None
  with hb.train.MonitoredTrainingSession(
      server.target,
      is_chief=True,
      hooks=[
        tf.train.StopAtStepHook(last_step=100),
        tf.train.NanTensorHook(loss),
        tf.train.LoggingTensorHook(
          tensors={'loss': loss},
          every_n_iter=20)]) as sess:
    while not sess.should_stop():
      final_loss = sess.run(loss)
      sess.run(train_op)
  return final_loss


def _test_get_dense_tensor_with_segment_rank(_):
  import tensorflow as tf
  import hybridbackend.tensorflow as hb

  embedding_dimension = 2

  @hb.function(emb_segment_rank={'aaa': 1}, emb_backend='PAIEV',
               emb_device='/cpu:0')
  def lookup_fn():
    sparse_input = tf.sparse.SparseTensor(
      values=[2, 0, 1, 1],
      indices=[[0, 1, 1], [0, 1, 2], [1, 1, 1], [1, 1, 2]],
      dense_shape=[4, 2, 3])
    categorical_column = hb.feature_column.raw_categorical_column('aaa')
    emb_col = hb.feature_column.embedding_column(
      categorical_column,
      embedding_dimension,
      initializer=tf.ones_initializer(tf.float32),
      combiner='mean')
    return hb.feature_column.DenseFeatures([emb_col])({'aaa': sparse_input})

  with tf.Graph().as_default():
    server = hb.train.Server()
    with tf.device(hb.train.device_setter()):
      embs = lookup_fn()
    with hb.train.MonitoredTrainingSession(
        server.target, is_chief=True) as sess:
      return sess.run(embs)


def _test_shared_embedding_column(_, lr):
  import tensorflow as tf
  from hybridbackend.tensorflow.feature_column.dense_features import \
    DenseFeatures
  from hybridbackend.tensorflow.feature_column.feature_column import \
    embedding_column
  from hybridbackend.tensorflow.feature_column.raw_categorical_column import \
    raw_categorical_column
  from hybridbackend.tensorflow.feature_column.feature_column import \
    shared_embedding_columns
  from hybridbackend.tensorflow.framework.context import Context
  from hybridbackend.tensorflow.training.optimizer import wraps_optimizer
  from hybridbackend.tensorflow.training.server_lib import device_setter
  from hybridbackend.tensorflow.training.server import Server

  with tf.Graph().as_default():
    server = Server()
    with tf.device(device_setter()):
      Context.get().update_params(emb_backend='PAIEV')
      Context.get().update_params(emb_device='/cpu:0')
      columns = [
        embedding_column(
          raw_categorical_column(key='ad1'),
          dimension=30,
          initializer=tf.ones_initializer(tf.float32)),
        embedding_column(
          raw_categorical_column(key='ad2'),
          dimension=40,
          initializer=tf.ones_initializer(tf.float32)),
      ]
      columns += shared_embedding_columns(
        [raw_categorical_column(key='ad0'),
         raw_categorical_column(key='user0')],
        dimension=20,
        initializer=tf.ones_initializer(tf.float32))
      features = {
        'ad0': tf.constant([0, 1, 3, 2]),
        'ad1': tf.constant([1, 5, 3, 4]),
        'ad2': tf.constant([5, 2, 7, 4]),
        'user0': tf.constant([2, 5, 4, 7])
      }
      out_emb = DenseFeatures(columns)(features)
      loss = tf.reduce_mean(out_emb)
      opt = wraps_optimizer(tf.train.AdagradOptimizer)(lr)
      step = tf.train.get_or_create_global_step()
      train_op = opt.minimize(loss, global_step=step)

      final_loss = None
      with tf.train.MonitoredTrainingSession(
          server.target, is_chief=True,
          hooks=[
            opt.make_session_run_hook(),
            tf.train.StopAtStepHook(last_step=100),
            tf.train.NanTensorHook(loss),
            tf.train.LoggingTensorHook(
              tensors={'loss': loss, 'step': step},
              every_n_iter=20)]) as sess:
        while not sess.should_stop():
          final_loss = sess.run(loss)
          sess.run(train_op)
      return final_loss


class EmbeddingTest(unittest.TestCase):
  '''Tests for embedding column.
  '''
  def test_get_dense_tensor(self):
    results = Spawn()(_test_get_dense_tensor)
    np.testing.assert_allclose(
      results[0],
      [[1., 1.],
       [1., 1.],
       [0., 0.],
       [1., 1.]], rtol=1e-6)

  def test_get_dense_tensor_sharded(self):
    results = Spawn(2)(_test_get_dense_tensor_sharded)
    np.testing.assert_allclose(
      results[0],
      [[1., 1.],
       [1., 1.],
       [0., 0.],
       [1., 1.]], rtol=1e-6)
    np.testing.assert_allclose(
      results[1],
      [[1., 1.],
       [1., 1.],
       [0., 0.],
       [1., 1.]], rtol=1e-6)

  def test_get_dense_tensor_with_varscope(self):
    results = Spawn(2)(_test_get_dense_tensor_with_varscope)
    np.testing.assert_allclose(
      results[0],
      [[1., 1.],
       [1., 1.],
       [0., 0.],
       [1., 1.]], rtol=1e-6)
    np.testing.assert_allclose(
      results[1],
      [[1., 1.],
       [1., 1.],
       [0., 0.],
       [1., 1.]], rtol=1e-6)

  def test_embedding_column_with_optimizer(self):
    results = Spawn(2)(
      lambda rank: _test_embedding_column_with_optimizer(rank, 0.0001),
      seed=42)
    np.testing.assert_allclose(results[0], 0.999929, rtol=1e-6)
    np.testing.assert_allclose(results[1], 0.999929, rtol=1e-6)

  def test_get_dense_tensor_disable_concat(self):
    results = Spawn()(_test_get_dense_tensor_disable_concat)
    np.testing.assert_equal(len(results[0]), 2)

  def test_embedding_column_with_coalescing(self):
    results = Spawn(2)(
      lambda rank: _test_embedding_column_with_coalescing(rank, 0.0001),
      seed=42)
    np.testing.assert_allclose(results[0], 0.999929, rtol=1e-6)
    np.testing.assert_allclose(results[1], 0.999929, rtol=1e-6)

  def test_embedding_column_function(self):
    results = Spawn(2)(
      lambda rank: _test_embedding_column_with_function(rank, 0.0001),
      seed=42)
    np.testing.assert_allclose(results[0], 0.999929, rtol=1e-6)
    np.testing.assert_allclose(results[1], 0.999929, rtol=1e-6)

  def test_embedding_column_function_unique(self):
    results = Spawn(2)(
      lambda rank: _test_embedding_column_with_function_unique(rank, 0.0001),
      seed=42)
    np.testing.assert_allclose(results[0], 0.999929, rtol=1e-6)
    np.testing.assert_allclose(results[1], 0.999929, rtol=1e-6)

  def test_get_dense_tensor_with_segment_rank(self):
    results = Spawn(2)(_test_get_dense_tensor_with_segment_rank)
    np.testing.assert_allclose(
      results[0],
      [[0., 0.],
       [1., 1.],
       [0., 0.],
       [1., 1.],
       [0., 0.],
       [0., 0.],
       [0., 0.],
       [0., 0.]], rtol=1e-6)
    np.testing.assert_allclose(
      results[1],
      [[0., 0.],
       [1., 1.],
       [0., 0.],
       [1., 1.],
       [0., 0.],
       [0., 0.],
       [0., 0.],
       [0., 0.]], rtol=1e-6)

  def test_shared_embedding_column(self):
    results = Spawn(2)(
      lambda rank: _test_shared_embedding_column(rank, 0.0001),
      seed=42)
    np.testing.assert_allclose(results[0], 0.999923, rtol=1e-6)
    np.testing.assert_allclose(results[1], 0.999923, rtol=1e-6)


# pylint: enable=missing-docstring
if __name__ == '__main__':
  register(['gpu', 'emb'], extra='deeprec')
  os.environ['CUDA_VISIBLE_DEVICES'] = '0,1'
  unittest.main()