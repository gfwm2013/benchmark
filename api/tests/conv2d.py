#   Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
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

from common_import import *


class Conv2dConfig(APIConfig):
    def __init__(self):
        super(Conv2dConfig, self).__init__('conv2d')
        self.feed_spec = [
            {
                "range": [0, 1]
            },  # input
            {
                "permute": [2, 3, 1, 0]
            }  # filters
        ]

    def init_from_json(self, filename, config_id=0):
        super(Conv2dConfig, self).init_from_json(filename, config_id)
        if self.data_format == "NCHW":
            self.num_channels = self.input_shape[1]
        elif self.data_format == "NHWC":
            self.num_channels = self.input_shape[4]
        self.filter_shape = [
            self.num_filters, self.num_channels, self.filter_size[0],
            self.filter_size[1]
        ]

    def to_tensorflow(self):
        tf_config = self
        tf_config.filter_shape = [
            self.filter_size[0], self.filter_size[1], self.num_channels,
            self.num_filters
        ]
        tf_config.padding = self._convert_padding(self.padding)
        return tf_config

    def _convert_padding(self, padding):
        if isinstance(padding, str):
            return padding

        assert isinstance(padding, list)
        pad_top = padding[0] if len(padding) == 2 else padding[0]
        pad_bottom = padding[0] if len(padding) == 2 else padding[1]
        pad_left = padding[1] if len(padding) == 2 else padding[2]
        pad_right = padding[1] if len(padding) == 2 else padding[3]

        if self.data_format == "NCHW":
            return [[0, 0], [0, 0], [pad_top, pad_bottom],
                    [pad_left, pad_right]]
        elif self.data_format == "NHWC":
            return [[0, 0], [pad_top, pad_bottom], [pad_left, pad_right],
                    [0, 0]]


class PDConv2d(PaddleAPIBenchmarkBase):
    def build_program(self, config):
        with fluid.program_guard(self.main_program, self.startup_program):
            input = fluid.data(
                name='input',
                shape=config.input_shape,
                dtype=config.input_dtype,
                lod_level=0)
            filter = fluid.layers.create_parameter(
                name='filter',
                shape=config.filter_shape,
                dtype=config.input_dtype)
            input.stop_gradient = False
            result = fluid.layers.conv2d(
                input=input,
                num_filters=config.num_filters,
                filter_size=config.filter_size,
                stride=config.stride,
                padding=config.padding,
                dilation=config.dilation,
                groups=config.groups,
                param_attr='filter',
                bias_attr=False,
                use_cudnn=config.use_cudnn,
                act=None,
                data_format=config.data_format)

            self.feed_vars = [input, filter]
            self.fetch_vars = [result]
            if config.backward:
                self.append_gradients(result, [input])


class TFConv2d(TensorflowAPIBenchmarkBase):
    def build_graph(self, config):
        input = self.placeholder(
            name='input', shape=config.input_shape, dtype=config.input_dtype)
        filter = self.placeholder(
            name='filter', shape=config.filter_shape, dtype=config.input_dtype)
        if tf.__version__ <= "1.15.0":
            result = tf.nn.conv2d(
                input=input,
                filters=filter,
                strides=config.stride,
                padding=config.padding,
                data_format=config.data_format,
                dilations=config.dilation,
                use_cudnn_on_gpu=config.use_cudnn)
        else:
            result = tf.nn.conv2d(
                input=input,
                filters=filter,
                strides=config.stride,
                padding=config.padding,
                data_format=config.data_format,
                dilations=config.dilation)

        self.feed_list = [input, filter]
        self.fetch_list = [result]
        if config.backward:
            self.append_gradients(result, [input])


if __name__ == '__main__':
    test_main(PDConv2d(), TFConv2d(), config=Conv2dConfig())
