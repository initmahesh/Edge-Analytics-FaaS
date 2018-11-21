# Hardware-accelerated Function-as-a-Service Using Microsoft Azure Iot Edge

## Table of contents

<!-- Table of contents -->
   * [Introduction](#introduction)
   * [Supported Platforms](#supported-platforms)
   * [Pre-requisites](#pre-requisites)
   * [Description of Samples](#description-of-samples)
   * [Converting Deep Learning Models for Inference Engine](#converting-deep-learning-models-for-inference-engine)
   * [Configuring Azure Iot Edge](#configuring-azure-iot-edge)
   * [Creating FaaS modules from code samples](#creating-faas-modules-from-code-samples)
   * [Deploying the FaaS modules on Edge device](#deploying-the-faas-modules-on-edge-device)
   * [Output Consumption](#output-consumption)
   * [Optional: Integration with Azure Functions](#optional-integration-with-azure-functions)
   * [References](#references)
<!-- Table of contents -->

## Introduction

Hardware accelerated Function-as-a-Service (FaaS) enables cloud developers to deploy inference functionalities on Intel IoT edge devices with accelerators (Integrated GPU, FPGA, and Movidius).  These functions provide a great developer experience and seamless migration of visual analytics from cloud to edge in a secure manner using containerized environment. Hardware-accelerated FaaS provides the best-in-class performance by accessing optimized deep learning libraries on Intel IoT edge devices with accelerators.
	
This document describes the creation and deployment of FaaS inference samples (based on Python 3.5) using Azure's Iot Edge service [1]. These functions can be created, modified, and updated in the cloud and can be deployed from cloud to edge using Azure Iot Edge Runtime. This document covers description of samples, pre-requisites for Intel edge device, configuring a Azure Iot Hub, creating and packaging docker images, deployment of docker images and how to consume the inference output. 

## Supported Platforms

* Operating System: Ubuntu 16.04
* Hardware:
  * Aaeon Up2 kit with integrated GPU (https://software.intel.com/en-us/blogs/2018/05/16/kits-to-accelerate-your-computer-vision-deployments) 
  * IEI 870 tank with integrated GPU (https://software.intel.com/en-us/blogs/2018/05/16/kits-to-accelerate-your-computer-vision-deployments)
  * Accelerators: Arria10 1150 FPGA (https://www.buyaltera.com/Search/?keywords=arria+kit) , Intel Vision Accelerator Design Card (VAD)(https://www.ieiworld.com/mustang-f100/en/), Intel Vision Accelerator Design Card for FPGA (VAD-F) (https://www.intel.com/content/www/us/en/internet-of-things/solution-briefs/vision-accelerator-design-brief.html )
## Pre-requisites

### Pre-requisites for Intel Edge Devices

1. Download and install OpenVINO R4 release Toolkit from https://software.intel.com/en-us/openvino-toolkit (for FPGA, install Openvino fpga installer)
2. For configuring GPU to use OpenVINO, follow the instructions under section “Additional Installation Steps for Processor Graphics (GPU)” at https://software.intel.com/en-us/articles/OpenVINO-Install-Linux#inpage-nav-4-1
3. Create a writeable <DATA_DIR> on the host device to hold input and output data. Copy any video files for input here. Note that this directory location should be accessible to all UIDs.
	For example:
	```
	$ mkdir /opt/data
	$ chmod a+rw /opt/data
	```
	
4. Create a readable <MODEL_DIR> on the host device to hold the trained models in OpenVINO IR format.Note that this directory location should be accessible to all UIDs.
	For example:
	```
	$ mkdir /opt/models
	$ chmod a+r /opt/models
	```

5. Make a note of the <OPENVINO_DIR> which is where OpenVINO is installed (usually in /opt/intel/computer_vision_sdk_2018.4.420, for FPGA /opt/intel/computer_vision_sdk_fpga_2018.4.420)
6. Additional instructions for FPGA. Make a note of <ALTERA_DIR>, the directory in which Altera OpenCL runtime and BSP are installed. Also, <DEVICE_DIR> which is /dev/aclhddlf_1150_sg10 for VAD card and /dev/acla10_ref0 for arria 10.

### Workstation pre-requisites for producing custom images
1. Ubuntu/Linux OS
2. Install Docker CE as shown in https://docs.docker.com/install/linux/docker-ce/ubuntu/

## Description of Samples

We provide the following Azure Iot samples:

* azure-iot-classification-sample.py

    This sample classifies a video stream using classification networks such as AlexNet and GoogLeNet and publishes class labels, class names, confidence values for top-10 candidates along with frame id, inference fps and frame timestamp on Azure Iot Cloud every second. 

* azure-iot-object-detection-ssd-sample.py

    This sample detects objects in a video stream and classifies them using single-shot multi-box detection (SSD) networks such as SSD Squeezenet, SSD Mobilenet, and SSD300. This sample publishes detection outputs such as class labels, class names, confidence values, bounding box coordinates for each detection along with frame id, inference fps and frame timestamp on Azure IoT Cloud every second. 

## Converting Deep Learning Models for Inference Engine

### Downloading Sample Models

* For classification, download the BVLC Alexnet model (deploy.prototxt and bvlc_alexnet.caffemodel) as an example from https://github.com/BVLC/caffe/tree/master/models/bvlc_alexnet. Any custom pre-trained classification models can be used with the classification sample.

* For object detection, download Intel Edge optimized models available at https://github.com/intel/Edge-optimized-models. These models are provided as an example, but any custom pre-trained SSD models can be used with the object detection sample. 

### Setting up & running the Model Optimizer tool

* Model Optimizer is a tool provided with the OpenVINO to convert a model to an Intermediate Representation (IR) format. A model must first be converted into an IR format to be parsable by the Inference Engine.
* For setting up Model Optimizer and converting deep learning models to the IR format, follow the instructions at: https://software.intel.com/en-us/articles/OpenVINO-ModelOptimizer. 


## Configuring Azure Iot Edge

<b>Pre-requisite</b>: Install Azure CLI to manage Azure cloud resources using command line interface.
Refer to: https://docs.microsoft.com/en-gb/cli/azure/install-azure-cli-apt?view=azure-cli-latest

For each Intel edge platform, we need to create a Azure Iot Hub and edge Device and Azure IotEdge Runtime. To create and configure the Iot Hub on Azure cloud and Azure Iot Edge on the IoT device, follow the instructions in the Azure documentation links below:

<b>1. Create an IoT Hub.</b> Follow instructions at https://docs.microsoft.com/en-us/azure/iot-edge/quickstart-linux#create-an-iot-hub 

<b>2. Register an IoT Edge device instance on the cloud.</b> Follow instructions at: https://docs.microsoft.com/en-us/azure/iot-edge/quickstart-linux#register-an-iot-edge-device

<b>3. Install and configure Azure Iot Edge Runtime software on the edge device.</b> Follow the instructions at: https://docs.microsoft.com/en-us/azure/iot-edge/quickstart-linux#install-and-start-the-iot-edge-runtime


## Creating FaaS modules from code samples

1. Download the code samples along with the provided Dockerfile

2. To build the FaaS docker images, run the following command in the same folder:
	```
	$ docker build -t <image-name> --build-arg SCORING_SCRIPT="<script-name>" .
	```
	For example to build a FaaS image with the azure_iot_object_detection_ssd_sample.py, run the following:
	```
	$ docker build -t ssd-faas --build-arg SCORING_SCRIPT="azure-iot-object-detection-ssd-sample.py" .
	```

3. Upload the samples to an Azure container registry as follows:<br>

 	a. Follow the link below to upload your image to the cloud:
	https://docs.microsoft.com/en-us/azure/container-registry/container-registry-get-started-docker-cli

	a. Tag the image accordingly
	```
	$ docker tag <image-name>:<tag> <registryurl>/<image-name>:<tag>
	```
	b. Login to the container registry
	```
	$ az acr login -n <registry-name> -u <registry-user-name> -p <registry-password>
	```
	c. Push the docker image to the registry
	``` 
	$ docker push <registryurl>/<image-name>:<tag>
	``` 
	d. Lists the repositories that you just uploaded
	```
		az acr repository list --name <registry-name> --output table
	```


## Deploying the FaaS modules on Edge device

1. After creating Iot Edge and pushing the docker image onto the Azure Container Repository, you need to deploy the image onto the Iot Edge.
2. In the Azure portal, navigate to your IoT hub.
3. Go to <b>IoT Edge</b> and select your <b>IoT Edge device</b>.
4. Select <b>Set Modules</b>.

	a. On the same page, enter your Container Registry Settings - name, address, username, password.

	b. On the Deployment Modules section of the page, click Add then select <b> IoT Edge Module </b>.

	c. In the Name field, enter your <b> docker-image-name </b>.

	d. In the Image URI field, enter <b> \<registryurl\>/\<image-name\>:\<tag\> </b>.

	e. Docker options:
	In the Container Create Options please replace as below
	```json	
	{
		"HostConfig": {
			"Binds": [
			"<OPENVINO_DIR>:/opt/intel/computer_vision_sdk",
			"<DATA_DIR>:/opt/data",
			"<MODEL_DIR>:/opt/model"
			],

			"Devices": [
			{
				"PathOnHost": "/dev/dri/renderD128",
				"PathInContainer": "/dev/dri/renderD128",
				"CgroupPermissions": "rwm"
			}
			]
		}
	}
	```
    
	For FPGA based devices (VAD-F or Arria 10 devkit), add the additional options to HostConfig shown below:
	```json	
	{
	    "HostConfig": {
			"Binds": [
			"<ALTERA_DIR>:/opt/altera",
			"/etc/OpenCL/vendors:/etc/OpenCL/vendors",
			"/opt/Intel/OpenCL/Boards:/opt/Intel/OpenCL/Boards"
			],
	    		"Devices": [
			{
				"PathOnHost": "<DEVICE_DIR>",
				"PathInContainer": "<DEVICE_DIR>",
				"CgroupPermissions": "rwm"
			}
                       ]
            }
         }
	```
	where DEVICE_DIR=/dev/aclhddlf_1150_sg10 for VAD-F and DEVICE_DIR=/dev/acla10_ref0 for a10_devkit

	
 	f. And in environmental variables, specify the following:

	| NAME|VALUE|
	| ---|---|
	| DEVICE| Choose an accelerator device <br/> **CPU** or **GPU** or **HETERO:FPGA,CPU**|
	| INPUT | **cam** for Camera Input <br/> (or) <br/> full path to input file under the */opt/data/* folder<br/> when using camera input, add the camera device to the "Devices" above container options as follows <br/>`{"PathOnHost": "/dev/video0","PathInContainer": "/dev/video0","CgroupPermissions": "rwm"}` |
	| MODEL_XML_PATH | Path to the .xml file of the model in OpenVINO IR format inside the */opt/model/* directory |
	| CONNECTIONSTRING | Connection string for the IoT Edge device in Azure IoT Hub |
	| OUTPUT_DIR| Path to folder to write output into within '/opt/data/' directory |
 
	For FPGA based accelerator devices, specify the following additional environmental variables
	
	For a10_devkit:
	
	| NAME| VALUE|
	| ---|---|
	| DLA_AOCX| /opt/intel/computer_vision_sdk/bitstreams/a10_devkit_bitstreams/4-0_A10DK_FP16_AlexNet_GoogleNet.aocx ( For SSD use /opt/intel/computer_vision_sdk/bitstreams/a10_devkit_bitstreams/4-0_A10DK_FP16_TinyYolo_SSD300.aocx) |
	| CL_CONTEXT_COMPILER_MODE_INTELFPGA| 3|
	| LD_LIBRARY_PATH| /opt/altera/aocl-pro-rte/aclrte-linux64/board/a10_ref/linux64/lib:/opt/altera/aocl-pro-rte/aclrte-linux64/host/linux64/lib:<INSTALL_DIR>/opencv/share/OpenCV/3rdparty/lib:<INSTALL_DIR>/opencv/lib:/opt/intel/opencl:<INSTALL_DIR>/deployment_tools/inference_engine/external/cldnn/lib:<INSTALL_DIR>/deployment_tools/inference_engine/external/mkltiny_lnx/lib:<INSTALL_DIR>/deployment_tools/inference_engine/lib/ubuntu_16.04/intel64:<INSTALL_DIR>/deployment_tools/model_optimizer/model_optimizer_caffe/bin:<INSTALL_DIR>/openvx/lib |
    
	For VAD-F card:
	
	| NAME| VALUE|
	| ---|---|
	| DLA_AOCX| /opt/intel/computer_vision_sdk/bitstreams/a10_vision_design_bitstreams/4-0_PL1_FP16_Generic_AlexNet_GoogleNet_VGG.aocx ( For SSD use /opt/intel/computer_vision_sdk/bitstreams/a10_vision_design_bitstreams/4-0_PL1_FP16_TinyYolo_SSD300.aocx) |
	| CL_CONTEXT_COMPILER_MODE_INTELFPGA| 3|
	| LD_LIBRARY_PATH| /opt/altera/aocl-pro-rte/aclrte-linux64/board/hddlf_1150_sg1/linux64/lib:/opt/altera/aocl-pro-rte/aclrte-linux64/host/linux64/lib:<INSTALL_DIR>/opencv/share/OpenCV/3rdparty/lib:<INSTALL_DIR>/opencv/lib:/opt/intel/opencl:<INSTALL_DIR>/deployment_tools/inference_engine/external/cldnn/lib:<INSTALL_DIR>/deployment_tools/inference_engine/external/mkltiny_lnx/lib:<INSTALL_DIR>/deployment_tools/inference_engine/lib/ubuntu_16.04/intel64:<INSTALL_DIR>/deployment_tools/model_optimizer/model_optimizer_caffe/bin:<INSTALL_DIR>/openvx/lib |
	
	<br> 
	
	Example of container create configuration with a **Camera** input and **VAD-F** accelerator:

	```json	
	{
		"HostConfig": {
			"Binds": [
			"<OPENVINO_DIR>:/opt/intel/computer_vision_sdk",
			"<DATA_DIR>:/opt/data",
			"<MODEL_DIR>:/opt/model",
			"<ALTERA_DIR>:/opt/altera",
			"/etc/OpenCL/vendors:/etc/OpenCL/vendors",
			"/opt/Intel/OpenCL/Boards:/opt/Intel/OpenCL/Boards"
			],

			"Devices": [
			{
				"PathOnHost": "/dev/aclhddlf_1150_sg10",
				"PathInContainer": "/dev/aclhddlf_1150_sg10",
				"CgroupPermissions": "rwm"
			},
			{
				"PathOnHost": "/dev/video0",
				"PathInContainer": "/dev/video0",
				"CgroupPermissions": "rwm"
			}
			]
		}
	}
	```

	g. Back in the **Add modules** step, select **Next**.
	
	h. In the **Review Deployment** step, select **Submit**.
	
	i. After the deployment, click **Refresh**. You should see the device connected on the Iotedge device page and the module running
	
5. Verify via edgeAget logs for deployment status on the edge device: 
```
docker container logs edgeAgent -f 
```
6. The output of the FaaS module itself can be accessed with the image logs. For example: 
```
docker container logs <image-name> -f
```



## Output Consumption
---
* Stream Analytics:
	* On the Azure Portal, Create a new Stream Analytics Job (found under Internet of Things)
		* Provide a JobName and Resource Group. Hosting Environment is Cloud. 
		* Under the Job Topology on the Left Panel, configure the Inputs, Outputs. 
		* Select Inputs, Add Stream Input -> Iot Hub -> Provide a name for your Input alias and select your IOTHub and Save.
		* Select Outputs, Add-> Power BI -> Provide a name for your Output alias, dataset and tablename. Authorize your email to use Power BI and Save.
		* Select Query, Fill the Query by providing your Input alias and Output Alias.
		* Go to the 'Overview' page to start the inference stream. 
* Power BI: 
	* Go to https://powerbi.microsoft.com/en-us/ and sign in using your Azure credentials.
		* On the left Panel, click on My Workspace arrow to expand the selection. 
		* Select your Dataset-> Select Visualizations -> Select the Fields - eventsEnqueuedUtcTime and Fps.
		* To further view the dataset along with the table, Select view dataset on top right corner of your chart.


## Optional: Integration with Azure Functions

### Creating and Packaging Azure Functions
* Download and Install VS code from: https://code.visualstudio.com/ 
* In VS Code, on left hand panel, select Extensions and add the necessary extensions: 
	* Azure Iot Edge
	* Azure Account
	* Azure Functions
	* Azure Iot Toolkit	
	* Docker
	* Python
* Setup the added Extensions: In VS Code, select View -> Command Palette. Enable the extensions as follows:
	* <b>Azure Account</b>: Sign into Azure by running the command <b> Azure: Sign in </b>
	* <b>Azure Iot Edge</b>: Run the command <b> Azure Iot Edge: New Iot Edge solution </b>
		* Create a folder to contain the Iot Edge solution files.
	* Choose <b> Python module </b> -> (Provide a Module name) -> Replace localhost:5000/ with your container Registry login server name ( Found at Azure Portal-> Container Registry-> Overview). Please Note: Python modules require cookie cutter to be installed on the system. Install it through the command line: <b> pip install --upgrade --user cookiecutter </b>
	* <b>Azure Iot Toolkit</b>: Run the command <b> Azure IoT Hub: Select IoT Hub </b>
		* <b>Select the subscription</b> -> <b>Hub Name </b>. 
* In VS Code, open terminal and Sign into Azure Container Registry using the folling command: <b> az acr login -n <registry-name> -u <registry-user-name> -p <registry-password> </b> (username password found under Azure Portal -> Container Registry -> Access Keys)
	* Once logged in, you will be able to see your Container Registry using command <b> az acr list </b>.
* Configuring the Azure Function: 
	* Expand the Solution in the left panel.
	* Right-click on the module and choose <b> Add a new Module </b>. Provide a module name and choose the Python module.
	* Right-click on the module name, choose <b> Open Containing Folder </b>, copy all the files from the Azure-Iot-Edge-setup folder into the current folder.
	* Open the modules.json file, 
		* edit the Docker name to <b>./Dockerfile </b>.
		* edit the tag name to your desired tag.	
* Build and Push Image: In the Left Pane, right-click the  deployment.template.json file, choose <b> Build and Push to Iot Edge Solution </b>.
* Create an IOT Edge Device: 
	* In the VS Code, expand the Azure IoT Hub Devices section, Right-click and create Iot Edge Device. 
	  You will notice in the output the device info and your device is added in the Azure Iot Hub Device section along with 2 modules: edgeAgent and edgeHub.	  
* Deployment of Module: 
	* Follow the <b> [Configure the cloud and device](#configure-the-cloud-and-device) </b> section to setup the Module in the Azure Portal.
	* Right-click the name of your IoT Edge device in VS Code, and then select Create Deployment for single device.  
* Login to Docker:
	* View -> Open View -> Terminal
	* Run the command <b>docker login -u <username> <acr login server> </b>

## References
---
1. Azure Iot Edge:https://docs.microsoft.com/en-us/azure/iot-edge/
2. Docker: https://docs.docker.com/get-started/
3. Power BI: https://powerbi.microsoft.com/en-us/
4. Azure portal: https://portal.azure.com/
5. Open Vino: https://software.intel.com/en-us/openvino-toolkit
6. Azure Functions: https://docs.microsoft.com/en-us/azure/iot-edge/how-to-deploy-modules-vscode
7. VS Code: https://code.visualstudio.com/





