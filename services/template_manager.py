# File: transcribe_audio_service/services/template_manager.py

import os
import json
import csv
from copy import deepcopy
from xml.etree.ElementTree import ElementTree
from services.constants import FORMATS_REQUIRING_TEMPLATES, SUPPORTED_OUTPUT_EXTENSIONS


class TemplateManager:
    def __init__(self, template_dir="templates"):
        base_dir = os.path.dirname(os.path.abspath(__file__))  # full path to services/
        self.template_dir = os.path.join(base_dir, "..", template_dir)  # navigate to project root / templates/
        self._json = None
        self._xml = None
        self._csv_headers = None
        self._txt_template = None

    def get_template(self, fmt):
        fmt = fmt.lower()

        if fmt not in SUPPORTED_OUTPUT_EXTENSIONS:
            raise ValueError(f"Unsupported output format: {fmt}")

        if fmt not in FORMATS_REQUIRING_TEMPLATES:
            return None  #parquet, srt, vtt don’t need templates

        loader_map = {
            "json": self._get_json,
            "xml": lambda: self._get_xml().getroot(),
            "csv": self._get_csv_headers,
            "txt": self._get_txt_template
        }

        loader = loader_map.get(fmt)
        if loader:
            return deepcopy(loader()) if fmt == "json" else loader()
        else:
            raise ValueError(f"No loader defined for format: {fmt}")

    def _get_json(self):
        if self._json is None:
            path = os.path.join(self.template_dir, "transcript_template.json")
            with open(path, "r", encoding="utf-8") as f:
                self._json = json.load(f)
        return self._json

    def _get_xml(self):
        if self._xml is None:
            path = os.path.join(self.template_dir, "transcript_template.xml")
            self._xml = ElementTree()
            self._xml.parse(path)
        return self._xml

    def _get_csv_headers(self):
        if self._csv_headers is None:
            path = os.path.join(self.template_dir, "transcript_template.csv")
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                self._csv_headers = next(reader)  # read first (header) row
        return self._csv_headers

    def _get_txt_template(self):
        if self._txt_template is None:
            path = os.path.join(self.template_dir, "transcript_template.txt")
            with open(path, "r", encoding="utf-8") as f:
                self._txt_template = f.read()
        return self._txt_template
