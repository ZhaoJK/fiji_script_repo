#@ File    (label = "Root directory", style = "directory") input_dir
#@ String  (label = "File extension", value="czi") ext

#@ CommandService command
#@ DatasetIOService io


from ij import IJ, WindowManager
from ij import ImageStack, ImagePlus
import imageware.Builder
import ij.plugin.StackWriter as StackWriter
import ij.plugin.Duplicator as Duplicator
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable,Measurements
from ij.plugin.filter import Analyzer
from ij.plugin import ZProjector
from ij.gui import GenericDialog

from loci.plugins import BF
from  loci.plugins.in import ImporterOptions

import edfgui.ExtendedDepthOfField as edf
import edfgui.Parameters as para
from edf import EdfRealWavelets, Tools, Color2BW

from register_virtual_stack import Register_Virtual_Stack_MT

import emblcmci.BleachCorrection_ExpoFit as bleachExp
from de.csbdresden.stardist import StarDist2D 

import java.awt.Color as Color
from ij.gui import Roi

import os, glob,string


#open image with bioformat
def openImgBF(imgName):

	options = ImporterOptions();
	options.setId(imgName);
	#options.setAutoscale(True);
	options.setColorMode(ImporterOptions.COLOR_MODE_COMPOSITE);
	#options.setQuiet(True)
	options.setStackFormat("Hyperstack")
	options.setStackOrder("XYCZT")
	#options.setStitchTiles(True)
	
	imps = BF.openImagePlus(options)
	imps[0].show()
	return imps[0]


#edf setting
edf_para = para()
edf_para.doDenoising = True

"""
colorconversion=0
edfmethod=1
outputcolormap=1

toposigma=2.0
densigma=2.0
wvthreshold=10.0

filterlen=6
splineorder=3
nscales=1
varwindow=3
medianwindow=3

reassignment=false
subbandcc=false
majcc=false
morphopen=false
morphclose=false
topogauss=false
denoising=true
median=false

showtopo=false
show3d=false
log=false
"""

#reset env
rm = RoiManager.getInstance()
if rm is None:
	rm = RoiManager()
rm.reset()

def run():
	root_dir = input_dir.getAbsolutePath()
	for img_dir, directories, filenames in os.walk(root_dir):
		filenames.sort()
		for filename in filenames:
		# Check for file extension
			if not filename.endswith(ext):
				continue
			process(root_dir, img_dir, filename)
 
