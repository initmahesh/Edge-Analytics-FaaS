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
import os
import sys
import time
import json
import ast
from argparse import ArgumentParser
from subprocess import Popen, PIPE, check_output

# Python 2 & 3 compatible input
try:
   input = raw_input
except NameError:
   pass

def build_argparser():
    parser = ArgumentParser()
    parser.add_argument("-l", "--lambda_file", help="Path to the python script with the lambda function", required=True, type=str)
    parser.add_argument("-c", "--config_file", help="Path to the configuration file", required=True, type=str)
    return parser

def generate_resource(id, name, resource_type, source_path, destination_path=None):
    resource_key = None
    if resource_type == "device":
        resource_key = "LocalDeviceResourceData"
    elif resource_type == "volume":
        resource_key = "LocalVolumeResourceData"
    else:
        print("[ERROR] Resource type: %s is invalid. Please pick 'volume' or 'device'" % resource_type)
        sys.exit(-1)

    if source_path == None:
        print("[ERROR]: Source path cannot be empty")
        sys.exit(-1)

    resource = {
        "Id" : id,
        "Name" : name,
        "ResourceDataContainer" : {
            resource_key : {
                "SourcePath" : source_path,
                "GroupOwnerSetting" : {
                    "AutoAddGroupOwner" : True,
                    "GroupOwner" : ""
                }
            }
        }
    }

    if resource_type == "volume":
        if destination_path == None:
            print("[ERROR]: Destination path cannot be empty")
            sys.exit(-1)
        resource["ResourceDataContainer"][resource_key]["DestinationPath"] = destination_path
    return resource

def role_exists(role_name):
    cmd = [
        "aws",
        "iam",
        "list-roles"
        ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))
    for role in output_json["Roles"]:
        if role["RoleName"] == role_name:
            return True
    return False

def create_role(role_name):
    role_dict = {
        "Version" : "2012-10-17",
        "Statement" : [
            {
                "Effect" : "Allow",
                "Principal" : {
                    "Service" : "lambda.amazonaws.com"
                },
                "Action" : "sts:AssumeRole"
            }
        ]
    }

    cli_input = json.dumps(role_dict)
    cmd = [
        "aws",
        "iam",
        "create-role",
        "--role-name",
        role_name,
        "--assume-role-policy-document",
        cli_input
    ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))
    return output_json["Role"]["Arn"]

def delete_role(role_name):
    cmd = [
        "aws",
        "iam",
        "delete-role",
        "--role-name",
        role_name
    ]
    output = execute_command(cmd)

def lambda_exists(lambda_name):
    cmd = [
        "aws",
        "lambda",
        "list-functions"
    ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))
    for function in output_json["Functions"]:
        if function["FunctionName"] == lambda_name:
            return True
    return False

def create_lambda(function_name, role_arn, lambda_noext, lambda_zip):
    cmd = [
        "aws",
        "lambda",
        "create-function",
        "--function-name",
        function_name,
        "--runtime",
        "python2.7",
        "--role",
        role_arn,
        "--handler",
        lambda_noext + ".function_handler",
        "--zip-file",
        "fileb://%s" % lambda_zip,
        "--publish"
    ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))
    arn = output_json["FunctionArn"]
    version = output_json["Version"]
    return (arn, version)

def delete_lambda(function_name):
    cmd = [
        "aws",
        "lambda",
        "delete-function",
        "--function-name",
        function_name
    ]
    output = execute_command(cmd)

def alias_exists(lambda_name, alias_name):
    cmd = [
        "aws",
        "lambda",
        "list-aliases",
        "--function-name",
        lambda_name
    ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))
    for alias in output_json["Aliases"]:
        if alias["Name"] == alias_name:
            return True
    return False

def create_alias(function_name, function_version, alias_name):
    cmd = [
        "aws",
        "lambda",
        "create-alias",
        "--function-name",
        function_name, "--name",
        alias_name,
        "--function-version",
        function_version
    ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))
    alias_arn = output_json["AliasArn"]
    return alias_arn

def delete_alias(function_name, alias_name):
    cmd = [
        "aws",
        "lambda",
        "delete-alias",
        "--function-name",
        function_name,
        "--name",
        alias_name
    ]
    output = execute_command(cmd)

def create_function_definition(function_definition_dict):
    cli_input = json.dumps(function_definition_dict)
    cmd = [
        "aws",
        "greengrass",
        "create-function-definition",
        "--cli-input-json",
        cli_input
    ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))
    function_definition_version_arn = output_json["LatestVersionArn"]
    return function_definition_version_arn

