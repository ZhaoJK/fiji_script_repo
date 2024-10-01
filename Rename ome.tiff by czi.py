# Rename ome.tiff according to region of Czi Scanner
#

import os
import numpy as np
import matplotlib.pyplot as plt
from aicspylibczi import CziFile
import xml.etree.ElementTree as ET
import pandas as pd

directory_path = "H:\\Expdata_HDD1\\mSkin_Ferro_Fib_pheno_20240910\\Wound"
for filename in os.listdir(directory_path+"\\raw"):
    if filename.endswith('.czi'):
        print(f'Processing file: {filename}')
        file_path = os.path.join(directory_path+"\\raw", filename)
        czi = CziFile(file_path, True)
        root = czi.meta

        for scene in root.findall('.//Scenes/Scene'):
            x_pos = float(scene[2].text.split(",")[0])
            print(x_pos)
            scene_index = int(scene.attrib['Index']) + 1
            if x_pos < -25000:
                new_file_type = 'PDPN(568)_pSTAT3(647)'
            else:
                new_file_type = 'RUNX2(568)_aSMA(647)'
            czi_filename = filename.split('.')[0]
            original_filename = f'{czi_filename}_s{scene_index}.tiff'
            new_filename = f'{czi_filename}_{new_file_type}_s{scene_index}.tiff'

            if os.path.exists(os.path.join(directory_path, original_filename)):
                os.rename(os.path.join(directory_path, original_filename), os.path.join(directory_path, new_filename))
                print(f'Renamed {original_filename} -> {new_filename}')
