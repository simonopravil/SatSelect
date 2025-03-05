import ee

def MosaicByDate(originalCollection):
    
    def unique_values(collection, field):
        values = ee.Dictionary(collection.reduceColumns(ee.Reducer.frequencyHistogram(), [field]).get('histogram')).keys()
        return values

    def daily_mosaics(imgs):

        def simplifyDate(img):
            d = ee.Date(img.get('system:time_start'))
            day = d.get('day')
            m = d.get('month')
            y = d.get('year')
            simpleDate = ee.Date.fromYMD(y,m,day)
            return img.set('simpleTime',simpleDate.millis())

        imgs = imgs.map(simplifyDate)
        days = unique_values(imgs,'simpleTime')

        def do_mosaic(d):
            d = ee.Number.parse(d)
            d = ee.Date(d)
            t = imgs.filterDate(d,d.advance(1,'day')).sort('order').sort('CLOUD_COVER')
            f = ee.Image(t.first())
            t = t.mosaic()
            t = t.set('system:time_start',d.millis())
            t = t.copyProperties(f)
            return t

        imgs = days.map(do_mosaic)
        
        return ee.ImageCollection.fromImages(imgs)
    
    mosaiked = daily_mosaics(originalCollection)
    return mosaiked