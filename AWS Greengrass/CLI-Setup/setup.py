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

def generate_resource(resource_id, name, resource_type, source_path, destination_path=None):
    """ Generate a resource according to greengrass specifications."""
    resource_key = None
    if resource_type == "device":
        resource_key = "LocalDeviceResourceData"
    elif resource_type == "volume":
        resource_key = "LocalVolumeResourceData"
    else:
        print("[ERROR] Resource type: {0} is invalid. Please pick 'volume' or 'device'".format(resource_type))
        sys.exit(-1)
    
    if source_path == None:
        print("[ERROR]: Source path cannot be empty")
        sys.exit(-1)
    
    resource = {
        "Id" : resource_id,
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
    """Check if a role exists."""
    cmd = [
        "aws",
        "iam",
        "list-roles"
        ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))
    for role in output_json["Roles"]:
        if role["RoleName"].lower() == role_name.lower():
            return True
    return False

def create_role(role_name):
    """Create a role."""
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

def attached_role_policy_exists(role_name):
    """Checking if role has attached policies"""
    cmd = [
        "aws",
        "iam",
        "list-attached-role-policies",
        "--role-name",
        role_name
    ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))

    if len(output_json["AttachedPolicies"]) > 0:
    	return True

    return False
    
def delete_role(role_name):
    """Delete a role."""
    cmd = [
        "aws",
        "iam",
        "delete-role",
        "--role-name",
        role_name
    ]
    output = execute_command(cmd)

def lambda_exists(lambda_name):
    """Check if a lambda function exists."""
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
    """Create a lambda function."""
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
        "fileb://{0}".format(lambda_zip),
        "--publish"
    ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))
    arn = output_json["FunctionArn"]
    version = output_json["Version"]
    return (arn, version)

def delete_lambda(function_name):
    """Delete a lambda function."""
    cmd = [
        "aws",
        "lambda",
        "delete-function",
        "--function-name",
        function_name
    ]
    output = execute_command(cmd)

def alias_exists(lambda_name, alias_name):
    """Check if an alias exists."""
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
    """Create an alias."""
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
    """Delete an alias."""
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
    """Create a function definition."""
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
    """Create a subscription definition."""
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

def create_resource_definition(resource_dict):
    """Create a resource definition."""
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
    resource_definition_version_arn = output_json["LatestVersionArn"]
    return resource_definition_version_arn

def get_core_definition_version(group_id, group_version):
    """Get the core definition version from the group."""
    cmd = [
        "aws",
        "greengrass",
        "get-group-version",
        "--group-id",
        group_id,
        "--group-version",
        group_version
    ]
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))
    core_definition_version_arn = output_json["Definition"]["CoreDefinitionVersionArn"]
    return core_definition_version_arn

def get_group(group_name):
    """Check if a group exists."""
    cmd = [
        "aws",
        "greengrass",
        "list-groups"
    ]
    print("[INFO]: Checking if Group: {0} exists".format(group_name))
    output = execute_command(cmd)
    output_json = json.loads(output.decode("utf-8"))

    groups = output_json["Groups"]
    for group in groups:
        if group["Name"] == group_name:
            return group
    
    return None

def execute_command(cmd):
    """Execute a command."""
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        print("[ERROR]: Bad command: {0}".format(" ".join(cmd)))
        print("[DEBUG]: Response: \n{0}\n{1}\n{0}".format("=" * 50, stderr.decode("utf-8")))
        sys.exit(-1)
    return stdout

