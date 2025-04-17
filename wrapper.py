import ee
from procesCollection import sentinel2_preproc, landsat_preproc
from cloudmask import apply_cs_plus_mask, mask_landsat_with_conf, compute_cloud_cover
from mosaic import MosaicByDate, mosaic_imgcol
from reproject import repr, res
from histogram_matching import prep_landsat, match_histograms
from indices import apply_indices

def run_processing(params):
    aoi = params['aoi']
    startDate = params['startDate']
    endDate = params['endDate']
    tileCldFilter = params['tileCldFilter']
    maskBands = params['s2_score+_cloudBand']
    maskConf = params['s2_maskConf']
    useLandsat = params['useLandsat']
    maskConf_L = params['l_maskConf']
    applyMosaic = params['applyMosaic']
    applyHistMatch = params['applyHistMatch']
    applyHistMatchBands = params['applyHistMatchBands']
    indices = params['indices'] # could be empty, or combinations


    SENTINEL = sentinel2_preproc(aoi, startDate, endDate, tileCldFilter)
    SENTINEL = apply_cs_plus_mask(SENTINEL, maskBands, maskConf)
    SENTINEL = apply_indices(SENTINEL, indices)
    SENTINEL = SENTINEL.map(compute_cloud_cover(aoi)).filter(ee.Filter.gte('cloud_cover_roi', 0.1))

    if applyMosaic == True:
        SENTINEL = mosaic_imgcol(SENTINEL)

    if applyHistMatch == True:
        landsat_8_col = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
            .filterBounds(aoi)
            .map(prep_landsat)
        )
        landsat_8_col = apply_indices(landsat_8_col, indices)
        SENTINEL = SENTINEL.select('blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'ndvi').map(lambda img: match_histograms(img, landsat_8_col, aoi, days=40))
        SENTINEL = SENTINEL.map(lambda i: i.set('satellite', 'S2'))

    
    if useLandsat == True:
        LANDSAT = landsat_preproc(aoi, startDate, endDate, tileCldFilter)
        LANDSAT = mask_landsat_with_conf(LANDSAT, 'Medium')
        LANDSAT = apply_indices(LANDSAT, indices)
        LANDSAT = LANDSAT.filter(ee.Filter.calendarRange(4, 9, 'month'))
        
        return SENTINEL.merge(LANDSAT).sort("system:time_start") 
    else:
        return SENTINEL