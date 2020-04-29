#!/usr/bin/python3
from LuxonisFunctions import *
import threading
import time
import serial
import tflite_runtime.interpreter as tflite
import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
from picamera import PiCamera
from picamera.array import PiRGBArray
import serial
from time import sleep

exitFlag = 0
isTarget = 0
disable_msg = [0 0]

# Pan tilt Parameters
thresh = 20 # px
xServo = '0 '
fire = '3 '
deltaP = 2 # degrees
fire_time = 6
servo_time = 1
stepper_angle = 0 

class Target (threading.Thread):
	def __init__(self, config, p, method,ser0,ser1):
		threading.Thread.__init__(self)
		self.config = config
		self.p = p
		self.method = method
		self.ser0 = ser0
		self.ser1
	def run(self):
		while exitFlag is 0:
			data = getImageData(self.p,self.config,self.method,None)
			global isTarget
			global stepper_angle

			if data is not None:
				# Target identified
				isTarget = 1
				print("Centering...")		
				
				# Check X position				
				x_pos = data[0]

				# Check if centered and Fire
				if abs(x_pos) < thresh:

					# Stop rotating navigation
					enable = 0
					heading = 2				
					command = bytearray([enable, heading])
					self.ser1.write(command)				
						
					# Construct command
					print("Fire!")				
					command = fire + '\n'
					self.ser0.write(command.encode('utf-8'))
					init_time = time.time()

					# Keep up with data queue
					while (time.time() - init_time < fire_time):
						data = getImageData(self.p,self.config,self.method,2)
						
					# Successful shot - reset navigation					
					if data is None:
						isTarget = 0
						print('reset')
						
				# Otherwise move servo by fixed amount 
				else:
					init_time = time.time()
					if x_pos > 0:
						heading = 4
					else:
						heading = 0
					enable = 1
					command = (bytearray([enable, heading_id])) 					
					self.ser1.write(command)
					while (time.time() - init_time < servo_time):
						data = getImageData(self.p,self.config,self.method,2)

class Nav (threading.Thread):
	def __init__(self, model,camera):
		threading.Thread.__init__(self)
		self.model = model
		self.camera = camera
		self.frame = PiRGBArray(self.camera, size=(640,720))
		self.cut = [-54, -18, 18, 54]

	def run(self):
		# Allocate Tensors
		interpreter = tflite.Interpreter(model_path=self.model)
		interpreter.allocate_tensors()
		
		# Get input and output tensors
		input_details = interpreter.get_input_details()
		output_details = interpreter.get_output_details()
				
		# check the type of the input tensor
		floating_model = input_details[0]['dtype']== np.float32

		# Main loop
		while exitFlag is 0:
		
			# Only perform inference if there is a target
			if isTarget is 0:

				# Aquire image
				camera.start_preview()
				self.camera.capture(self.frame,'rgb')
				input_data = np.array([self.frame.array],dtype=np.float32)
				interpreter.set_tensor(0,input_data)
				interpreter.invoke()
				heading = interpreter.get_tensor(37)
				print(heading)
				heading_id = int(np.digitize(x=heading, bins=self.cut))	
				print(heading_id)
				#self.ser.write(bytearray([1, heading_id]))	
				self.frame.truncate(0)
				time.sleep(1)
				
			else:
				#self.ser.write(disable_msg)
				time.sleep(2)	


if __name__ == '__main__':
	# Setup Navigation
	#camera = PiCamera(resolution=(640,720))	
	ser1 = serial.Serial('/dev/ttyUSB1')
	#navigation = Nav('Nav-Model-1.tflite',camera)#,ser1)
	#navigation.start()
	
	# Setup Targeting
	ser0 = serial.Serial('/dev/ttyUSB0')
	time.sleep(2) 
	ser0.write(bytes('y','utf-8'))
	config, p = setupLuxonis()	
	target = Target(config,p,'CV',ser0,ser1)
	target.start()
	

#thread1.join()
#thread2.join()
