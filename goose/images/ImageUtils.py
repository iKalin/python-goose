# -*- coding: utf-8 -*-
"""\
This is a python port of "Goose" orignialy licensed to Gravity.com
under one or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.

Python port was written by Xavier Grangier for Recrutae

Gravity.com licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import hashlib
import os
import urllib2
from PIL import Image
from goose.utils.encoding import smart_str
from goose.images.ImageDetails import ImageDetails
from goose.images.ImageExtractor import LocallyStoredImage

class ImageUtils(object):
    details = {}

    @classmethod
    def getPngInfo(self, data):
        if data[12:16] != 'IHDR': return None
        imageDetails = ImageDetails()
        imageDetails.setMimeType('png')
        imageDetails.setWidth(int(data[16:20].encode('hex'),16))
        imageDetails.setHeight(int(data[20:24].encode('hex'),16))
        imageDetails.size = len(data)
        return imageDetails

    @classmethod
    def getGifInfo(self, data):
        imageDetails = ImageDetails()
        imageDetails.setMimeType('gif')
        imageDetails.setWidth(ord(data[6])+ord(data[7])*256)
        imageDetails.setHeight(ord(data[8])+ord(data[9])*256)
        imageDetails.size = len(data)
        return imageDetails

    @classmethod
    def getJpegInfo(self, data, pos = 2):
        if data[pos] != '\xff': return None
        pos += 1;
        if data[pos] in ['\xc0','\xc1','\xc2','\xc3']:
            pos += 4
            imageDetails = ImageDetails()
            imageDetails.setMimeType('jpg')
            imageDetails.setWidth(ord(data[pos+2])*256 + ord(data[pos+3]))
            imageDetails.setHeight(ord(data[pos])*256 + ord(data[pos+1]))
            imageDetails.size = len(data)
            return imageDetails
        pos += 1;
        delta = ord(data[pos])*256 + ord(data[pos+1])
        return self.getJpegInfo(data, pos + delta)

    @classmethod
    def getImageInfo(self, data):
        try:
            if data[1:4] == 'PNG': 
                return self.getPngInfo(data)
            elif data[0] == '\xff' and data[1] == '\xd8': 
                return self.getJpegInfo(data)
            elif data[0:3] == 'GIF': 
                return self.getGifInfo(data)
            else: return None
        except:
            return None

    @classmethod
    def storeImageToLocalFile(self, httpClient, linkhash, imageSrc, config):
        """\
        Writes an image src http string to disk as a temporary file
        and returns the LocallyStoredImage object
        that has the info you should need on the image
        """
        # check for a cache hit already on disk
        image = self.readExistingFileInfo(linkhash, imageSrc, config)
        if image:
            return image

        # no cache found download the image
        data = self.fetchEntity(httpClient, imageSrc)
        if data:
            image = self.writeEntityContentsToDisk(data, linkhash, imageSrc, config)
            if image:
                return image

        return None

    @classmethod
    def getFileExtensionName(self, imageDetails):
        mimeType = imageDetails.getMimeType().lower()
        mimes = {
            'png': '.png',
            'jpg': '.jpg',
            'jpeg': '.jpg',
            'gif': '.gif',
        }
        return mimes.get(mimeType, 'NA')

    @classmethod
    def readExistingFileInfo(self, linkhash, imageSrc, config):
        localImageName = self.getLocalFileName(linkhash, imageSrc, config)
        if localImageName in ImageUtils.details:
            identify = config.imagemagickIdentifyPath
            imageDetails = ImageUtils.details[localImageName]
            fileExtension = self.getFileExtensionName(imageDetails)
            return LocallyStoredImage(
                imgSrc=imageSrc,
                localFileName=localImageName,
                linkhash=linkhash,
                bytes=imageDetails.getSize(),
                fileExtension=fileExtension,
                height=imageDetails.getHeight(),
                width=imageDetails.getWidth()
            )
        return None

    @classmethod
    def writeEntityContentsToDisk(self, entity, linkhash, imageSrc, config):
        localSrcPath = self.getLocalFileName(linkhash, imageSrc, config)
        ImageUtils.details[localSrcPath] = self.getImageInfo(entity)
        if ImageUtils.details[localSrcPath] is None:
            ImageUtils.details[localSrcPath] = ImageDetails()
        return self.readExistingFileInfo(linkhash, imageSrc, config)

    @classmethod
    def getLocalFileName(self, linkhash, imageSrc, config):
        imageHash = hashlib.md5(smart_str(imageSrc)).hexdigest()
        return config.localStoragePath + "/" + linkhash + "_py_" + imageHash

    @classmethod
    def purgeStoredDetails(self, linkhash, config):
        path = config.localStoragePath + "/" + linkhash + "_py_"
        to_del = []
        for k in ImageUtils.details:
            if k.startswith(path): to_del.append(k)
        for k in to_del: del ImageUtils.details[k]

    @classmethod
    def cleanImageSrcString(self, imgSrc):
        return imgSrc.replace(" ", "%20")

    @classmethod
    def fetchEntity(self, httpClient, imageSrc):
        try:
            req = urllib2.Request(imageSrc)
            f = urllib2.urlopen(req)
            data = f.read()
            return data
        except:
            return None
