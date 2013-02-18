#!/usr/bin/env python
# -*- coding: utf-8 -*- 
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
"""WriteBuffer Object"""
__author__ = "Arthur Messner <arthur.messner@gmail.com>"
__copyright__ = "Copyright (c) 2013 Arthur Messner"
__license__ = "GPL"
__version__ = "$Revision$"
__date__ = "$Date$"
# $Id

import time
import logging


class WriteBuffer(object):
    """Object to hold data with maximum length blocksize, the flush"""

    def __init__(self, meta_storage, block_storage, blocksize, hashfunc):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.ERROR)
        self.logger.debug("WriteBuffer.__init__()")
        self.blocksize = blocksize
        self.hashfunc = hashfunc
        self.meta_storage = meta_storage
        self.block_storage = block_storage
        self.__reinit()

    def flush(self):
        """write self.buf to block_storage"""
        self.logger.debug("WriteBuffer.flush()")
        # flush self.buf
        # blocklevel hash
        blockhash = self.hashfunc()
        blockhash.update(self.buf)
        # filelevel hash
        self.filehash.update(self.buf)
        self.bytecounter += len(self.buf)
        # dedup
        if self.deduphash.has_key(blockhash.hexdigest()):
            self.deduphash[blockhash.hexdigest()] += 1
        else:
            self.deduphash[blockhash.hexdigest()] =1
            # store
            self.block_storage.put(self.buf, blockhash.hexdigest())
        # store in sequence of blocks
        self.sequence.append(blockhash.hexdigest())

    def add(self, data):
        """adds data to buffer and flushes if length > blocksize"""
        # self.logger.debug("WriteBuffer.add(<buf>)")
        if (len(self.buf) + len(data)) >= self.blocksize:
            # add only remaining bytes to internal buffer
            self.buf += data[:self.blocksize-len(self.buf)]
            # self.logger.debug("Buffer flush")
            # assert len(self.buf) == self.blocksize
            self.flush()
            # begin next block buffer
            self.buf = data[self.blocksize:]
        else:
            # self.logger.debug("Adding buffer")
            # assert len(self.buf) < self.blocksize
            self.buf += data
        return(len(data))

    def __reinit(self):
        """set some coutners to zero"""
        self.logger.debug("WriteBuffer.__reinit()")
        self.buf = ""
        # counting bytes = len
        self.bytecounter = 0
        # hash for whole file
        self.filehash = self.hashfunc()
        # starttime
        self.starttime = time.time()
        # deduphash
        self.deduphash = {}
        # sequence of blocks
        self.sequence = []

    def release(self):
        """write remaining data, and closes file"""
        self.logger.debug("WriteBuffer.release()")
        if len(self.buf) != 0:
            self.logger.debug("adding remaining data")
            self.flush()
        self.logger.debug("File was %d bytes long", self.bytecounter)
        duration = time.time() - self.starttime
        self.logger.debug("Duration %s seconds", duration)
        self.logger.debug("Speed %0.2f B/s", self.bytecounter / duration)
        # write meta information
        # save informations for return
        filehash = self.filehash.hexdigest()
        sequence = self.sequence
        size = self.bytecounter
        # reinitialize counters for next file
        self.__reinit()
        return(filehash, sequence, size)
