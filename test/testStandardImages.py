import MainAnalysis as ma
import ExpFile as exp
import MatplotlibPlotters as mp
import numpy as np

exp.setPath('23','June','2021')
ee = exp.ExpFile(25)
key, rawData, dataMinusBg, dataMinusAvg, avgPic,\
pictureFitParams, pictureFitErrors, plottedData,\
v_params, v_errs, h_params, h_errs, intRawData = \
ma.standardImages(25,loadType='mako',cameraType='mako',
                  key = np.broadcast_to( ee.get_key()[1],(50,41)).flatten(),
                  fitPics=True)


# ma.standardImages(25,loadType='mako',key = np.broadcast_to( ee.get_key()[1],(50,41)).flatten())