def create_subscription_definition(subscription_definition_dict):
    cli_input = json.dumps(subscription_definition_dict)
    cmd = [
        "aws",
        "greengrass",
        "create-subscription-definition",
        "--cli-input-json",
        cli_input
    ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))
    subscription_definition_version_arn = output_json["LatestVersionArn"]
    return subscription_definition_version_arn

def execute_command(cmd):
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        print("[ERROR]: Bad command: %s" % " ".join(cmd))
        rows, columns = check_output(['stty', 'size']).decode().split()
        print("[DEBUG]: Response: \n%s\n%s\n%s" % ("=" * int(columns), stderr, "=" * int(columns)))
        sys.exit(-1)
    return stdout

def require_openvino():
    INTEL_CVSDK_DIR = os.environ.get('INTEL_CVSDK_DIR')

    if INTEL_CVSDK_DIR is None:
        print("[ERROR]: Please source the OpenVINO setupvars script before running this."
        " For example:\nsource /opt/intel/computer_vision_sdk/bin/setupvars.sh")
        sys.exit(-1)
    if not os.path.isdir(INTEL_CVSDK_DIR):
        print("[ERROR] INTEL_CVSDK_DIR: %s does not exist." % INTEL_CVSDK_DIR)
        sys.exit(-1)
    else:
        print("[INFO]: OpenVINO found at %s" % INTEL_CVSDK_DIR)
        LD_LIBRARY_PATH = os.environ.get('LD_LIBRARY_PATH')
    return (INTEL_CVSDK_DIR, LD_LIBRARY_PATH)

def require_altera():
    ALTERA_RTE_DIR = os.environ.get("INTELFPGAOCLSDKROOT")
    if ALTERA_RTE_DIR is None:
        print("[ERROR]: Please source the Altera init_opencl script before running this."
        " For example:\nsource /opt/altera/aocl-pro-rte/aclrte-linux64/init_opencl.sh")
        sys.exit(-1)
    if not os.path.isdir(ALTERA_RTE_DIR):
        print("[ERROR] ALTERA_RTE_DIR: %s does not exist." % ALTERA_RTE_DIR)
        sys.exit(-1)
    else:
        print("[INFO]: Altera RTE found at %s" % ALTERA_RTE_DIR)
        OPENCL_VENDOR_DIR = "/etc/OpenCL/vendors"
        OPENCL_BOARD_DIR = "/opt/Intel/OpenCL/Boards"
    return (ALTERA_RTE_DIR, OPENCL_VENDOR_DIR, OPENCL_BOARD_DIR)

def get_python2_path():
    PYTHONPATH = os.environ.get('PYTHONPATH').split(":")[0]
    if "python3" in PYTHONPATH:
        PYTHONPATH = PYTHONPATH.replace("python3.6", "python2.7")
        PYTHONPATH = PYTHONPATH.replace("python3.5", "python2.7")
        PYTHONPATH = PYTHONPATH.replace("python3", "python2")
    return PYTHONPATH

