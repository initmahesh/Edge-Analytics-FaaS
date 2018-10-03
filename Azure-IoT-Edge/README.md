# Hardware-accelerated Function-as-a-Service Using Azure README

These scripts demonstrate how to enable HW accelerated FaaS with OpenVINO from within the Azure environment. Please see Azure-Iot-Edge-Setup.md for detailed usage instructions.

 - azure-iot-classification-sample.py: This script uses HW acceleration to do classification on an input video stream. It uses networks like AlexNet and GoogLeNet.
 - azure-iot-object-detection-ssd-sample.py: This scripts uses HW acceleration to do object detection on a video stream. It uses single-shot multi-box detection (SSD) networks such as SSD Squeezenet, SSD Mobilenet, and SSD300.

Report security problems to: https://01.org/security