def require_openvino():
    """Check if OpenVINO's source script is sourced."""
    intel_cvsdk_dir = os.environ.get('INTEL_CVSDK_DIR')
    
    if intel_cvsdk_dir is None:
        print("[ERROR]: Please source the OpenVINO setupvars script before running this."
        " For example:\nsource /opt/intel/computer_vision_sdk/bin/setupvars.sh")
        sys.exit(-1)
    if not os.path.isdir(intel_cvsdk_dir):
        print("[ERROR] INTEL_CVSDK_DIR: {0} does not exist.".format(intel_cvsdk_dir))
        sys.exit(-1)
    else:
        print("[INFO]: OpenVINO found at {0}".format(intel_cvsdk_dir))
        ld_library_path = os.environ.get('LD_LIBRARY_PATH')
    return (intel_cvsdk_dir, ld_library_path)

def require_altera():
    """Check if altera's source script is sourced."""
    altera_rte_dir = os.environ.get("INTELFPGAOCLSDKROOT")
    if altera_rte_dir is None:
        print("[ERROR]: Please source the Altera init_opencl script before running this."
        " For example:\nsource /opt/altera/aocl-pro-rte/aclrte-linux64/init_opencl.sh")
        sys.exit(-1)
    if not os.path.isdir(altera_rte_dir):
        print("[ERROR] INTELFPGAOCLSDKROOT: {0} does not exist.".format(altera_rte_dir))
        sys.exit(-1)
    else:
        print("[INFO]: Altera RTE found at {0}".format(altera_rte_dir))
        opencl_vendor_dir = "/etc/OpenCL/vendors"
        opencl_board_dir = "/opt/Intel/OpenCL/Boards"
    return (altera_rte_dir, opencl_vendor_dir, opencl_board_dir)

def get_python2_path(intel_cvsdk_dir):
    """Read PYTHONPATH from env and convert OpenVINO python paths to Python 2.7."""
    pythonpath = os.environ.get('PYTHONPATH').split(":")
    fixed_paths = []
    for path in pythonpath:
        if intel_cvsdk_dir in path:
            path = path.replace("python3.6", "python2.7")
            path = path.replace("python3.5", "python2.7")
            path = path.replace("python3", "python2")
            fixed_paths.append(path)
    python2_path = ":".join(fixed_paths)
    return python2_path

def get_user_input(message):
    """Get non-empty input from user."""
    user_input = ""
    while len(user_input) == 0:
        user_input = input(message)
    return user_input

