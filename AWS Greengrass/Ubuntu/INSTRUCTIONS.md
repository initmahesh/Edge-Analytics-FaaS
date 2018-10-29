Hardware-accelerated Function-as-a-Service Using AWS Greengrass
=================

Table of contents
=================

<!-- Table of contents -->
   * [Introduction](#introduction)
   * [Supported Platforms](#supported-platforms)
   * [Pre-requisites for Intel Edge Devices](#pre-requisites-for-intel-edge-devices)
   * [Description of Samples](#description-of-samples)
   * [Converting Deep Learning Models](#converting-deep-learning-models)
   * [Configuring a Greengrass Group](#configuring-a-greengrass-group)
   * [Creating and Packaging Lambda Functions](#creating-and-packaging-lambda-functions)
   * [Deployment of Lambda Functions](#deployment-of-lambda-functions)
      * [Configuring the Lambda Function](#configuring-the-lambda-function)
      * [Local Resources](#local-resources)
      * [Deployment](#deployment)
   * [Output Consumption](#output-consumption)
   * [References](#references)
<!-- Table of contents -->

Introduction
=================

Hardware accelerated Function-as-a-Service (FaaS) enables cloud developers to deploy inference functionalities [1] on Intel IoT edge devices with accelerators (Integrated GPU, FPGA, and Movidius).  These functions provide a great developer experience and seamless migration of visual analytics from cloud to edge in a secure manner using containerized environment. Hardware-accelerated FaaS provides the best-in-class performance by accessing optimized deep learning libraries on Intel IoT edge devices with accelerators.

This document describes implementation of FaaS inference samples (based on Python 2.7) using AWS Greengrass [1] and lambdas [2]. These lambdas can be created, modified, or updated in the cloud and can be deployed from cloud to edge using AWS Greengrass. This document covers description of samples, pre-requisites for Intel edge device, configuring a Greengrass group, creating and packaging lambda functions, deployment of lambdas and various options to consume the inference output.

Supported Platforms
=================

* Operating System: Ubuntu 16.04
* Hardware:
  * Aaeon Up2 kit with integrated GPU (https://software.intel.com/en-us/blogs/2018/05/16/kits-to-accelerate-your-computer-vision-deployments)
  * IEI 870 tank with integrated GPU (https://software.intel.com/en-us/blogs/2018/05/16/kits-to-accelerate-your-computer-vision-deployments)
  * Any Greengrass certified Intel gateway with Atom Apollo Lake processor, Core Skylake and Xeon Skylake in https://aws.amazon.com/greengrass/faqs/. These platforms come with an integrated GPU that can be used for inference.
  * Accelerators: Arria10 1150 FPGA (https://www.buyaltera.com/Search/?keywords=arria+kit)


Pre-requisites for Intel Edge Devices
=================

* Download and install OpenVINO R3 Toolkit from https://software.intel.com/en-us/openvino-toolkit
* For configuring GPU to use OpenVINO, follow the instructions under section “Additional Installation Steps for Processor Graphics (GPU)” at
https://software.intel.com/en-us/articles/OpenVINO-Install-Linux#inpage-nav-4-1
* Python 2.7 with opencv-python, numpy, boto3 (use the below commands to install the packages)
    ```
    sudo apt-get install python-pip
    sudo pip2 install opencv-python numpy boto3
    ```

Description of Samples
=================

The Greengrass samples are part of OpenVINO release. They are located at <INSTALL_DIR>/deployment_tools/inference_engine/samples/python_samples/greengrass_samples, where <INSTALL_DIR> refers to OpenVINO installation directory throughout this document. By default, <INSTALL_DIR> is /opt/intel/computer_vision_sdk.

We provide the following Greengrass samples:
* greengrass_classification_sample.py

    This Greengrass sample classifies a video stream using classification networks such as AlexNet and GoogLeNet and publishes class labels, class names, confidence values for top-10 candidates along with frame id, inference fps and frame timestamp on AWS IoT Cloud every second.

* greengrass_object_detection_sample_ssd.py

    This Greengrass sample detects objects in a video stream and classifies them using single-shot multi-box detection (SSD) networks such as SSD Squeezenet, SSD Mobilenet, and SSD300. This sample publishes detection outputs such as class labels, class names, confidence values, bounding box coordinates for each detection along with frame id, inference fps and frame timestamp on AWS IoT Cloud every second.

Converting Deep Learning Models
=================

Downloading Sample Models
-------------------

For classification, download the BVLC Alexnet model (deploy.prototxt and bvlc_alexnet.caffemodel) as an example from https://github.com/BVLC/caffe/tree/master/models/bvlc_alexnet. Any custom pre-trained classification models can be used with the classification sample.

For object detection, download Intel Edge optimized models available at https://github.com/intel/Edge-optimized-models. These models are provided as an example, but any custom pre-trained SSD models can be used with the object detection sample. 

Setting up Model Optimizer
---------------------

Below steps describe installing pre-requisites and setting up environment variables for Model Optimizer:

~~~~~~~~~~~~~~~~~~~~~~~~~~~
source <INSTALL_DIR>/bin/setupvars.sh
cd <INSTALL_DIR>/deployment_tools/model_optimizer/install_prerequisites
sudo –E ./install_prerequisites.sh
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Model Optimizer uses Python 3.5, whereas Greengrass samples use Python 2.7. In order for Model Optimizer not to influence the global Python configuration, activate a virtual environment as below:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
cd <INSTALL_DIR>/deployment_tools/model_optimizer
source venv/bin/activate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Running Model Optimizer
--------------------

For converting deep learning models to Intermediate Representation (IR) using Model Optimizer, follow the instructions at: https://software.intel.com/en-us/articles/OpenVINO-ModelOptimizer. For example, for above models use the following commands.

For CPU, models should be converted with data type FP32 and for GPU/FPGA, it should be with data type FP16 for the best performance.

For classification using BVLC Alexnet model,

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
python3 mo.py --framework caffe --input_model <model_location>/bvlc_alexnet.caffemodel --input_proto <model_location>/deploy.prototxt --data_type <data_type> --output_dir <output_dir> --input_shape [1,3,227,227]
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For object detection using SqueezeNetSSD-5Class model,

~~~~~~~~~~~~~~~~~~~~~~~~~~~
python3 mo.py --framework caffe --input_model <model_location>/SqueezeNetSSD-5Class.caffemodel --input_proto <model_location>/SqueezeNetSSD-5Class.prototxt --data_type <data_type> --output_dir <output_dir>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

where <model_location> is the location where the user downloaded the models, <data_type> is FP32 or FP16 depending on target device, and <output_dir> is the directory where the user wants to store the IR. IR contains .xml format corresponding to the network structure and .bin format corresponding to weights. This .xml should be passed to <PARAM_MODEL_XML> mentioned in Section 8.1. In the BVLC Alexnet model, the prototxt defines the input shape with batch size 10 by default. In order to use any other batch size, the entire input shape needs to be provided as an argument to the model optimizer. For example, if you want to use batch size 1, you can provide “--input_shape [1,3,227,227]”.

To deactivate the virtual environment after converting the model, use the below command:

`deactivate`

Configuring a Greengrass group
=================

For each Intel edge platform, we need to create a new Greengrass group and install Greengrass core software to establish the connection between cloud and edge.
* To create a Greengrass group, follow the instructions in the AWS Greengrass developer guide at: https://docs.aws.amazon.com/greengrass/latest/developerguide/gg-config.html
* To install and configure Greengrass core on edge platform, follow the instructions at https://docs.aws.amazon.com/greengrass/latest/developerguide/gg-device-start.html

Creating and Packaging Lambda Functions
=================

* To download the AWS Greengrass Core SDK for python 2.7, follow the steps 1-4 at: https://docs.aws.amazon.com/greengrass/latest/developerguide/create-lambda.html
* Replace greengrassHelloWorld.py with Greengrass sample (greengrass_classification_sample.py/greengrass_object_detection_sample_ssd.py) and zip it with extracted Greengrass SDK folders from the previous step into greengrass_sample_python_lambda.zip. The zip should contain:
  * greengrasssdk
  * greengrass sample(greengrass_classification_sample.py or  greengrass_object_detection_sample_ssd.py)

    For example:
    ```
    zip -r greengrass_sample_python_lambda.zip greengrasssdk greengrass_object_detection_sample_ssd.py
    ```
* To complete creating lambdas, follow steps 6-11 at: https://docs.aws.amazon.com/greengrass/latest/developerguide/create-lambda.html
* In step 9(a), while uploading the zip file, make sure to name the handler as below depending on the Greengrass sample you are using:

  `greengrass_object_detection_sample_ssd.function_handler` (or)

  `greengrass_classification_sample.function_handler`

Deployment of Lambda Functions
=================

Configuring the Lambda Function
-----------

* After creating the Greengrass group and the lambda function, start configuring the lambda function for AWS Greengrass by following the steps 1-8 in AWS Greengrass developer guide at: https://docs.aws.amazon.com/greengrass/latest/developerguide/config-lambda.html
* In addition to the details mentioned in step 8 of the AWS Greengrass developer guide, change the Memory limit to 2048MB to accommodate large input video streams.  
* Add the following environment variables as key-value pair when editing the lambda configuration and click on update:

    Key | Value
    :------------- | :-------------
    LD_LIBRARY_PATH |<INSTALL_DIR>/opencv/share/OpenCV/3rdparty/lib:<INSTALL_DIR>/opencv/lib:/opt/intel/opencl:<INSTALL_DIR>/deployment_tools/inference_engine/external/cldnn/lib:<INSTALL_DIR>/deployment_tools/inference_engine/external/mkltiny_lnx/lib:<INSTALL_DIR>/deployment_tools/inference_engine/lib/ubuntu_16.04/intel64:<INSTALL_DIR>/deployment_tools/model_optimizer/model_optimizer_caffe/bin:<INSTALL_DIR>/openvx/lib
    PYTHONPATH | <INSTALL_DIR>/python/python2.7/ubuntu16
    PARAM_MODEL_XML | <MODEL_DIR>/<IR.xml>, where <MODEL_DIR> is user specified and contains IR.xml, the Intermediate Representation file from Intel Model Optimizer
    PARAM_INPUT_SOURCE | <DATA_DIR>/input.mp4 to be specified by user. Holds both input and output data. For webcam, set PARAM_INPUT_SOURCE to `/dev/video0`
    PARAM_DEVICE | For CPU, specify `CPU`. For GPU, specify `GPU`. For FPGA, specify `HETERO:FPGA,CPU`
    PARAM_CPU_EXTENSION_PATH | <INSTALL_DIR>/deployment_tools/inference_engine/lib/ubuntu_16.04/intel64/<CPU_EXTENSION_LIB>, where CPU_EXTENSION_LIB is libcpu_extension_sse4.so for Intel Atom processors and libcpu_extension_avx2.so for Intel Core and Xeon processors
    PARAM_OUTPUT_DIRECTORY | <DATA_DIR> to be specified by user. Holds both input and output data
    PARAM_NUM_TOP_RESULTS | User specified for classification sample.(e.g. 1 for top-1 result, 5 for top-5 results)
    PARAM_TOPIC_NAME | Name of the topic for subscription to AWS IoT CLoud for publishing inference results
    PARAM_LABELMAP_FILE | Absolute path for the labelmap file which translates class labels to class names depending on the model in json format: `{"label0":"name0", "label1":"name1"}`.


* Use below LD_LIBRARY_PATH and additional environment variables for Arria10 FPGA:

    Key | Value
    :------------- | :-------------
    LD_LIBRARY_PATH | /opt/altera/aocl-pro-rte/aclrte-linux64/board/a10_ref/linux64/lib:/opt/altera/aocl-pro-rte/aclrte-linux64/host/linux64/lib:<INSTALL_DIR>/opencv/share/OpenCV/3rdparty/lib:<INSTALL_DIR>/opencv/lib:/opt/intel/opencl:<INSTALL_DIR>/deployment_tools/inference_engine/external/cldnn/lib:<INSTALL_DIR>/deployment_tools/inference_engine/external/mkltiny_lnx/lib:<INSTALL_DIR>/deployment_tools/inference_engine/lib/ubuntu_16.04/intel64:<INSTALL_DIR>/deployment_tools/model_optimizer/model_optimizer_caffe/bin:<INSTALL_DIR>/openvx/lib
    DLA_AOCX | <INSTALL_DIR>/a10_devkit_bitstreams/2-0-1_A10DK_FP11_SSD300.aocx
    CL_CONTEXT_COMPILER_MODE_INTELFPGA | 3


* Add subscription to subscribe or publish messages from Greengrass lambda function by following the steps 10-14 in AWS Greengrass developer guide at: https://docs.aws.amazon.com/greengrass/latest/developerguide/config-lambda.html. The “Optional topic filter” field should be set by `PARAM_TOPIC_NAME` environment variable inside lambda configuration (See `Configuring the Lambda Function` section)

    For example `intel/faas/ssd` or `intel/faas/classification`


Local Resources
-----------

* Add local resources and access privileges by following the instructions https://docs.aws.amazon.com/greengrass/latest/developerguide/access-local-resources.html
* Following are the local resources needed for various hardware (CPU,GPU and FPGA) options:

  * General (for all hardware options):

    Name | Resource Type | Local Path | Access
    ------------- |------------- | ------------- | -------------
    ModelDir | Volume | <MODEL_DIR> to be specified by user | Read-Only
    Webcam | Device | /dev/video0 | Read and Write
    DataDir | Volume | <DATA_DIR> to be specified by user. Holds both input and output data. | Read and Write
    OpenVINOPath | Volume | <INSTALL_DIR> where INSTALL_DIR is the OpenVINO installation directory | Read-Only

  * GPU:

    Name | Resource Type | Local Path | Access
    ------------- |------------- | ------------- | -------------
    GPU | Device | /dev/dri/renderD128 | Read and Write

  * FPGA:

    Name | Resource Type | Local Path | Access
    ------------- |------------- | ------------- | -------------
    FPGA | Device | /dev/acla10_ref0 | Read and Write
    FPGA_DIR1 | Volume | /opt/Intel/OpenCL/Boards | Read-Only
    FPGA_DIR2 | Volume | /etc/OpenCL/vendors | Read-Only

  * Movidius:

    Movidius hasn’t been validated with Greengrass yet. This section will be updated in future releases.

Deployment
-----------

To deploy the lambda function to AWS Greengrass core running on Intel edge device, select “Deployments” on group page and follow the instructions at: https://docs.aws.amazon.com/greengrass/latest/developerguide/configs-core.html

If you are using GPU or FPGA acceleration, in order to make sure the lambda function runs properly, make sure to add proper device access resources mentioned in the `Local Resources` section.

Only one greengrass lambda function can be run at any given time. If you are deploying your second lambda function, make sure to switch the previous lambda function to `on demand` mode so that it remains dormant.


Output Consumption
=================

There are four options available for output consumption. These options are used to report/stream/upload/store inference output at an interval defined by the variable `reporting_interval` in the Greengrass samples.
* IoT Cloud Output:

    This option is enabled by default in the Greengrass samples using a variable `enable_iot_cloud_output`.  We can use it to verify the lambda running on the edge device. It enables publishing messages to IoT cloud using the subscription topic specified in the lambda (For example, `intel/faas/classification` for classification and `intel/faas/ssd` for object detection samples). For classification, class labels, class names, confidence values for top-10 candidates along with frame id, inference fps and frame timestamp are published to AWS IoT Cloud every second. For SSD object detection, class labels, class names, confidence values, bounding box coordinates for each detection along with frame id, inference fps and frame timestamp are published to AWS IoT Cloud every second. To view the output on IoT cloud, follow the instructions at https://docs.aws.amazon.com/greengrass/latest/developerguide/lambda-check.html

* Kinesis Streaming:

    This option enables inference output to be streamed from the edge device to cloud using Kinesis [3] streams when `enable_kinesis_output` is set to True. The edge devices act as data producers and continually push processed data to the cloud. The users need to set up and specify Kinesis stream name, Kinesis shard, and AWS region in the Greengrass samples.  

* Cloud Storage using AWS S3 Bucket:

    This option enables uploading and storing processed frames (in JPEG format) in an AWS S3 bucket when `enable_s3_jpeg_output` variable is set to True. The users need to set up and specify the S3 bucket name in the Greengrass samples to store the JPEG images. The images are named using the timestamp and uploaded to S3.

* Local Storage:

    This option enables storing processed frames (in JPEG format) on the edge device when `enable_s3_jpeg_output` variable is set to True. The images are named using the timestamp and stored in a directory specified by `PARAM_OUTPUT_DIRECTORY`.

References
=================

[1] AWS Greengrass: https://aws.amazon.com/greengrass/

[2] AWS Lambda: https://aws.amazon.com/lambda/

[3] AWS Kinesis: https://aws.amazon.com/kinesis/
