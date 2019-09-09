import json
import re
import os

class LoadParameterFile(object):
    """Class which parses a Commander1 parameterfile into a json datafile."""
    def __init__(self, filename):

        self.filename = filename
        self.formatfile = '../data/format.txt'
        self.jsonfilename = '../data/param.json'
        self.masterbands_filename = '../data/masterbands.txt'
        self.masterbands_jsonfilename = '../data/masterbands.json'
        self.masterforegrounds_filename = '../data/masterforegrounds.txt'
        self.masterforegrounds_jsonfilename = '../data/masterforegrounds.json'

        self.general_settings = {}
        self.frequency_bands = {}
        self.masterbands = {}
        self.fg_templates = {}
        self.fg_pix = {}
        self.foregrounds = {}
        self.masterforegrounds = {}
        self.remaining_content = {}

        self.load_data()
        self.build_json_objects()

    def load_paramfile_format(self, formatfile):
        """Loads the format of typical parameterfiles."""
        format_items = []
        with open(formatfile, 'r') as f:
            for line in f:
                format_items.append(line.split()[0])
        return format_items

    def find_sections(self):
        """Returns the different sections of the Commander1 parameterfile."""
        section_ranges = []
        located_sections = []
        with open(self.filename, 'r') as f:
            for i, line in enumerate(f):
                if 'FREQ_LABEL' in line and 'FREQ_LABEL' not in located_sections:
                    section_ranges.append(i)
                    located_sections.append('FREQ_LABEL')
                if 'NUM_FG_TEMP' in line and 'NUM_FG_TEMP' not in located_sections:
                    section_ranges.append(i)
                    located_sections.append('NUM_FG_TEMP')
                if 'T_CMB' in line and 'T_CMB' not in located_sections:
                    section_ranges.append(i)
                    located_sections.append('T_CMB')
                if 'COMP_TYPE' in line and 'COMP_TYPE' not in located_sections:
                    section_ranges.append(i)
                    located_sections.append('COMP_TYPE')
                if 'NUM_OBJECTS' in line and 'NUM_OBJECTS' not in located_sections:
                    section_ranges.append(i)
                    located_sections.append('NUM_OBJECTS')

        with open(self.filename, 'r') as f:
            parameter_file = f.readlines()
            try:
                general_settings_section = parameter_file[0:section_ranges[0]]
                frequency_bands_section = parameter_file[section_ranges[0]:section_ranges[1]]
                fg_temp_section = parameter_file[section_ranges[1]:section_ranges[2]]
                pix_fg_section = parameter_file[section_ranges[2]:section_ranges[3]]
                foreground_section = parameter_file[section_ranges[3]:section_ranges[4]]
                remaining_content =  parameter_file[section_ranges[4]:]
            except IndexError:
                raise IndexError('Parameterfile does not match format of typical Commander1 parameterfiles.')

            return(general_settings_section, frequency_bands_section, fg_temp_section,
                   pix_fg_section, foreground_section, remaining_content)

    def load_data(self):
        """Loading data from the parameterfile."""
        def get_line_content(line):
            line_items = line.split()
            param = line_items[0]
            if len(line_items) > 2:
                value_and_comment = ' '.join(line_items[2:])
                if '#' in value_and_comment:
                    value = value_and_comment.split('#', 1)[0]
                    comment = value_and_comment.split('#', 1)[1]
                    value = f'{value:{15}}#{comment}'
                else:
                    value = value_and_comment
            else:
                value = line_items[2]
            return param, value

        def load_parameters(section, dictionary):
            """Reading and loading parameters."""
            for line in section:
                if "=" in line:
                    param, value = get_line_content(line)
                    dictionary.update({param:value})

        def load_frequency_bands(section):
            """Reading and loading all frequency bands."""
            frequency_bands = section
            i = 0
            for line in frequency_bands:
                if "=" in line:
                    param, value = get_line_content(line)
                    if "FREQ_LABEL" in param:
                        if i > 0:
                            self.frequency_bands.update({newband:newband_params})
                        newband = value.strip("'")
                        newband_params = {}
                        i += 1
                    if "MAP" in param:
                        param = "MAP_0001"
                    else:
                        param = param[:-2]
                    newband_params.update({param:value})
            self.frequency_bands.update({newband:newband_params})

        def load_foregrounds(section):
            """Reading and loading all foregrounds."""
            foregrounds = section
            pattern = re.compile(r'\d{2}[_]\d{2}')
            pattern_values_with_space = re.compile(r"[']{1}[^']+[']{1}")
            i = 0
            for line in foregrounds:
                if "=" in line:
                    param, value = get_line_content(line)
                    match = pattern.search(param)
                    if "COMP_TYPE" in param:
                        if i > 0:
                            self.foregrounds.update({newfg:newfg_params})
                        i += 1
                        newfg_params = {}
                    if "FG_LABEL" in param:
                            newfg = value.strip("'")
                    if match:
                        param = re.sub(pattern,match.group(0)[2:],param)
                    else:
                        param = param[:-2]
                    newfg_params.update({param:value})
            self.foregrounds.update({newfg:newfg_params})

        def load_masterbands(filename):
            """Loads all known frequency bands."""
            with open(filename, 'r') as f:
                masterbands = f.readlines()

            i = 0
            for line in masterbands:
                if "=" in line:
                    param = line.split()[0]
                    value = line.split()[2]
                    if "FREQ_LABEL" in param:
                        if i > 0:
                            self.masterbands.update({newband:newband_params})
                        newband = value.strip("'")
                        newband_params = {}
                        i += 1
                    if "MAP" in param:
                        param = "MAP_0001"
                    else:
                        param = param[:-2]
                    newband_params.update({param:value})
            self.masterbands.update({newband:newband_params})

        def load_masterforegrounds(filename):
            """Loads all known foregrounds."""
            with open(filename, 'r') as f:
                masterforegrounds = f.readlines()

            pattern = re.compile(r'\d{2}[_]\d{2}')
            pattern_values_with_space = re.compile(r"[']{1}[^']+[']{1}")
            i = 0
            for line in masterforegrounds:
                if "=" in line:
                    param = line.split()[0]
                    value = line.split()[2]
                    if len(line.split()) > 2:
                        match = pattern_values_with_space.search(line)
                        if match:
                            value = match.group(0)
                    match = pattern.search(param)
                    if "COMP_TYPE" in param:
                        if i > 0:
                            self.masterforegrounds.update({newfg:newfg_params})
                        i += 1
                        newfg_params = {}
                    if "FG_LABEL" in param:
                            newfg = value.strip("'")
                    if match:
                        param = re.sub(pattern,match.group(0)[2:],param)
                    else:
                        param = param[:-2]
                    newfg_params.update({param:value})
            self.masterforegrounds.update({newfg:newfg_params})

        general_section, frequency_section, fg_temp_section, pix_section,\
             foreground_section, remaining_content = self.find_sections()

        load_parameters(general_section, self.general_settings)
        load_frequency_bands(frequency_section)
        load_masterbands(self.masterbands_filename)
        load_parameters(fg_temp_section, self.fg_templates)
        load_parameters(pix_section, self.fg_pix)
        load_foregrounds(foreground_section)
        load_masterforegrounds(self.masterforegrounds_filename)
        load_parameters(remaining_content, self.remaining_content)

    def build_json_objects(self):
        """Creates a json-object out of the loaded data and writes it to file."""
        json_data = {}
        json_data['General Settings'] = self.general_settings
        json_data['Frequency Bands'] = self.frequency_bands
        json_data['Foreground Templates'] = self.fg_templates
        json_data['Pixel Foreground Parameters'] = self.fg_pix
        json_data['Foregrounds'] = self.foregrounds
        json_data['Final Parameters'] = self.remaining_content

        with open(self.jsonfilename, 'w') as f:
            json.dump(json_data, f, indent=4)
        with open(self.masterbands_jsonfilename, 'w') as f:
            json.dump(self.masterbands, f, indent=4)
        with open(self.masterforegrounds_jsonfilename, 'w') as f:
            json.dump(self.masterforegrounds, f, indent=4)

    def get_json_data(self, filename):
        """Reads data from a json-object."""
        with open(filename, 'r') as f:
            data = json.load(f)
        return data

if __name__ == "__main__":
    LoadedParams = LoadParameterFile("param_tutorial.txt")
    # json_data = LoadedParams.get_json_data(LoadedParams.jsonfilename)
    # masterfgs = LoadedParams.get_json_data(LoadedParams.masterforegrounds_jsonfilename)
    # print(masterfgs)
