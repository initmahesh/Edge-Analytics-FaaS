# FaaS Setup with AWS CLI

The `setup.py` script can be used to automatically configure your greengrass group in order to run FaaS on your edge platforms. The script assumes that the user provides an existing Greengrass group with a Greengrass core attached to it. The script sets up the resource accesses, environment variables, lambda function and subscription. After this, the user can go to AWS Console and deploy the group set up by the script.

This script can be run either on the edge device or on any remote device, as long as the OpenVINO installation locations match.

Prerequisites
==========
  * OpenVINO  
    The install location of OpenVINO must match the install location on the target edge device
  * Greengrass group with an attached core  
    In order to create a Greengrass group and attach a Greengrass Core to the group, please follow `Module 1` and `Module 2` here:  
https://docs.aws.amazon.com/greengrass/latest/developerguide/gg-gs.html
  * AWS CLI  
    In order to install AWS CLI:  
    https://docs.aws.amazon.com/cli/latest/userguide/installing.html  
    After installing CLI, configure it with your credentials  
    https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html  
  * AWS Greengrass Core SDK  
    The `greengrasssdk` from AWS Greengrass Core SDK must be copied to the same folder as `setup.py`  
    Follow instructions 1-4 from here:  
    https://docs.aws.amazon.com/greengrass/latest/developerguide/create-lambda.html
  * A lambda function  
    A Python script for the lambda function you want to run inside Greengrass. This script must be copied to the same folder as `setup.py`  
    Eg: `greengrass_object_detection_ssd.py`


Configuration
==========
The setup script requires the `config.json` file that has these keys. For more detailed explanation for these variables, please <blabla>  
GREENGRASS_GROUP_NAME   # Name of the greengrass group you want the setup the lambda function inside. The group must already have a greengrass core.  
LAMBDA_FUNCTION_NAME    # Lambda function name you want to create. This is independent from the name of the python script.  
LAMBDA_TOPIC            # Topic name for subscription to IoT Cloud  
PARAM_DEVICE            # GPU or CPU or HETERO:FPGA,CPU  
PARAM_MODEL_XML         # Full path to the xml file for the optimized model  
PARAM_INPUT_SOURCE      # Full path to the input source file or /dev/video0 for webcam  
PARAM_OUTPUT_DIRECTORY  # Full path for the output directory  
PARAM_NUM_TOP_RESULTS   # Number of top results to be returned  (Required for classification use case only)  
DLA_AOCX                # DLA_AOCX for FPGA inference (Required for FPGA only)
PARAM_LABELMAP_FILE     # Absolute path for the labelmap file which translates class labels to class names depending on the model in json format: {"label0":"name0", "label1":"name1"}.


Instructions
==========

1) Modify the `config.json` values according to your requirements

2) Source openvino `setupvars.sh` script:  
   For instance: `source /opt/intel/computer_vision_sdk/bin/setupvars.sh`

3) Run setup.py: 
   `python setup.py --lambda_file <name of your python script for lambda> --config_file config.json`
    
4) Visit your AWS Console to verify if your group has been configured properly

5) Deploy your Greengrass group <blabla>