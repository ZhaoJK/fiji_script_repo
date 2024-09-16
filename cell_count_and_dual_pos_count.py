from net.imagej import ImageJ
from org.scijava import Context
from org.scijava.command import CommandService
from ch.epfl.biop.wrappers.cellpose.ij2commands import Cellpose_SegmentImgPlusOwnModelAdvanced
from ij import IJ, ImagePlus, WindowManager, CompositeImage
from ij.process import ImageProcessor, ImageStatistics,ImageConverter
from ij.plugin import Duplicator, ChannelArranger, RGBStackMerge
from ij.plugin.frame import RoiManager
from ij.gui import Roi
from java.io import File
import os, re
from inra.ijpb.label import LabelImages
from  inra.ijpb.measure.region2d import Centroid
from inra.ijpb.plugins import DrawLabelsAsOverlayPlugin


def initialize_fiji_context():
    """Initialize ImageJ context and command service."""
    context = Context()
    command_service = context.getService(CommandService)
    return command_service


def run_cellpose_segmentation(image, model_path, nuclei_channel=1, cyto_channel=-1):
    """Run Cellpose segmentation on the image."""
    params = {
        'imp': image,
        'diameter': 25,
        'cellproba_threshold': 0.0,
        'flow_threshold': 0.4,
        'model_path': File(model_path),
        'model': 'nuclei_cp3',
        'nuclei_channel': nuclei_channel,
        'cyto_channel': cyto_channel,
        'dimensionMode': "2D",
        'stitch_threshold': -1
    }
    command_service = initialize_fiji_context()
    future = command_service.run(Cellpose_SegmentImgPlusOwnModelAdvanced, True, params)
    model_output = future.get().getOutputs()
    return model_output.get("cellpose_imp")


def count_nuclei(segmented_image):
    """Count the number of nuclei in the segmented image."""
    ip = segmented_image.getProcessor()
    stats = ip.getStatistics()
    return int(stats.max)


def process_dual_positive(image, hue_thresholds=(17, 62), size_threshold=200):
    """Process and filter dual-positive cells by thresholding and size filtering."""
    imp_RGB = ChannelArranger().run(image, [3,4])
    imp_RGB.setDisplayMode(IJ.COMPOSITE)
    
    ic = ImageConverter(imp_RGB)
    ic.convertToRGB()
    	
    ic = ImageConverter(imp_RGB)
    ic.convertToHSB()
    
    hue_channel = Duplicator().run(imp_RGB, 1, 1, 1, 1, 1, 1)
    hue_processor = hue_channel.getProcessor()
    
    hue_processor.setThreshold(hue_thresholds[0], hue_thresholds[1], 0)
    IJ.run(hue_channel, "Make Binary", "")
    IJ.run(hue_channel, "Create Selection", "")
    
    roi = hue_channel.getRoi()
    return roi


def clear_background(image, roi):
    """Clear the background in the segmented image based on a given ROI."""
    image.setRoi(roi)
    IJ.run(image, "Make Inverse", "")
    IJ.setBackgroundColor(0, 0, 0)
    IJ.run(image, "Clear", "")

def remove_small_object(image, object_size=200):
    """Remove small object from segmented image based on a given object_size."""
    IJ.run(image, "Label Size Filtering", "operation=Greater_Than size=" + str(int(object_size)))
    imp_filter = WindowManager.getImage(image.getTitle() + "-sizeFilt")
    imp_filter.hide()
    return imp_filter

def get_unique_objects(image):
    """Count the unique objects in the image by intensity values."""
    processor = image.getProcessor()
    unique_intensities = set()
    
    for x in range(processor.getWidth()):
        for y in range(processor.getHeight()):
            intensity = processor.getPixel(x, y)
            if intensity != 0:
                unique_intensities.add(intensity)
    
    return unique_intensities


def create_overlay_image(base_image, segmented_image, unique_objects):
    """Create an overlay image and label unique objects."""
    processor = segmented_image.getProcessor()
    
    # Clear non-unique objects in the segmented image
    for x in range(processor.getWidth()):
        for y in range(processor.getHeight()):
            intensity = processor.getPixel(x, y)
            if intensity not in unique_objects:
                processor.putPixel(x, y, 0)
    
    base_dup = Duplicator().run(base_image)
    base_dup = ChannelArranger().run(base_dup, [1, 3, 4])
    
    ic = ImageConverter(base_dup)
    ic.convertToRGB()
    
    labels = LabelImages.findAllLabels(segmented_image)
    centroids = Centroid().centroids(segmented_image.getProcessor(), labels)
    DrawLabelsAsOverlayPlugin().addLabelsAsOverlay(base_dup, labels, centroids)
    IJ.run("Labels...", "color=magenta font=14 show")  
    base_dup.show()



def count_cell_and_nuclei(original_image):
    """count cells and nuclei from image with a selected ROI."""
    original_roi = original_image.getRoi()
    # Check if ROI is None
    if original_roi is None:
        print("ROI not found!")
        exit(1)
    
    # Duplicate the image for further processing
    duplicated_image = Duplicator().run(original_image)
    
    # Segment nuclei using Cellpose
    model_path = "C:\\Users\\123\\.cellpose\\models\\nuclei_cp3"
    segmented_nuclei_image = run_cellpose_segmentation(Duplicator().run(original_image,1,1,1,1,1,1), model_path)
    # Count the number of nuclei
    total_nuclei = count_nuclei(segmented_nuclei_image)
    
    # Process dual-positive cells
    roi = process_dual_positive(duplicated_image)
    
    # Clear the background in the segmented image
    segmented_nuclei_image_clear = segmented_nuclei_image.duplicate()
    clear_background(segmented_nuclei_image_clear, roi)
    segmented_nuclei_image_clear = remove_small_object(segmented_nuclei_image_clear,150)
    
    # Count dual-positive objects
    unique_objects = get_unique_objects(segmented_nuclei_image_clear)
    total_positive = len(unique_objects)
    print(original_image.getTitle() + "\t" + original_roi.getName() + "\t" + str(int(total_nuclei)) + "\t" + str(int(total_positive)))
    
    # Create overlay image with labeled objects
    create_overlay_image(original_image, segmented_nuclei_image, unique_objects)

def main():
    # Get the currently open image
    original_image = WindowManager.getCurrentImage()
    original_image.setTitle(re.sub("\\.tiff|\\.jpg|\\.tif", "", original_image.getTitle()))
    
    rm = RoiManager.getInstance()
    if rm is None:
        rm = RoiManager()
        print("No ROIs in the ROI Manager!")
        original_image.setRoi(200,200,600,600);
        exit()

    rois = rm.getRoisAsArray()
    print("Image"+ "\t"+ "ROI" + "\t"+ "Nuclei"+ "\t"+ "Dual positive")
    for i in range(len(rois)):
        original_image.setRoi(rois[i])
        count_cell_and_nuclei(original_image)
    rm.runCommand("Save", original_image.getOriginalFileInfo().directory + original_image.getTitle() + "_RoiSet.zip")
    #rm.reset()
if __name__ == "__main__":
    main()
    print("Finished!!!")
