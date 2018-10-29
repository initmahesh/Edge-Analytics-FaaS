# Hardware-accelerated Function-as-a-Service Using AWS Greengrass README

These scripts demonstrate how to enable HW accelerated FaaS with OpenVINO from within an AWS Greengrass container. Please see the INSTRUCTIONS.md file in the appropriate OS folder for detailed usage instructions.

 - greengrass_classification_sample.py: This script uses HW acceleration to do classification on an input video stream. It uses networks like AlexNet and GoogLeNet.
 - greengrass_object_detection_sample_ssd.py: This scripts uses HW acceleration to do object detection on a video stream. It uses single-shot multi-box detection (SSD) networks such as SSD Squeezenet, SSD Mobilenet, and SSD300.

Report security problems to: https://01.org/security