def process(root_dir, current_img_dir, img_name):
	print "Processing:"
	
	# Opening the image
	print("current image dir", current_img_dir)
	print("Open image file", img_name)

	imgPath = os.path.join(current_img_dir, img_name)
	imp_raw = openImgBF(imgPath)
	
	#remove extension from image title
	imp_title = imp_raw.getTitle().split(".")[0]
	imp_dir = IJ.getDirectory("image")
	
	#log out
	print("Image title: ", imp_title)
	print("Image from", imp_dir)
	
	
	#EDF start 
	new_imp_list = list()
	
	imp_raw_nFrame = imp_raw.getNFrames() + 1
	
	for i in range(1,imp_raw_nFrame):
		imp_raw.setPosition(0, 0, i)
		impBW = Duplicator().run(imp_raw, 0,0 ,1, imp_raw.getNSlices(),i,i)
		
		imageStack = imageware.Builder.wrap(impBW)
		nx = imageStack.getWidth()
		ny = imageStack.getHeight()
		
		#log out 
		print("EDF at " + str(i) + "/" + str(imp_raw_nFrame-1))
		
		edf = EdfRealWavelets(edf_para.splineOrder, edf_para.nScales,
							edf_para.subBandCC, edf_para.majCC, edf_para.rateDenoising)
		ima = edf.process(imageStack)
		
		imageStack = Tools.crop(imageStack,nx,ny);
		ima[0] = Tools.crop(ima[0],nx,ny);
		ima[1] = Tools.crop(ima[1],nx,ny);
		impComposite = ImagePlus("T_" + str(i), ima[0].buildImageStack())
	
		new_imp_list.append(impComposite)
	
	imp_raw.changes = False
	imp_raw.close()
	imp_temp_stack = ImageStack.create(new_imp_list)
	imp_edf = ImagePlus(imp_title + "_edf",imp_temp_stack)
	
	#imp_temp_stack.changes = False
	#imp_temp_stack.close()
	imp_edf.show()
	print("EDF Done!!!")
	
	
	#init temp folder for register
	
	temp_dir = imp_dir + "tmp/"
	if not os.path.exists(temp_dir): os.makedirs(temp_dir)
	temp_dir_files = glob.glob(temp_dir + "*")
	for f in temp_dir_files:
		os.remove(f)
		
	temp_dir2 = imp_dir + "tmp2/"
	if not os.path.exists(temp_dir2): os.makedirs(temp_dir2)
	temp_dir_files = glob.glob(temp_dir2 + "*")
	for f in temp_dir_files:
		os.remove(f)
	
	imp_edf_title = imp_edf.getTitle()
	imp_edf_title = string.replace(imp_edf_title, " ", "_")
	print("EDF image:", imp_edf_title)
	
	
	print("Writing single tiff ...")
	StackWriter.save(imp_edf, 
					 temp_dir, 
					 "name=" + imp_edf_title + "_ format=tiff digits=2")
	
	#set plugin parameters	
	source_dir = temp_dir
	output_dir = temp_dir2
	
	print("Registering EDF image...")
	#IJ.run(imp_edf, "Register Virtual Stack Slices", "source=" + source_dir +" output=" + output_dir + " feature=Affine registration=[Affine               -- free affine transform               ]")
	Register_Virtual_Stack_MT.exec(source_dir, output_dir, None, imp_edf_title + "_30.tif",Register_Virtual_Stack_MT.SIMILARITY, Register_Virtual_Stack_MT.SIMILARITY,  False, False)
	
	imp_reg = WindowManager.getImage("Registered tmp")
	imp_reg_title = imp_edf_title + "_reg"
	imp_reg.setTitle(imp_reg_title)
	
	print("Registeration finished!!!")
	print("Saving...!!!")
	IJ.saveAs(imp_reg, "Tiff",  imp_dir + imp_reg_title + ".tif")
	imp_edf.changes = False
	imp_edf.close()
	
	#IJ.run(imp_reg, "Save",  imp_dir + imp_reg_title + ".tif")
	imp_reg.setTitle(imp_reg_title + ".tif")
	
	temp_dir_files = glob.glob(temp_dir + "/*")
	for f in temp_dir_files:
		os.remove(f)
	temp_dir_files = glob.glob(temp_dir2 + "/*")
	for f in temp_dir_files:
		os.remove(f)
	
	#reset env
	rm = RoiManager.getInstance()
	if rm is None:
		rm = RoiManager()
	rm.reset()
	
	#get current image
	imp_reg.changes = False
	imp_reg.close()
	
	imp_reg = IJ.openImage(imp_dir + imp_reg_title + ".tif")
	
	imp_nFrame = imp_reg.getNSlices()
	
	#16 bit , bleach correnction
	IJ.run(imp_reg, "16-bit", "")
	IJ.run(imp_reg, "Subtract Background...", "rolling=200 stack")
	IJ.run(imp_reg, "Properties...", "channels=1 slices=1 frames=" + str(imp_nFrame) +" pixel_width=0.645 pixel_height=0.645 voxel_depth=1.0000 frame=[5 sec]")
	#BCEF = bleachExp(imp_reg)	#BleachCorrection_ExpoFit
	#try:
	#	BCEF.core()
	#finally:
	imp_reg.show()
	
	imp_reg_bb_title =  imp_reg_title + "_bb16"
	imp_reg.setTitle(imp_reg_bb_title)
	print("Save bleachcorrected image...")
	IJ.saveAs(imp_reg, "Tiff", imp_dir + imp_reg_bb_title +  ".tif")
	
	imp_zproj = ZProjector.run(imp_reg,"max")
	res = command.run(StarDist2D, False,
		"input", imp_zproj,
		"modelChoice", "Versatile (fluorescent nuclei)",
		'normalizeInput',True, 
		'percentileBottom',0.5, 
		'percentileTop',98.0, 
		'probThresh',0.5, 
		'nmsThresh',0.4, 
		'outputType',"Both", 
		'nTiles',1, 
		'excludeBoundary',20, 
		'roiPosition',"Automatic", 
		'verbose',False, 
		'showCsbdeepProgress',False, 
		'showProbAndDist',0
		).get()
	label = res.getOutput("label")
	print("Saving labelling image...")
	label_img_path = imp_dir + imp_reg_bb_title + "_label.tif"
	if os.path.exists(label_img_path ): os.remove(label_img_path)
	io.save(label, label_img_path)
	#IJ.saveAs(imp_label, "Tiff", imp_dir + "\\z-proj_max_stardist_label\\" + imp_title + "_bg_bleach_16_frame_stardist_label.tif")
	print("Saving ROI ...")
	
	
	rm.runCommand("Save", imp_dir + imp_reg_bb_title + "_roi.zip")
	
	print("Measure intensity for each roi ...")
	rm.runCommand(imp_reg,"Show All");
	rois = rm.getRoisAsArray() #ij.gui.Roi
	IJ.run("Set Measurements...", "mean display redirect=None decimal=2");