def main():
    # Check if INTEL_CVSDK_DIR is exported
    intel_cvsdk_dir, ld_library_path = require_openvino()
    
    # Read PYTHONPATH set by OpenVINO and convert paths to Python 2.7
    pythonpath = get_python2_path(intel_cvsdk_dir)
    print("[INFO]: PYTHONPATH is: {0}".format(pythonpath))
    
    args = build_argparser().parse_args()
    lambda_file_name = os.path.basename(args.lambda_file)
    lambda_noext = os.path.splitext(lambda_file_name)[0]
    lambda_zip = lambda_noext + ".zip"
    
    # Check if greengrasssdk exists
    if not os.path.isdir("./greengrasssdk"):
        print("[ERROR]: Folder: greengrasssdk is not found")
        sys.exit(-1)
    
    # Check if lambda file exists
    if not os.path.isfile(args.lambda_file):
        print("[ERROR]: Lambda file: {0} is not found".format(args.lambda_file))
        sys.exit(-1)
    
    # Check if config file exists
    if not os.path.isfile(args.config_file):
        print("[ERROR]: Config file: {0} is not found".format(args.config_file))
        sys.exit(-1)
    
    # Zip lambda function along with greengrasssdk folder
    cmd = [
        "zip",
        "-r",
        lambda_zip,
        "greengrasssdk",
        args.lambda_file
    ]
    output = execute_command(cmd)
    
    # Read the configuration file
    with open(args.config_file) as f:
        config_dict = json.load(f)
    
    # Read parameters from the configuration file
    param_device = config_dict["PARAM_DEVICE"]
    param_input_source = config_dict["PARAM_INPUT_SOURCE"]
    param_output_directory = config_dict["PARAM_OUTPUT_DIRECTORY"]
    param_model_xml = config_dict["PARAM_MODEL_XML"]
    param_num_top_results = config_dict["PARAM_NUM_TOP_RESULTS"]
    if "FPGA" in param_device:
        dla_aocx = config_dict["DLA_AOCX"]
    lambda_function_name = config_dict["LAMBDA_FUNCTION_NAME"]
    model_dir = os.path.dirname(param_model_xml)
    openvino_dir = intel_cvsdk_dir
    greengrass_group_name = config_dict["GREENGRASS_GROUP_NAME"]
    lambda_topic = config_dict["LAMBDA_TOPIC"]
    output_dir = param_output_directory
    
    # Check if label map file is provided.
    if "PARAM_LABELMAP_FILE" in config_dict:
        labelmap_file_name = config_dict["PARAM_LABELMAP_FILE"]

    # Create resource list and resource access list
    resources = []
    resource_accesses = []
    
    # Check if Altera RTE is sourced for FPGA
    if "FPGA" in param_device:
        (altera_rte_dir, opencl_vendor_dir, opencl_board_dir) = require_altera()
    
    # Check if group name provided exists in the cloud
    target_group = get_group(greengrass_group_name)
    if not target_group:
        print("[ERROR] Group: {0} does not exist.".format(group_name))
        sys.exit(-1)
    
    print("[INFO]: Found the Group: {0}".format(greengrass_group_name))
    aws_group_id = target_group["Id"]
    
    # Check if lambda function name is not empty. Otherwise throw an error message
    if not lambda_function_name:
        print("[ERROR]: LAMBDA_FUNCTION_NAME cannot be empty in config.json file")
        sys.exit(-1)

    # Check if lambda topic name is not empty. Otherwise throw an error message
    if not lambda_topic:
        print("[ERROR]: LAMBDA_TOPIC cannot be empty in config.json file")
        sys.exit(-1)

    # Find the core definition version ARN from the group
    core_definition_version_arn = get_core_definition_version(target_group["Id"], target_group["LatestVersion"])
    
    # Add GPU resources
    if "GPU" in param_device:
        resources.append(generate_resource("GPU", "GPU", "device", "/dev/dri/renderD128"))
        resource_accesses.append({"ResourceId":"GPU", "Permission": "rw"})
    
    # Add FPGA resources
    if "FPGA" in param_device:
        resources.append(generate_resource("FPGA", "FPGA", "device", "/dev/acla10_ref0"))
        resource_accesses.append({"ResourceId":"FPGA", "Permission": "rw"})
        
        resources.append(generate_resource("ALTERA_RTE_DIR", "ALTERA_RTE_DIR", "volume", altera_rte_dir, altera_rte_dir))
        resource_accesses.append({"ResourceId":"ALTERA_RTE_DIR", "Permission": "ro"})
        
        resources.append(generate_resource("OPENCL_VENDOR_DIR", "OPENCL_VENDOR_DIR", "volume", opencl_vendor_dir, opencl_vendor_dir))
        resource_accesses.append({"ResourceId":"OPENCL_VENDOR_DIR", "Permission": "ro"})
        
        resources.append(generate_resource("OPENCL_BOARD_DIR", "OPENCL_BOARD_DIR", "volume", opencl_board_dir, opencl_board_dir))
        resource_accesses.append({"ResourceId":"OPENCL_BOARD_DIR", "Permission": "ro"})
    
    # Add model directory as read-only
    resources.append(generate_resource("MODEL_DIR", "MODEL_DIR", "volume", model_dir, model_dir))
    resource_accesses.append({"ResourceId":"MODEL_DIR", "Permission": "ro"})
    
    # Add output directory as read-write
    resources.append(generate_resource("OUTPUT_DIR", "OUTPUT_DIR", "volume", output_dir, output_dir))
    resource_accesses.append({"ResourceId":"OUTPUT_DIR", "Permission": "rw"})
    
    # Check if the input source is a camera and add device access
    if param_input_source.startswith("/dev/"):
        resources.append(generate_resource("Webcam", "Webcam", "device", param_input_source))
        resource_accesses.append({"ResourceId":"Webcam", "Permission": "rw"})
    # Check if the input source is a file and add volume access
    else:
        data_dir = os.path.dirname(param_input_source)
        resources.append(generate_resource("DATA_DIR", "DATA_DIR", "volume", data_dir, data_dir))
        resource_accesses.append({"ResourceId":"DATA_DIR", "Permission": "ro"})
    
    # Add OpenVINO directory as read-only
    resources.append(generate_resource("OPENVINO_DIR", "OPENVINO_DIR", "volume", openvino_dir, openvino_dir))
    resource_accesses.append({"ResourceId":"OPENVINO_DIR", "Permission": "ro"})
    
    # Create the resource dictionary
    resource_dict = {
        "InitialVersion" : {
            "Resources" : resources
        }
    }
    
    # Create resource definition
    print("[INFO]: Creating resource definition")
    resource_definition_version_arn = create_resource_definition(resource_dict)
    print("[INFO]: resource_definition_version_arn: {0}".format(resource_definition_version_arn))
    
    # Check if the role name exists and overwrite or create a new one
    role_name = lambda_function_name + "_role"
    while role_exists(role_name):
        user_input = get_user_input("Role named {0} already exists in your configuration. Would you like to overwrite it? (yes/no): ".format(role_name))
        if user_input == "yes":
            #Check if role has attached policies. If yes, prompt the user to enter a new role name.
            #Otherwise, overwrite existing role.
            print("[INFO]: Checking if role {0} has attached policies".format(role_name))
            if attached_role_policy_exists(role_name):
                print("[INFO]: Role has attached policy. To overwrite, detach role policy (or) enter a new role name")
                continue
            else:
                print("[INFO]: No attached policy for role: {0}".format(role_name))
                print("[INFO]: Deleting role: {0}".format(role_name))
                delete_role(role_name)
        elif user_input == "no":
            role_name = get_user_input("Please enter a new role name: ")
        else:
            continue
    
    print("[INFO]: Creating role: {0}".format(role_name))
    role_arn = create_role(role_name)
    print("[INFO]: role_arn: {0}".format(role_arn))
    
    # Check if the lambda function name exists and overwrite or create a new one
    while lambda_exists(lambda_function_name):
        user_input = get_user_input("Lambda function named {0} already exists in your configuration. Would you like to overwrite it? (yes/no): ".format(lambda_function_name))
        if user_input == "yes":
            print("[INFO]: Deleting lambda function: {0}".format(lambda_function_name))
            delete_lambda(lambda_function_name)
        elif user_input == "no":
            lambda_function_name = get_user_input("Please enter a new lambda function name: ")
        else:
            continue
    
    # Sleep for 10 seconds to make sure role is updated in the cloud
    print("[INFO]: Sleeping 10 seconds to let the role update")
    time.sleep(10.0)
    
    print("[INFO]: Creating lambda function: {0}".format(lambda_function_name))
    (function_arn, function_version) = create_lambda(lambda_function_name, role_arn, lambda_noext, lambda_zip)
    print("[INFO]: function_arn: {0}".format(function_arn))
    print("[INFO]: function_version: {0}".format(function_version))
    
    # Check if the alias name exists and overwrite or create a new one
    alias_name = lambda_function_name + "_alias"
    while alias_exists(lambda_function_name, alias_name):
        user_input = get_user_input("Alias named {0} already exists in your configuration. Would you like to overwrite it? (yes/no): ".format(alias_name))
        if user_input == "yes":
            print("[INFO]: Deleting alias {0}".format(alias_name))
            delete_alias(alias_name)
        elif user_input == "no":
            alias_name = get_user_input("Please enter a new alias name: ")
        else:
            continue
    
    print("[INFO]: Creating alias: {0}".format(alias_name))
    alias_arn = create_alias(lambda_function_name, function_version, alias_name)
    print("[INFO]: ALIAS ARN: {0}".format(alias_arn))
    
    # Setup the function definition
    
    paths = ld_library_path.split(":")
    param_cpu_extension_path = next(path for path in paths if "intel64" in path) + "/libcpu_extension_avx2.so"
    
    function_definition_dict = {
        "Name" : lambda_function_name + "_function_definition",
        "InitialVersion" : {
            "Functions" : [
                {
                    "Id" : lambda_function_name + "_function_id",
                    "FunctionArn" : function_arn + ":" + alias_name,
                    "FunctionConfiguration" : {
                        "Pinned" : True,
                        "MemorySize" : 2097152,
                        "Timeout" : 30,
                        "Environment" : {
                            "AccessSysfs" : True,
                            "Variables" : {
                                "PYTHONPATH" : pythonpath,
                                "PARAM_INPUT_SOURCE" : param_input_source,
                                "LD_LIBRARY_PATH" : ld_library_path,
                                "PARAM_CPU_EXTENSION_PATH" : param_cpu_extension_path,
                                "PARAM_DEVICE" : param_device,
                                "PARAM_MODEL_XML" : param_model_xml,
                                "PARAM_OUTPUT_DIRECTORY" : param_output_directory,
                                "PARAM_NUM_TOP_RESULTS" : param_num_top_results,
                                "PARAM_TOPIC_NAME" : lambda_topic
                            },
                            "ResourceAccessPolicies" : resource_accesses
                        }
                    }
                }
            ]
        }
    }
    
    #If label map file path is provided in config file, add the param to dict
    if "PARAM_LABELMAP_FILE" in config_dict:
        function = function_definition_dict["InitialVersion"]["Functions"][0]
        function["FunctionConfiguration"]["Environment"]["Variables"]["PARAM_LABELMAP_FILE"] = labelmap_file_name

    if "FPGA" in param_device:
        function = function_definition_dict["InitialVersion"]["Functions"][0]
        function["FunctionConfiguration"]["Environment"]["Variables"]["DLA_AOCX"] = dla_aocx
        function["FunctionConfiguration"]["Environment"]["Variables"]["CL_CONTEXT_COMPILER_MODE_INTELFPGA"] = "3"
    
    print("[INFO]: Creating function definition: {0}".format(function_definition_dict["Name"]))
    function_definition_version_arn = create_function_definition(function_definition_dict)
    print("[INFO]: function_definition_version_arn: {0}".format(function_definition_version_arn))
    
    # Create subscription definition
    subscription_dict = {
        "Name" : lambda_function_name + "_sub",
        "InitialVersion" : {
            "Subscriptions" : [
                {
                    "Id" : lambda_function_name + "_sub",
                    "Source" : function_arn + ":" + alias_name,
                    "Subject" : lambda_topic,
                    "Target" : "cloud"
                }
            ]
        }
    }
    
    print("[INFO]: Creating subscription definition: {0}".format(subscription_dict["Name"]))
    subscription_definition_version_arn = create_subscription_definition(subscription_dict)
    print("[INFO]: subscription_definition_version_arn: {0}".format(subscription_definition_version_arn))
    
    # Create group version
    cmd = [
        "aws",
        "greengrass",
        "create-group-version",
        "--group-id",
        aws_group_id,
        "--resource-definition-version-arn",
        resource_definition_version_arn,
        "--core-definition-version-arn",
        core_definition_version_arn,
        "--function-definition-version-arn",
        function_definition_version_arn,
        "--subscription-definition-version-arn",
        subscription_definition_version_arn
    ]
    
    print("[INFO]: Creating group")
    output = execute_command(cmd)
    print(output.decode("utf-8"))
    print("[INFO]: Success!")

if __name__ == '__main__':
    sys.exit(main() or 0)