def main():
    #Check if INTEL_CVSDK_DIR is exported
    INTEL_CVSDK_DIR, LD_LIBRARY_PATH = require_openvino()

    #Read PYTHONPATH set by OpenVINO and convert paths to Python 2.7
    PYTHONPATH = get_python2_path()
    print("[INFO]: PYTHONPATH is: %s" % PYTHONPATH)

    args = build_argparser().parse_args()
    lambda_base = os.path.basename(args.lambda_file)
    lambda_noext = os.path.splitext(lambda_base)[0]
    lambda_zip = lambda_noext + ".zip"

    #Zip lambda function along with greengrasssdk folder
    cmd = [
        "zip",
        "-r",
        lambda_zip,
        "greengrasssdk",
        args.lambda_file
    ]
    output = execute_command(cmd)

    #Read the configuration file
    with open(args.config_file) as f:
        config_dict = json.load(f)

    #Read parameters from the configuration file
    PARAM_DEVICE = config_dict["PARAM_DEVICE"]
    PARAM_INPUT_SOURCE = config_dict["PARAM_INPUT_SOURCE"]
    PARAM_OUTPUT_DIRECTORY = config_dict["PARAM_OUTPUT_DIRECTORY"]
    PARAM_MODEL_XML = config_dict["PARAM_MODEL_XML"]
    PARAM_NUM_TOP_RESULTS = config_dict["PARAM_NUM_TOP_RESULTS"]
    if "FPGA" in PARAM_DEVICE:
        DLA_AOCX = config_dict["DLA_AOCX"]
    LAMBDA_FUNCTION_NAME = config_dict["LAMBDA_FUNCTION_NAME"]
    MODEL_DIR = os.path.dirname(PARAM_MODEL_XML)
    OPENVINO_DIR = INTEL_CVSDK_DIR
    GREENGRASS_GROUP_NAME = config_dict["GREENGRASS_GROUP_NAME"]
    LAMBDA_TOPIC = config_dict["LAMBDA_TOPIC"]
    OUTPUT_DIR = PARAM_OUTPUT_DIRECTORY

    #Create the resource dictionary with an empty resource array
    resources = []
    resource_dict = {
        "InitialVersion" : {
            "Resources" : [
            ]
        }
    }

    #Check if Altera RTE is sourced for FPGA
    if "FPGA" in PARAM_DEVICE:
        (ALTERA_RTE_DIR, OPENCL_VENDOR_DIR, OPENCL_BOARD_DIR) = require_altera()

    #Check if group name provided exists in the cloud
    cmd = [
        "aws",
        "greengrass",
        "list-groups"
    ]
    print("[INFO]: Checking if Group: %s exists" % GREENGRASS_GROUP_NAME)
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))

    groups = output_json["Groups"]
    target_group = None
    for group in groups:
        if group["Name"] == GREENGRASS_GROUP_NAME:
            target_group = group

    if target_group == None:
        print("[ERROR] Group: %s does not exist." % GREENGRASS_GROUP_NAME)
        sys.exit(-1)

    print("[INFO]: Found the Group: %s" % GREENGRASS_GROUP_NAME)
    #Find the core definition version ARN from the group
    AWS_GROUP_ID = target_group["Id"]
    cmd = [
        "aws",
        "greengrass",
        "get-group-version",
        "--group-id",
        target_group["Id"],
        "--group-version",
        target_group["LatestVersion"]
    ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))
    CORE_DEFINITION_VERSION_ARN = output_json["Definition"]["CoreDefinitionVersionArn"]

    #Add GPU resources
    if "GPU" in PARAM_DEVICE:
        resource_dict["InitialVersion"]["Resources"].append(generate_resource("GPU", "GPU", "device", "/dev/dri/renderD128"))
        resources.append({"ResourceId":"GPU", "Permission": "rw"})

    #Add FPGA resources
    if "FPGA" in PARAM_DEVICE:
        resource_dict["InitialVersion"]["Resources"].append(generate_resource("FPGA", "FPGA", "device", "/dev/acla10_ref0"))
        resources.append({"ResourceId":"FPGA", "Permission": "rw"})

        resource_dict["InitialVersion"]["Resources"].append(generate_resource("ALTERA_RTE_DIR", "ALTERA_RTE_DIR", "volume", ALTERA_RTE_DIR, ALTERA_RTE_DIR))
        resources.append({"ResourceId":"ALTERA_RTE_DIR", "Permission": "ro"})

        resource_dict["InitialVersion"]["Resources"].append(generate_resource("OPENCL_VENDOR_DIR", "OPENCL_VENDOR_DIR", "volume", OPENCL_VENDOR_DIR, OPENCL_VENDOR_DIR))
        resources.append({"ResourceId":"OPENCL_VENDOR_DIR", "Permission": "ro"})

        resource_dict["InitialVersion"]["Resources"].append(generate_resource("OPENCL_BOARD_DIR", "OPENCL_BOARD_DIR", "volume", OPENCL_BOARD_DIR, OPENCL_BOARD_DIR))
        resources.append({"ResourceId":"OPENCL_BOARD_DIR", "Permission": "ro"})

    #Add model directory as read-only
    resource_dict["InitialVersion"]["Resources"].append(generate_resource("MODEL_DIR", "MODEL_DIR", "volume", MODEL_DIR, MODEL_DIR))
    resources.append({"ResourceId":"MODEL_DIR", "Permission": "ro"})

    #Add output directory as read-write
    resource_dict["InitialVersion"]["Resources"].append(generate_resource("OUTPUT_DIR", "OUTPUT_DIR", "volume", OUTPUT_DIR, OUTPUT_DIR))
    resources.append({"ResourceId":"OUTPUT_DIR", "Permission": "rw"})

    #Check if the input source is a camera and add device access
    if PARAM_INPUT_SOURCE.startswith("/dev/"):
        resource_dict["InitialVersion"]["Resources"].append(generate_resource("Webcam", "Webcam", "device", PARAM_INPUT_SOURCE))
        resources.append({"ResourceId":"Webcam", "Permission": "rw"})
    #Check if the input source is a file and add volume access
    else:
        DATA_DIR = os.path.dirname(PARAM_INPUT_SOURCE)
        resource_dict["InitialVersion"]["Resources"].append(generate_resource("DATA_DIR", "DATA_DIR", "volume", DATA_DIR, DATA_DIR))
        resources.append({"ResourceId":"DATA_DIR", "Permission": "ro"})

    #Add OpenVINO directory as read-only
    resource_dict["InitialVersion"]["Resources"].append(generate_resource("OPENVINO_DIR", "OPENVINO_DIR", "volume", OPENVINO_DIR, OPENVINO_DIR))
    resources.append({"ResourceId":"OPENVINO_DIR", "Permission": "ro"})

    #Create resource definition
    print("[INFO]: Creating resource definition")
    cli_input = json.dumps(resource_dict)
    cmd = [
        "aws",
        "greengrass",
        "create-resource-definition",
        "--cli-input-json",
        cli_input
    ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))
    RESOURCE_DEFINITION_VERSION_ARN = output_json["LatestVersionArn"]
    print("[INFO]: RESOURCE_DEFINITION_VERSION_ARN: %s" % RESOURCE_DEFINITION_VERSION_ARN)

    #Check if the role name exists and overwrite or create a new one
    ROLE_NAME = "%s_role" % LAMBDA_FUNCTION_NAME
    while role_exists(ROLE_NAME):
        yesno = input("Role named %s already exists in your configuration. Would you like to overwrite it? (yes/no): " % ROLE_NAME)
        if yesno == "yes":
            print("[INFO]: Deleting role: %s" % ROLE_NAME)
            delete_role(ROLE_NAME)
        else:
            ROLE_NAME = ""
            while len(ROLE_NAME) == 0:
                ROLE_NAME = input("Please enter a new role name:")

    print("[INFO]: Creating role: %s" % ROLE_NAME)
    ROLE_ARN = create_role(ROLE_NAME)
    print("[INFO]: ROLE_ARN: %s" % ROLE_ARN)

    #Check if the lambda function name exists and overwrite or create a new one
    while lambda_exists(LAMBDA_FUNCTION_NAME):
        yesno = input("Lambda function named %s already exists in your configuration. Would you like to overwrite it? (yes/no): " % LAMBDA_FUNCTION_NAME)
        if yesno == "yes":
            print("[INFO]: Deleting lambda function: %s" % LAMBDA_FUNCTION_NAME)
            delete_lambda(LAMBDA_FUNCTION_NAME)
        else:
            LAMBDA_FUNCTION_NAME = ""
            while len(LAMBDA_FUNCTION_NAME) == 0:
                LAMBDA_FUNCTION_NAME = input("Please enter a new lambda function name:")

    #Sleep for 10 seconds to make sure role is updated in the cloud
    print("[INFO]: Sleeping 10 seconds to let the role update")
    time.sleep(10.0)

    print("[INFO]: Creating lambda function: %s" % LAMBDA_FUNCTION_NAME)
    (FUNCTION_ARN, FUNCTION_VERSION) = create_lambda(LAMBDA_FUNCTION_NAME, ROLE_ARN, lambda_noext, lambda_zip)
    print("[INFO]: FUNCTION_ARN: %s" % FUNCTION_ARN)
    print("[INFO]: FUNCTION_VERSION:%s" % FUNCTION_VERSION)

    #Check if the alias name exists and overwrite or create a new one
    ALIAS_NAME = LAMBDA_FUNCTION_NAME + "_alias"
    while alias_exists(LAMBDA_FUNCTION_NAME, ALIAS_NAME):
        yesno = input("Alias named %s already exists in your configuration. Would you like to overwrite it? (yes/no): " % ALIAS_NAME)
        if yesno == "yes":
            print("[INFO]: Deleting alias %s" % ALIAS_NAME)
            delete_alias(ALIAS_NAME)
        else:
            ALIAS_NAME = ""
            while len(ALIAS_NAME) == 0:
                ALIAS_NAME = input("Please enter a new alias name:")

    print("[INFO]: Creating alias: %s" % ALIAS_NAME)
    ALIAS_ARN = create_alias(LAMBDA_FUNCTION_NAME, FUNCTION_VERSION, ALIAS_NAME)
    print("[INFO]: ALIAS ARN: %s" % ALIAS_ARN)

    #Setup the function definition

    paths = LD_LIBRARY_PATH.split(":")
    PARAM_CPU_EXTENSION_PATH = next(path for path in paths if "intel64" in path) + "/libcpu_extension_avx2.so"

    function_definition_dict = {
        "Name" : "%s_function_definition" % LAMBDA_FUNCTION_NAME,
        "InitialVersion" : {
            "Functions" : [
                {
                    "Id" : "%s_function_id" % LAMBDA_FUNCTION_NAME,
                    "FunctionArn" : FUNCTION_ARN + ":" + ALIAS_NAME,
                    "FunctionConfiguration" : {
                        "Pinned" : True,
                        "MemorySize" : 2097152,
                        "Timeout" : 30,
                        "Environment" : {
                            "AccessSysfs" : True,
                            "Variables" : {
                                "PYTHONPATH" : PYTHONPATH,
                                "PARAM_INPUT_SOURCE" : PARAM_INPUT_SOURCE,
                                "LD_LIBRARY_PATH" : LD_LIBRARY_PATH,
                                "PARAM_CPU_EXTENSION_PATH" : PARAM_CPU_EXTENSION_PATH,
                                "PARAM_DEVICE" : PARAM_DEVICE,
                                "PARAM_MODEL_XML" : PARAM_MODEL_XML,
                                "PARAM_OUTPUT_DIRECTORY" : PARAM_OUTPUT_DIRECTORY,
                                "PARAM_NUM_TOP_RESULTS" : PARAM_NUM_TOP_RESULTS
                            },
                            "ResourceAccessPolicies" : resources
                        }
                    }
                }
            ]
        }
    }

    if "FPGA" in PARAM_DEVICE:
        function = function_definition_dict["InitialVersion"]["Functions"][0]
        function["FunctionConfiguration"]["Environment"]["Variables"]["DLA_AOCX"] = DLA_AOCX
        function["FunctionConfiguration"]["Environment"]["Variables"]["CL_CONTEXT_COMPILER_MODE_INTELFPGA"] = "3"

    print("[INFO]: Creating function definition: %s" % function_definition_dict["Name"])
    FUNCTION_DEFINITION_VERSION_ARN = create_function_definition(function_definition_dict)
    print("[INFO]: FUNCTION_DEFINITION_VERSION_ARN: %s" % FUNCTION_DEFINITION_VERSION_ARN)

    #Create subscription definition
    subscription_dict = {
        "Name" : LAMBDA_FUNCTION_NAME + "_sub",
        "InitialVersion" : {
            "Subscriptions" : [
                {
                    "Id" : LAMBDA_FUNCTION_NAME + "_sub",
                    "Source" : FUNCTION_ARN + ":" + ALIAS_NAME,
                    "Subject" : LAMBDA_TOPIC,
                    "Target" : "cloud"
                }
            ]
        }
    }

    print("[INFO]: Creating subscription definition: %s" % subscription_dict["Name"])
    SUBSCRIPTION_DEFINITION_VERSION_ARN = create_subscription_definition(subscription_dict)
    print("[INFO]: SUBSCRIPTION_DEFINITION_VERSION_ARN: %s" % SUBSCRIPTION_DEFINITION_VERSION_ARN)

    #Create group version
    cmd = [
        "aws",
        "greengrass",
        "create-group-version",
        "--group-id",
        AWS_GROUP_ID,
        "--resource-definition-version-arn",
        RESOURCE_DEFINITION_VERSION_ARN,
        "--core-definition-version-arn",
        CORE_DEFINITION_VERSION_ARN,
        "--function-definition-version-arn",
        FUNCTION_DEFINITION_VERSION_ARN,
        "--subscription-definition-version-arn",
        SUBSCRIPTION_DEFINITION_VERSION_ARN
    ]

    print("[INFO]: Creating group")
    output = execute_command(cmd)
    print(output)
    print("[INFO]: Success!")

if __name__ == '__main__':
    sys.exit(main() or 0)