#	IJ.run(imp_reg, "Macro...", "code=roiManager('multi-measure measure_all')")
#	#rm.runCommand(imp_reg,"multi-measure measure one")
#	#rt = rm.multiMeasure(imp_reg);
#	
#	
#	print("Saving value to csv file ...")
#	rt = ResultsTable.getActiveTable()
#	rt.saveAs(imp_dir + imp_reg_bb_title + "_int.csv")
#	rt.reset()
#	
#	
#	print("Measurement finished!!!")
#	rm.runCommand(imp_reg,"Show None");
#	rm.reset()
	nIndexes = rm.getCount()
	nSlices =imp_reg.getStackSize()
	
	
	rt = ResultsTable() #ij.measure.ResultsTable
	rt.showRowNumbers(True)
	measurements2 = Measurements.MEAN|Measurements.SLICE|Measurements.LABELS
	analyzer = Analyzer(imp_reg, measurements2, rt) #Analyzer 
	analyzer.setRedirectImage(None)
	analyzer.disableReset(True)
	analyzer. setPrecision(3)
	
	for slice in range(nSlices):
		imp_reg.setSliceWithoutUpdate(slice)
		for i in range(nIndexes):
			rois[i].setColor(Color(255,200,200))
			rois[i].setStrokeWidth(1)
			imp_reg.setRoi(rois[i], True)
			analyzer.measure()

	print("Saving value to csv file ...")
	rt.saveAs(imp_dir + imp_reg_bb_title + "_int.csv")
	rt.reset()
	
	
	#export video
	IJ.run(imp_reg, "Properties...", "channels=1 slices=1 frames=" + str(imp_nFrame) +" pixel_width=1.6 pixel_height=1.6 voxel_depth=0 frame=[5 sec]");
	
	IJ.setForegroundColor(255, 255, 255);
	IJ.setBackgroundColor(0, 0, 0);
	
	rm.runCommand(imp_reg,"Show None")
	#IJ.setTool("text");
	IJ.run("Remove Overlay", "");
	IJ.run(imp_reg, "Label...", "format=0 starting=0 interval=5 x=20 y=20 font=60 text=sec range=1-" + str(imp_nFrame) + " use use_text");
	IJ.run(imp_reg, "Scale Bar...", "width=200 height=128 thickness=18 font=25 color=White background=None location=[Lower Right] horizontal bold hide overlay label");
	
	#IJ.run(imp, "Save", "")
	
	imp_reg.flattenStack();
	
	#imp_reg.getCalibration().fps = 12
	#AVI_Writer.writeImage​(imp_reg, imp_dir + imp_reg_bb_title + ".avi", AVI_Writer.JPEG_COMPRESSION, 90)
	IJ.run(imp_reg, "AVI... ", "compression=JPEG frame=12 save=[" + imp_dir + imp_reg_bb_title + ".avi]");

	print("Done!!!")
	
	imp_reg.changes = False
	imp_reg.close()
	rm.reset()

run()
