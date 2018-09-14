# Hardware-accelerated Function-as-a-Service Using AWS Greengrass

**License**

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

Hardware accelerated Function-as-a-Service (FaaS) enables cloud
developers to deploy inference functionalities on Intel® IoT edge
devices with accelerators (Intel® Processor Graphics, Intel® FPGA, and
Intel® Movidius™ Neural Compute Stick).  These functions provide a great
developer experience and seamless migration of visual analytics from
cloud to edge in a secure manner using containerized environment.
Hardware-accelerated FaaS provides the best-in-class performance by
accessing optimized deep learning libraries on Intel IoT edge devices
with accelerators.

This section describes implementation of FaaS inference samples (based
on Python\* 2.7) using [[AWS
Greengrass\*]{.underline}](https://aws.amazon.com/greengrass/) and [[AWS
Lambda\*]{.underline}](https://aws.amazon.com/lambda/) software. AWS
Lambda functions (lambdas) can be created, modified, or updated in the
cloud and can be deployed from cloud to edge using AWS Greengrass. This
document covers description of samples, pre-requisites for Intel edge
device, configuring an AWS Greengrass group, creating and packaging
lambda functions, deployment of lambdas and various options to consume
the inference output.

**Description**

**greengrass\_classification\_sample.py**

This AWS Greengrass sample classifies a video stream using
classification networks such as AlexNet and GoogLeNet and publishes
top-10 results on AWS IoT\* Cloud every second. 

**greengrass\_object\_detection\_sample\_ssd.py**

This AWS Greengrass sample detects objects in a video stream and
classifies them using single-shot multi-box detection (SSD) networks
such as SSD Squeezenet, SSD Mobilenet, and SSD300. This sample publishes
detection outputs such as class label, class confidence, and bounding
box coordinates on AWS IoT Cloud every second.

**Supported Platforms**

-   Operating system: Ubuntu\* 16.04 (64-bit)

-   Hardware: 

    -   Aaeon\* Up2 kit with integrated GPU
        ([[https://software.intel.com/en-us/blogs/2018/05/16/kits-to-accelerate-your-computer-vision-deployments]{.underline}](https://software.intel.com/en-us/blogs/2018/05/16/kits-to-accelerate-your-computer-vision-deployments)) 

    -   IEI\* 870 tank with integrated GPU
        ([[https://software.intel.com/en-us/blogs/2018/05/16/kits-to-accelerate-your-computer-vision-deployments]{.underline}](https://software.intel.com/en-us/blogs/2018/05/16/kits-to-accelerate-your-computer-vision-deployments))

    -   Any AWS Greengrass\* certified Intel® gateway with Intel Atom®,
        Intel® Core™ and Intel® Xeon® processors
        in [[https://aws.amazon.com/greengrass/faqs/]{.underline}](https://aws.amazon.com/greengrass/faqs/).
        These platforms come with an integrated GPU that can be used for
        inference.

    -   Accelerators: Intel® Arria® 10 GX 1150 FPGA Development Kit
        ([[https://www.buyaltera.com/Search/?keywords=arria+kit]{.underline}](https://www.buyaltera.com/Search/?keywords=arria+kit)) 

**Pre-requisites**

-   Download and install the OpenVINO™ toolkit
    from [[https://software.intel.com/en-us/openvino-toolkit]{.underline}](https://software.intel.com/en-us/openvino-toolkit)

-   Python\* 2.7 with opencv-python, numpy, boto3. Use sudo pip2
    install to install the packages in locations accessible by AWS
    Greengrass.

-   Download Intel\'s edge optimized models available
    at: [[https://github.com/intel/Edge-optimized-models]{.underline}](https://github.com/intel/Edge-optimized-models).
    Any custom pre-trained classification or SSD models can be used.

-   Convert the above models to Intermediate Representation (IR) using
    the Model Optimizer tool from the OpenVINO™ toolkit. Follow the
    instructions
    at: [[https://software.intel.com/en-us/articles/OpenVINO-ModelOptimizer]{.underline}](https://software.intel.com/en-us/articles/OpenVINO-ModelOptimizer).
    For CPU, models should be converted with data type FP32 and for GPU
    and FPGA, it should be with data type FP16 for the best performance.

-   To run the samples, the OpenVINO™ toolkit provides the
    pre-compiled libcpu\_extensionlibraries available in
    the \<INSTALL\_DIR\>/deployment\_tools/inference\_engine/lib/Ubuntu\_16.04/intel64/ folder:

    -   libcpu\_extension\_sse4.so -- for Intel Atom® processors

    -   libcpu\_extension\_avx2.so -- for Intel® Core™ and Intel® Xeon®
        processors.

To run the samples on other devices, it is recommended to rebuild the
libraries for a specific target to get performance gain. For build
instructions, refer to the [[Inference Engine Developer
Guide]{.underline}](https://software.intel.com/en-us/articles/OpenVINO-InferEngine#build-samples-linux).

**Configuring an AWS Greengrass group**

For each Intel\'s edge platform, you need to create a new AWS Greengrass
group and install AWS Greengrass core software to establish the
connection between cloud and edge. 

-   To create an AWS Greengrass group, follow the instructions in the
    AWS Greengrass developer guide
    at: [[https://docs.aws.amazon.com/greengrass/latest/developerguide/gg-config.html]{.underline}](https://docs.aws.amazon.com/greengrass/latest/developerguide/gg-config.html)

-   To install and configure AWS Greengrass core on edge platform,
    follow the instructions
    at [[https://docs.aws.amazon.com/greengrass/latest/developerguide/gg-device-start.html]{.underline}](https://docs.aws.amazon.com/greengrass/latest/developerguide/gg-device-start.html)

**Creating and Packaging Lambda Functions**

-   To download the AWS Greengrass Core SDK for Python\* 2.7, follow the
    steps 1-4
    at: [[https://docs.aws.amazon.com/greengrass/latest/developerguide/create-lambda.html]{.underline}](https://docs.aws.amazon.com/greengrass/latest/developerguide/create-lambda.html)

-   Replace greengrassHelloWorld.py with AWS Greengrass sample
    (greengrass\_classification\_sample.py, greengrass\_object\_detection\_sample\_ssd.py)
    and zip it with extracted AWS Greengrass SDK folders from the
    previous step into greengrass\_sample\_python\_lambda.zip. The zip
    should contain:

    -   greengrass\_common

    -   greengrass\_ipc\_python\_sdk

    -   greengrasssdk

    -   greengrass sample(greengrass\_classification\_sample.py or 
        greengrass\_classification\_sample.py)

For example:

  --- -----------------------------------------------------------------------------------------------------------------------------------------------------------
  1   zip -r greengrass\_sample\_python\_lambda.zip greengrass\_common greengrass\_ipc\_python\_sdk greengrasssdk greengrass\_object\_detection\_sample\_ssd.py
  --- -----------------------------------------------------------------------------------------------------------------------------------------------------------

-   To complete creating lambdas, follow steps 6-11
    at: [[https://docs.aws.amazon.com/greengrass/latest/developerguide/create-lambda.html]{.underline}](https://docs.aws.amazon.com/greengrass/latest/developerguide/create-lambda.html)

**Deployment of Lambdas**

**Configuring the Lambda function**

-   After creating the AWS Greengrass group and the lambda function,
    start configuring the lambda function for AWS Greengrass by
    following the steps 1-8 in AWS Greengrass developer guide
    at: [[https://docs.aws.amazon.com/greengrass/latest/developerguide/config-lambda.html]{.underline}](https://docs.aws.amazon.com/greengrass/latest/developerguide/config-lambda.html)

-   In addition to the details mentioned in step 8 of the AWS Greengrass
    developer guide, change the Memory limit to 2048MB to accommodate
    large input video streams.

-   Add the following environment variables as key-value pair when
    editing the lambda configuration and click on **Update**:

  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Key**                       **Value**
  ----------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  LD\_LIBRARY\_PATH             \<INSTALL\_DIR\>/opencv/share/OpenCV/3rdparty/lib:\
                                \<INSTALL\_DIR\>/opencv/lib:/opt/intel/opencl:\
                                \<INSTALL\_DIR\>/deployment\_tools/inference\_engine/external/cldnn/lib:\
                                \<INSTALL\_DIR\>/deployment\_tools/inference\_engine/external/mkltiny\_lnx/lib:\
                                \<INSTALL\_DIR\>/deployment\_tools/inference\_engine/lib/ubuntu\_16.04/intel64:\
                                \<INSTALL\_DIR\>/deployment\_tools/model\_optimizer/model\_optimizer\_caffe/bin:\
                                \<INSTALL\_DIR\>/openvx/lib

  PYTHONPATH                    \<INSTALL\_DIR\>/deployment\_tools/inference\_engine/python\_api/Ubuntu\_1604/python2

  PARAM\_MODEL\_XML             \<MODEL\_DIR\>/\<IR.xml\>, where \<MODEL\_DIR\> is user specified and contains IR.xml, the Intermediate Representation file from Intel Model Optimizer

  PARAM\_INPUT\_SOURCE          \<DATA\_DIR\>/input.mp4 to be specified by user. Holds both input and output data.

  PARAM\_DEVICE                 For CPU, specify \`CPU\`. For GPU, specify \`GPU\`. For FPGA, specify \`HETERO:FPGA,CPU\`.

  PARAM\_CPU\_EXTENSION\_PATH   \<INSTALL\_DIR\>/deployment\_tools/inference\_engine/lib/Ubuntu\_16.04/intel64/\<CPU\_EXTENSION\_LIB\>, where CPU\_EXTENSION\_LIB is libcpu\_extension\_sse4.so for Intel Atom® processors and libcpu\_extension\_avx2.so for Intel® Core™ and Intel® Xeon® processors.

  PARAM\_OUTPUT\_DIRECTORY      \<DATA\_DIR\> to be specified by user. Holds both input and output data.

  PARAM\_NUM\_TOP\_RESULTS      User specified for classification sample (e.g. 1 for top-1 result, 5 for top-5 results)
  -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

-   Use below LD\_LIBRARY\_PATH and additional environment variables for
    Intel® Arria® 10 GX FPGA Development Kit:

  ----------------------------------------------------------------------------------------------------------------------------
  **Key**                                  **Value**
  ---------------------------------------- -----------------------------------------------------------------------------------
  LD\_LIBRARY\_PATH                        /opt/altera/aocl-pro-rte/aclrte-linux64/board/a10\_ref/linux64/lib:\
                                           /opt/altera/aocl-pro-rte/aclrte-linux64/host/linux64/lib:\
                                           \<INSTALL\_DIR\>/opencv/share/OpenCV/3rdparty/lib:\
                                           \<INSTALL\_DIR\>/opencv/lib:/opt/intel/opencl:\
                                           \<INSTALL\_DIR\>/deployment\_tools/inference\_engine/external/cldnn/lib:\
                                           \<INSTALL\_DIR\>/deployment\_tools/inference\_engine/external/mkltiny\_lnx/lib:\
                                           \<INSTALL\_DIR\>/deployment\_tools/inference\_engine/lib/ubuntu\_16.04/intel64:\
                                           \<INSTALL\_DIR\>/deployment\_tools/model\_optimizer/model\_optimizer\_caffe/bin:\
                                           \<INSTALL\_DIR\>/openvx/lib

  DLA\_AOCX                                \<INSTALL\_DIR\>/a10\_devkit\_bitstreams/0-8-1\_a10dk\_fp16\_8x48\_arch06.aocx

  CL\_CONTEXT\_COMPILER\_MODE\_INTELFPGA   3
  ----------------------------------------------------------------------------------------------------------------------------

-   Add subscription to subscribe or publish messages from AWS
    Greengrass lambda function by following the steps 10-14 in AWS
    Greengrass developer guide
    at: [[https://docs.aws.amazon.com/greengrass/latest/developerguide/config-lambda.html]{.underline}](https://docs.aws.amazon.com/greengrass/latest/developerguide/config-lambda.html).
    The "Optional topic filter" field should be the topic mentioned
    inside the lambda function. For
    example, openvino/ssd or openvino/classification.

**Local Resources**

-   Add local resources and access privileges by following the
    instructions [[https://docs.aws.amazon.com/greengrass/latest/developerguide/access-local-resources.html]{.underline}](https://docs.aws.amazon.com/greengrass/latest/developerguide/access-local-resources.html)

-   Following are the local resources needed for various hardware (CPU,
    GPU and FPGA) options:

    -   **General (for all hardware options):**

  **Name**       **Resource Type**   **Local Path**                                                               **Access**
  -------------- ------------------- ---------------------------------------------------------------------------- ----------------
  ModelDir       Volume              \<MODEL\_DIR\> to be specified by user                                       Read-Only
  Webcam         Device              /dev/video0                                                                  Read-Only
  DataDir        Volume              \<DATA\_DIR\> to be specified by user. Holds both input and output data.     Read and Write
  OpenVINOPath   Volume              \<INSTALL\_DIR\> where INSTALL\_DIR is the OpenVINO installation directory   Read-Only

-   **GPU:**

  **Name**   **Resource Type**   **Local Path**        **Access**
  ---------- ------------------- --------------------- ----------------
  GPU        Device              /dev/dri/renderD128   Read and Write

-   **FPGA:**

  **Name**     **Resource Type**   **Local Path**             **Access**
  ------------ ------------------- -------------------------- ----------------
  FPGA         Device              /dev/acla10\_ref0          Read and Write
  FPGA\_DIR1   Volume              /opt/Intel/OpenCL/Boards   Read and Write
  FPGA\_DIR2   Volume              /etc/OpenCL/vendors        Read and Write

-   **VPU:**\
    Intel® Movidius™ Myriad™ VPU has not been validated with AWS
    Greengrass yet. This section will be updated in future releases.

**Deploy**

To deploy the lambda function to AWS Greengrass core device, select
"Deployments" on group page and follow the instructions
at: [[https://docs.aws.amazon.com/greengrass/latest/developerguide/configs-core.html]{.underline}](https://docs.aws.amazon.com/greengrass/latest/developerguide/configs-core.html).

**Output Consumption**

There are four options available for output consumption. These options
are used to report/stream/upload/store inference output at an interval
defined by the variable 'reporting\_interval' in the AWS Greengrass
samples. 

1.  AWS IoT\* Cloud Output\
    This option is enabled by default in the AWS Greengrass samples
    using a variable 'enable\_iot\_cloud\_output'.  We can use it to
    verify the lambda running on the edge device. It enables publishing
    messages to AWS IoT cloud using the subscription topic specified in
    the lambda (For example, openvino/classification for classification
    and openvino/ssd for object detection samples). For classification,
    top-1 result with class label are published to AWS IoT cloud. For
    SSD object detection, detection results such as bounding box
    co-ordinates of objects, class label, and class confidence are
    published. To view the output on AWS IoT cloud, follow the
    instructions at
    https://docs.aws.amazon.com/greengrass/latest/developerguide/lambda-check.html

2.  AWS Kinesis Streaming\
    This option enables inference output to be streamed from the edge
    device to cloud using AWS Kinesis streams when
    'enable\_kinesis\_output' is set to True. The edge devices act as
    data producers and continually push processed data to the cloud. The
    users need to set up and specify AWS Kinesis stream name, AWS
    Kinesis shard, and AWS region in the AWS Greengrass samples.

3.  Cloud Storage using AWS S3 Bucket\
    This option enables uploading and storing processed frames (in JPEG
    format) in an AWS S3\* bucket when
    the enable\_s3\_jpeg\_output variable is set to True. The users need
    to set up and specify the AWS S3 bucket name in the AWS Greengrass
    samples to store the JPEG images. The images are named using the
    timestamp and uploaded to AWS S3.

4.  Local Storage\
    This option enables storing processed frames (in JPEG format) on the
    edge device when the enable\_s3\_jpeg\_output variable is set
    to True. The images are named using the timestamp and stored in a
    directory specified by PARAM\_OUTPUT\_DIRECTORY.

Report security problems to: https://01.org/security
