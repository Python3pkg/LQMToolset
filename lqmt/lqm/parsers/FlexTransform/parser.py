"""
Created on Jan 12, 2015

@author: taxon
"""
import FlexTransform
from lqmt.lqm.data import Alert
import os
import inspect
import logging
import io


class FlexTransformParser(object):
    def __init__(self, config=None):
        self._logger = logging.getLogger("LQMT.Parsers")

        # get the FlexTransform directory
        self._current_dir, name = os.path.split(inspect.getfile(FlexTransform.FlexTransform))
        self._transform = FlexTransform.FlexTransform.FlexTransform()

        # config
        if config is not None:
            for p, c in config.items():
                self.add_parser(p, c)

    def add_parser(self, parserName, parserConfiguration):
        """
        Function that extends the AddParser function from FlexTransform.
        :param parserName: Name of the parser being added
        :param parserConfiguration: Path to the configuration file being added
        """
        if parserName not in self._transform.Parsers:
            config_file = open(os.path.join(self._current_dir, parserConfiguration), 'r')
            self._transform.add_parser(parserName, config_file)

    def parse(self, datafile, meta=None):
        """
        Parse the datafile using the metadata dictionary.

        Note: Removed sourceMetaData from the parser for now due to conflicts with STIX-TLP. Currently assessing
        if it needs to be included. Currently the meta file is just being used to identify the sourceParser.

        :param datafile: Contains path to the file containing the alert data.
        :param meta: Contains meta data about the datafile. Examples includes PayloadFormat, FileName, PayloadType, and
        more.
        :return: Returns parsed alert data.
        """
        alerts = []

        # TODO: Stix-tlp parser currently doesn't support meta files. Until it does, meta files are for the cfm format
        try:
            if meta['PayloadFormat'] == 'stix-tlp' or meta is None:
                data = self._transform.transform(
                    datafile,
                    meta['PayloadFormat'],
                    "LQMTools"
                )
            else:
                data = self._transform.transform(
                    datafile,
                    meta['PayloadFormat'],
                    "LQMTools",
                    source_meta_data=meta
                )

        except Exception as e:
            data = []
            self._logger.error(
                "LQMT-FlexTransform-Parser: Error parsing file file='{0}' exception='{1}'".format(datafile, e))
        for d in data:
            alert = Alert()
            alert.setFromDict(d)
            alerts.append(alert)

        return alerts

    def parseflextext(self, datafile, meta, destination_file_obj, config_str):
        """
        Flextext parser. Transforms intermediate data into a user defined structure.

        :param datafile: dir path to the alert datafile that will be transformed
        :param meta: Contains meta data about the datafile. Examples includes PayloadFormat, FileName, PayloadType, and
        more.
        :param destination_file_obj: File object used to write contents to file.
        :param config_str: Parser configuration in the form of a string. Is wrapped in an IO wrapped and then passed
        to FlexT to configure FlexText parser
        :return: Returns none. Data is outputted to file specified by destination_file_obj
        """

        # Add FlexText parser using config_str wrapped in StringIO object
        if 'FlexText' not in self._transform.Parsers:
            config_str_io = io.StringIO(config_str)
            config_str_txt = io.StringIO(config_str_io.read())
            self._transform.add_parser("FlexText", config_str_txt)

        # Run FlexText parser
        try:
            if meta['PayloadFormat'] == 'stix-tlp':
                self._transform.transform(
                    datafile,
                    meta['PayloadFormat'],
                    "FlexText",
                    target_file=destination_file_obj
                )

            else:
                self._transform.transform(
                    datafile,
                    meta['PayloadFormat'],
                    "FlexText",
                    target_file=destination_file_obj,
                    source_meta_data=meta
                )

        except Exception as e:
            self._logger.error(
                "LQMT-FlexText-Parser: Error parsing file file='{0}' exception='{1}'".format(datafile, e))

    def custom_parser(self, datafile, payloadformat, targetparser, meta=None):
        output = None
        try:
            output = self._transform.transform(
                datafile,
                payloadformat,
                targetparser,
                source_meta_data=meta
            )
        except Exception as e:
            self._logger.error("LQMT-Custom-Parser: Error parsing file. file='{0}' exception='{1}'".format(datafile, e))

        return output
