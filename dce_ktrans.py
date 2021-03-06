import os
import SimpleITK as sitk
import numpy as np
import vtk
import matplotlib.pyplot as plt

def readNifti(path):
	reader = sitk.ImageFileReader()
	reader.SetFileName(path)
	return reader.Execute()

def generateAIF(imageSeries,label=[],AIF_mode='label_average',labelNum=1,firstArrivalTime=0,scanInterval=1):
	if AIF_mode == 'label_average':
		if label != []:
			#check label is not empty
			statFilter = sitk.LabelStatisticsImageFilter()
			statFilter.Execute(label,label)
			if len(statFilter.GetLabels()) == 1:
				print 'AIF label is empty'
				return AIF_Parker(imageSeries,firstArrivalTime,scanInterval)
			else:
				return AIF_labelAverging(imageSeries,label,labelNum)
		else:
			print 'AIF label not found'
			return AIF_Parker(imageSeries,firstArrivalTime,scanInterval)
	elif AIF_mode == 'Parker':
		return AIF_Parker(imageSeries,firstArrivalTime,scanInterval)
	else:
		print 'invalid AIF model selection'
		return

def AIF_labelAverging(imageSeries,label,labelNum):
	print 'AIF is generated by label averging'
	statFilter = sitk.LabelStatisticsImageFilter()
	AIF = []
	for i in xrange(len(imageSeries)):
		statFilter.Execute(imageSeries[i],label)
		AIF.append(statFilter.GetMean(labelNum))
	return AIF

def AIF_Parker(imageSeries,firstArrivalTime,scanInterval):
	print 'AIF is generated by Parker model'

	timePoints = len(imageSeries)
	AIF = np.zeros(timePoints)
	firstArrivalTimePoint = int(np.ceil(firstArrivalTime/scanInterval))
	
	timeSeriesMinutes = scanInterval * np.arange(timePoints-firstArrivalTimePoint) / 60

	#Parker parameters from original paper
	a1 = 0.809
	a2 = 0.330
	T1 = 0.17406
	T2 = 0.365
	sigma1 = 0.0563
	sigma2 = 0.132
	alpha = 1.050
	beta = 0.1685
	s = 38.078
	tau = 0.483

	term_0 = alpha*np.exp(-1 * beta * timeSeriesMinutes) / (1 + np.exp(-s*(timeSeriesMinutes-tau)))
    
	A1 = a1 / (sigma1 * ((2*np.pi)**.5))
	B1 = np.exp(-(timeSeriesMinutes-T1)**2 / (2*sigma1**2))
	term_1 = A1 * B1

	A2 = a2 / (sigma2 * ((2*np.pi)**.5))
	B2 = np.exp(-(timeSeriesMinutes-T2)**2 / (2*sigma2**2))
	term_2 = A2 * B2

	post_bolus_AIF = term_0 + term_1 + term_2

	AIF[firstArrivalTimePoint:] = post_bolus_AIF

	return AIF

def separateTimeImage(image):
	# this function will reduce the image dimenison by 1 and convert them to image time array
	extractor = sitk.ExtractImageFilter()
	extractor.SetSize([image.GetSize()[0],image.GetSize()[1],0])
	image_separated = []
	for i in xrange(image.GetSize()[2]):
		extractor.SetIndex([0,0,i])
		image_separated.append(extractor.Execute(image))
	return image_separated

def main(data_folder):
	image = readNifti(data_folder + 'tofts_v6.nii.gz')
	AIF_label = readNifti(data_folder + 'tofts_v6-AIF-label_single_layer.nii.gz')
	image_separated = separateTimeImage(image)
	scanInterval = 0.5 #second

	# it is recommend to use label averaging AIF
	AIF = generateAIF(image_separated,AIF_label,labelNum = 1)
	# AIF = generateAIF(image_separated,firstArrivalTime=60,scanInterval=scanInterval) #AIF calculated in population mode
	# print AIF

	t = np.arange(0.0, image.GetSize()[2]*scanInterval, scanInterval)
	plt.plot(t, AIF)

	plt.xlabel('time (s)')
	plt.ylabel('T1')
	plt.title('Arterial Input Function')
	plt.grid(True)
	# plt.savefig("test.png")
	plt.show()

	writer = sitk.ImageFileWriter()
	# caster = sitk.CastImageFilter()
	# caster.SetOutputPixelType(1)
	for i in [01]:
		writer.SetFileName(data_folder+ str(i)+'.nii')
		writer.Execute(image_separated[500])

if __name__  == "__main__":
	data_folder = './test_data/'
	main(data_folder)