# EdgeFaaSGreengrass

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

Contents:
==========
* README              # README
* config.json         # Holds the configuration that needs to be filled by the user
* setup.py            # Setup script
* greengrasssdk/      # Greengrass SDK folder to be zipped by the script

config.json variables explained
==========

GREENGRASS_GROUP_NAME   # Name of the greengrass group you want the setup the lambda function inside. The group must already have a greengrass core.  
LAMBDA_FUNCTION_NAME    # Lambda function name you want to create. This is independent from the name of the python script.  
LAMBDA_TOPIC            # Topic name for subscription to IoT Cloud  
PARAM_DEVICE            # GPU or CPU or HETERO:FPGA,CPU  
DLA_AOCX                # DLA_AOCX for FPGA inference
PARAM_MODEL_XML         # Full path to the xml file for the optimized model  
PARAM_INPUT_SOURCE      # Full path to the input source file or /dev/video0 for webcam  
PARAM_OUTPUT_DIRECTORY  # Full path for the output directory  
PARAM_NUM_TOP_RESULTS   # Number of top results to be returned for classification sample only


Instructions
==========
1) Install aws cli
    https://docs.aws.amazon.com/cli/latest/userguide/installing.html
    After installing cli, configure it with your credentials
    https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

2) Copy the python script for the lambda function here

3) Modify the config.json values according to your needs

4) Source openvino setupvars

5) Run setup.py:
    python setup.py --lambda_file <name of your python script for lambda> --config_file config.json

6) Visit your aws console to see if your group has setup with the lambda function and resources
