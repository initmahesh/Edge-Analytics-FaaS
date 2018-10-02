"""
BSD 3-clause "New" or "Revised" license

Copyright (C) 2018 Intel Coporation.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from __future__ import print_function
import sys
import os
from argparse import ArgumentParser
import cv2
import sys
import timeit
import datetime
import iothub_client
import numpy as np
import json


from iothub_client import IoTHubClient, IoTHubClientError, IoTHubTransportProvider, IoTHubClientResult
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue
from openvino.inference_engine import IENetwork, IEPlugin
from collections import OrderedDict

reporting_interval = 1.0
PROTOCOL = IoTHubTransportProvider.MQTT
MESSAGE_TIMEOUT = 10000
INTERVAL = 1

enable_cloud_output = True
enable_local_jpeg_output = True

def build_argparser():
    parser = ArgumentParser()
    parser.add_argument("-m", "--model", help="Path to an .xml file with a trained model.", required=True, type=str)
    parser.add_argument("-i", "--input",
                        help="Path to video file or image. 'cam' for capturing video stream from camera", required=True,
                        type=str)
    parser.add_argument("-l", "--cpu_extension",
                        help="MKLDNN (CPU)-targeted custom layers.Absolute path to a shared library with the kernels "
                             "impl.", type=str, default=None)
    parser.add_argument("-pp", "--plugin_dir", help="Path to a plugin folder", type=str, default=None)
    parser.add_argument("-d", "--device",
                        help="Specify the target device to infer on; CPU, GPU, FPGA or MYRIAD is acceptable. Sample "
                             "will look for a suitable plugin for device specified (CPU by default)", default="CPU",
                        type=str)
    parser.add_argument("--labels", help="Labels mapping file", default=None, type=str)
    parser.add_argument("-nt", "--number_top", help="Number of top results", default=10, type=int)
    parser.add_argument("-o", "--connectionstring", help="connectionstring for iotedge", default="connection", type=str)
    return parser

# Handle direct method calls from IoT Hub
def device_method_callback(method_name, payload, user_context):
    global INTERVAL
    print ( "\nMethod callback called with:\nmethodName = %s\npayload = %s" % (method_name, payload) )
    device_method_return_value = DeviceMethodReturnValue()
    if method_name == "SetTelemetryInterval":
        try:
            INTERVAL = int(payload)
            # Build and send the acknowledgment.
            device_method_return_value.response = "{ \"Response\": \"Executed direct method %s\" }" % method_name
            device_method_return_value.status = 200
        except ValueError:
            # Build and send an error response.
            device_method_return_value.response = "{ \"Response\": \"Invalid parameter\" }"
            device_method_return_value.status = 400
    else:
        # Build and send an error response.
        device_method_return_value.response = "{ \"Response\": \"Direct method not defined: %s\" }" % method_name
        device_method_return_value.status = 404
    return device_method_return_value

def send_confirmation_callback(message, result, user_context):
    print ( "IoT Hub responded to message with status: %s" % (result) )

print( "Parsing Args" )
args = build_argparser().parse_args()
print( "connectionstring" )
print(args.connectionstring)

if enable_cloud_output:
    client = IoTHubClient(args.connectionstring, PROTOCOL)
    client.set_device_method_callback(device_method_callback, None)

if enable_local_jpeg_output:
    local_output_dir = os.environ.get("OUTPUT_DIR")
    assert os.path.isdir(local_output_dir), "Specified output directory doesn't exist"
    print("writing output jpeg frames to "+local_output_dir)

# Define the JSON message to send to IoT Hub.
def report_output(frame, res_json):
    json_string = json.dumps(res_json)
    print("Classification output: " + json_string)
    if enable_cloud_output:
        message = IoTHubMessage(json_string)
        print( "Sending message: %s" % message.get_string() )
        client.send_event_async(message, send_confirmation_callback, None)
    if enable_local_jpeg_output:
        now = datetime.datetime.now()
        date_prefix = str(now).replace(" ","_")
        retval = cv2.imwrite(os.path.join(local_output_dir, date_prefix + ".jpeg"), frame)


def iothub_client_object_detection_run():
    try:
        
        model_xml = args.model
        model_bin = os.path.splitext(model_xml)[0] + ".bin"
        # Plugin initialization for specified device and load extensions library if specified
        print("Initializing plugin for {} device...".format(args.device))
        plugin = IEPlugin(device=args.device, plugin_dirs=args.plugin_dir)
        if args.cpu_extension and 'CPU' in args.device:
            plugin.add_cpu_extension(args.cpu_extension)
        # Read IR
        print("Reading IR...")
        net = IENetwork.from_ir(model=model_xml, weights=model_bin)
        assert len(net.inputs.keys()) == 1, "Sample supports only single input topologies"
        assert len(net.outputs) == 1, "Sample supports only single output topologies"
        input_blob = next(iter(net.inputs))
        out_blob = next(iter(net.outputs))
        print("Loading IR to the plugin...")
        exec_net = plugin.load(network=net, num_requests=2)
        # Read and pre-process input image
        n, c, h, w = net.inputs[input_blob]
        del net
        if args.input == 'cam':
            input_stream = 0
        else:
            input_stream = args.input
            assert os.path.isfile(args.input), "Specified input file doesn't exist"

        labeldata = None
        if args.labels:
            with open(args.labels, 'r') as labels_file:
                labeldata = json.load(labels_file)

        cap = cv2.VideoCapture(input_stream)

        cur_request_id = 0
        next_request_id = 1
        last_report_time = timeit.default_timer()
        inf_seconds = 0.0
        frame_count = 0
        render_time = 0
    
        print("Starting inference in sync mode...")
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            initial_w = cap.get(3)
            initial_h = cap.get(4)
            in_frame = cv2.resize(frame, (w, h))
            in_frame = in_frame.transpose((2, 0, 1))  # Change data layout from HWC to CHW
            in_frame = in_frame.reshape((n, c, h, w))

            inf_start_time = timeit.default_timer()
            res = exec_net.infer(inputs={input_blob: in_frame})
            inf_seconds += timeit.default_timer() - inf_start_time
            frame_timestamp = datetime.datetime.now()
            frame_count += 1
            seconds_since_last_report = timeit.default_timer() - last_report_time

            # report if elapsed time exceeds threshold
            if seconds_since_last_report >= reporting_interval:
                res_json = OrderedDict()
                res_json["Candidates"] = OrderedDict()
                top_ind = np.argsort(res[out_blob], axis=1)[0, -args.number_top:][::-1]
                object_counter = 0
                for i in top_ind:
                    classlabel = labeldata[str(i)] if labeldata else str(i)
                    confidence = float(res[out_blob][0, i])
                    res_json["Candidates"][classlabel] = round(confidence, 2)
                    if object_counter == 0: 
                        cv2.putText(frame, "Top Label:"+ classlabel ,(0,30), cv2.FONT_HERSHEY_COMPLEX, 1, (125,125,0), 1)
                    object_counter += 1

                last_report_time = timeit.default_timer()
                report_output(frame, res_json)

        del exec_net
        del plugin

    except IoTHubError as iothub_error:
        print ( "Unexpected error %s from IoTHub" % iothub_error )
        return
    except KeyboardInterrupt:
        print ( "IoTHubClient sample stopped" )

iothub_client_object_detection_run()
