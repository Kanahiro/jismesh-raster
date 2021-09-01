import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))
from jismesh_raster.rasterize import rasterize  # nopep8


noaggr_basename = os.path.join(
    os.path.dirname(__file__), "fixture", "noaggr")
noheader_basename = os.path.join(
    os.path.dirname(__file__), "fixture", "noheader")
aggr_basename = os.path.join(
    os.path.dirname(__file__), "fixture", "aggr")


def noaggr_rasterize(args):
    return lambda: rasterize(csvfile=noaggr_basename + ".csv",
                             output=noaggr_basename + ".tif",
                             **args)


def noheader_rasterize(args):
    return lambda: rasterize(csvfile=noheader_basename + ".csv",
                             output=noheader_basename + ".tif",
                             **args)


def aggr_rasterize(args):
    return lambda: rasterize(csvfile=aggr_basename + ".csv",
                             output=aggr_basename + ".tif",
                             **args)


class TestRasterize(unittest.TestCase):

    def test_rasterize(self):
        # 1meshcode:1record csv, with header
        noaggr_rasterize({"meshcol": 0, "valuecol": 7})()
        noaggr_rasterize({"valuecol": 7})()
        with self.assertRaises(Exception):
            noaggr_rasterize({"valuecol": 7, "noheader": True})()

        # 1meshcode:1record csv, with no-header
        noheader_rasterize({"valuecol": 7})()
        noheader_rasterize({"valuecol": 7, "noheader": True})()

        # 1meshcode: n-records csv, with header
        with self.assertRaises(Exception):
            # aggr_method must be defined when n-records
            aggr_rasterize({"valuecol": 7})()
        aggr_rasterize({"valuecol": 7, "aggr_method": "mean"})()
        aggr_rasterize({"valuecol": 7, "aggr_method": "median"})()
        aggr_rasterize({"valuecol": 7, "aggr_method": "min"})()
        aggr_rasterize({"valuecol": 7, "aggr_method": "max"})()
        aggr_rasterize({"valuecol": 7, "aggr_method": "sum"})()
        aggr_rasterize({"valuecol": 7, "aggr_method": "stddev"})()
        with self.assertRaises(Exception):
            aggr_rasterize({"valuecol": 7, "aggr_method": "incorrectname"})()
