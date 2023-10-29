# Author: Jiakuan
# Date: 20231027 14:55
# 
# Measure Fascia Area by open lif files 
import os,re
from ij import IJ, ImagePlus, WindowManager
from ij.io import FileInfo, OpenDialog
import ij.plugin.Duplicator
from  ij.plugin.frame import RoiManager
from ij.gui import Roi, WaitForUserDialog, YesNoCancelDialog ,GenericDialog
from ij.process import ImageConverter, ImageProcessor
from ij.plugin.filter.MaximumFinder import findMaxima
from inra.ijpb.morphology import MinimaAndMaxima
from java.awt import Rectangle
from java.lang import Double, Integer
from loci.plugins import BF
from loci.plugins.in import ImporterOptions

# Confirm RoiManager opened
def setUpRM():
    rm = RoiManager.getInstance()
    if rm is None:
        rm = RoiManager()
    else:
        rm.reset()
    return rm
    
# Remove BF curve set when opening image
def resetStackCurve(curImp):
    if curImp.getCompositeMode() > 0:
        for i in range(curImp.getNChannels()):
            curImp.setC(i+1)
            IJ.resetMinAndMax(curImp)
            
        curImp.setDisplayMode(IJ.COMPOSITE);
        curImp.updateAndDraw()
    else:
        IJ.resetMinAndMax(curImp)

# Find Object
def findObject(imp):
    ip= imp.getProcessor()
    globalMax = [0,0,0]
    x = 0
    y = 0
    for y in range(0 ,ip.getHeight()):
    #find local minimum/maximum now
        for x in range(0, ip.getWidth()):
        #ImageStatistics won't work if we have no ImagePlus
            v = ip.getPixelValue(x, y)         #float 
            if globalMax[0] < v: globalMax = [v,x, y]
    IJ.doWand(imp, globalMax[1], globalMax[2], 180, "8-connected")


# open lif with BF
def openLif(root_dir, img_name):
    """Return the fiji imagePlus list from lif file.
    
    Parameters:
        root_dir -- root from disk sign to "/"
        img_name -- lif files name
    Returns:
        imps: list of imageplus
    exp:
        #root_dir = "H:/Exper Stuff/Ferr_Fascia-Gpx8_size_20221114/"
        #img_name = "d5 rsl3 lps.lif"
    """
    options = ImporterOptions()
    options.setId(root_dir + img_name)
    #options.setAutoscale(True);
    options.setColorMode(ImporterOptions.COLOR_MODE_COMPOSITE)
    #options.setQuiet(True)
    options.setStackFormat("Hyperstack")
    options.setStackOrder("XYCZT")
    options.setOpenAllSeries(True)
    #options.setStitchTiles(True)
    
    imps = BF.openImagePlus(options)
    return imps

# Conver image stack, which opened from lif, as 8-bit Gray image
def convert_8gray(imp):
    """Return the 8-bit gray image from stack file.
    Parameters:
        imp -- imagePlus object with RGB stack
    Returns:
        imp: list of imageplus
    """
    resetStackCurve(imp)
    ic = ImageConverter(imp)
    ic.convertToRGB()
    ic.convertToGray8()

# remove noize outside of object
def clear_noize(imp):
    """Delete all noise outside object
    Parameters:
        imp -- imagePlus object 
    Returns:
        imp: 
    """
    
    IJ.setBackgroundColor(0, 0, 0)
    cur_roi= imp.getRoi()
    cur_roi.getInverse(imp)
    ip= imp.getProcessor()
    #ip.fill()
    ip.fillOutside(cur_roi)
    
# centrize object
def center_object(imp):
    """move object to center
    Parameters:
        imp -- imagePlus object 
    Returns:
        imp: 
    """
    
    cur_roi= imp.getRoi()
    distance_x = imp.getWidth()/2 - cur_roi.getXBase()- cur_roi.getFloatWidth() /2 
    distance_y = imp.getHeight()/2 - cur_roi.getYBase() -  cur_roi.getFloatHeight() /2
    
    ip= imp.getProcessor()
    IJ.setBackgroundColor(0, 0, 0)
    
    #ip.resetRoi()
    IJ.run(imp, "Select None", "");
    ip.translate(distance_x , distance_y)
    
def measureArea(imp):
    IJ.run("Set Measurements...", "area display redirect=None decimal=3")
    IJ.run(imp, "Measure", "")

def rename_title(imp):
    cur_title = imp.getTitle()
    component_title = re.split("-", cur_title)
    day_title = re.search("D\d", component_title[0]).group(0)
    new_title = re.sub("jiakuan\s", "", cur_title)
    new_title = re.sub("\\.lif", "", new_title)
    new_title = re.sub("\s", "", new_title)
    new_title = re.sub("\\(RGB\\)", "", new_title)
    imp.setTitle(new_title)
    return day_title
    

# main function
OD = OpenDialog("Open lif file")
root_dir = OD.getDirectory()
img_name = OD.getFileName()
print("File: ", root_dir + img_name)
imps = openLif(root_dir, img_name)

for imp in imps:
    print(imp.getTitle())
    #fi = imp.getFileInfo()
    #curImgDir = fi.getFilePath()
    #curImgTitle = fi.fileName
    
    rm = setUpRM()
    convert_8gray(imp)
        
    #IJ.setTool("*Rectangle*")
    #wait_user = WaitForUserDialog("Waiting", "Create selection!")
    #wait_user.show()    
    IJ.run(imp, "Enhance Contrast...", "saturated=0.35 normalize");
    findObject(imp)
    
    #correct obj
    IJ.run("Wand Tool...", "tolerance=130 mode=8-connected")
    imp.show()
    wait_user = WaitForUserDialog("Waiting", "Create selection!")
    wait_user.show()
    wandRoi = imp.getRoi()
    
    clear_noize(imp)
    center_object(imp)
    
    findObject(imp)
    folderName = rename_title(imp)
    measureArea(imp)
    imp.show()
    
    saveDir = os.path.join(root_dir, folderName)
    if not os.path.exists(saveDir):
        os.mkdir(saveDir)
    IJ.saveAs(imp, "Tiff", os.path.join(saveDir, imp.getTitle()))
#IJ.runMacroFile(script_dir + "measureArea_fascia.ijm", [root_dir, img_name])
