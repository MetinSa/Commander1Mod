import re
import copy
import os
import shutil
from resources.LoadParameterFile import LoadParameterFile

class ConfigureParameterFile(object):
    """Main parameterfile configuration class.

    Handles all functionality considering direct changes to the parameterfile.
    """
    def __init__(self, filename):
        self.filename = filename

        LoadedParams = LoadParameterFile(self.filename)
        self.original_data = LoadedParams.get_json_data(LoadedParams.jsonfilename)    # loaded data which will be edited
        self.json_data = copy.deepcopy(self.original_data)  # Unedited loaded data
        self.masterbands = LoadedParams.get_json_data(LoadedParams.masterbands_jsonfilename)
        self.masterforegrounds = LoadedParams.get_json_data(LoadedParams.masterforegrounds_jsonfilename)
        self.add_space_before = LoadedParams.load_paramfile_format(LoadedParams.formatfile)
        self.band_labels = {}
        self.fg_labels = {}
        self.get_labels()

        self.reference_bands = {}
        self.get_initial_reference_bands()
        self.rename_fg_templates_to_match_bands()

    def get_initial_reference_bands(self):
        """Finds all bands used as reference."""
        reference_band_labels = []
        for fg in self.json_data['Foregrounds']:
            reference_band_labels.append(self.json_data['Foregrounds'][fg].get('REFERENCE_BAND').split()[0])
        for band, label in self.band_labels.items():
            if label in reference_band_labels:
                self.reference_bands.update({band:label})

    def get_labels(self):
        """Gets the label for each band."""
        for i, band in enumerate(self.json_data['Frequency Bands']):
            self.band_labels.update({band:f'{i+1}'})
        for i, fg in enumerate(self.json_data['Foregrounds']):
            self.fg_labels.update({fg:f'{i+1}'})

    def update_reference_band_labels(self):
        """Updates parameterfile reference bands."""
        for fg in self.json_data['Foregrounds']:
            reference_band_label = self.json_data['Foregrounds'][fg].get('REFERENCE_BAND'.split()[0])
            for band, label in self.reference_bands.items():
                if label == reference_band_label:
                    self.json_data['Foregrounds'][fg].update({'REFERENCE_BAND':self.band_labels.get(band)})

    def update_chains_dir(self, new_dir):
        """Updates chain directory."""
        if not new_dir:
            return
        self.json_data['General Settings'].update({'CHAIN_DIRECTORY':f"'{new_dir}'"})

    def update_nside(self, new_nside):
        """Updates NSIDE in all values in parameterfile."""
        allowed_nside = [64, 128, 256, 512, 1024, 2048, 4096]
        if new_nside not in allowed_nside:
            raise ValueError(f'Invalid NSIDE value.')
        self.json_data['General Settings'].update({'NSIDE':new_nside})
        pattern1 = re.compile(r'0064|0128|0256|0512|1024|2048|4096')
        pattern2 = re.compile(r'064|128|256|512|1024|2048|4096')

        def update_dicts(dictionary):
            """Updates single dictionaries in json data."""
            for param, value in dictionary.items():
                match1 = pattern1.search(str(value))
                match2 = pattern2.search(str(value))
                if match1 and param not in ['LMAX', 'LMAX_LOWRES']:
                    dictionary.update({param:re.sub(pattern1, f'{new_nside:04}', str(value))})
                if match2 and param not in ['LMAX', 'LMAX_LOWRES']:
                    dictionary.update({param:re.sub(pattern2, f'{new_nside:03}', str(value))})

        def update_nested_dicts(dictionary):
            """Updates nested dictionaries in json data."""
            for band in dictionary:
                for param, value in dictionary[band].items():
                    match1 = pattern1.search(str(value))
                    match2 = pattern2.search(str(value))
                    if match1 and param not in ['LMAX', 'LMAX_LOWRES']:
                        dictionary[band].update({param:re.sub(pattern1, f'{new_nside:04}', value)})
                    elif match2 and param not in ['LMAX', 'LMAX_LOWRES']:
                        dictionary[band].update({param:re.sub(pattern2, f'{new_nside:03}', value)})

        update_dicts(self.json_data['General Settings'])
        update_dicts(self.json_data['Foreground Templates'])
        update_dicts(self.json_data['Pixel Foreground Parameters'])
        update_dicts(self.json_data['Final Parameters'])
        update_nested_dicts(self.json_data['Frequency Bands'])
        update_nested_dicts(self.json_data['Foregrounds'])

    def toggle_outputs(self, boolean):
        """Sets all output maps to true/false."""
        for param, value in self.json_data['General Settings'].items():
            if 'OUTPUT_FREQUENCY_COMPONENT_MAPS' in param:
                value_items = value.split()
                if len(value_items) > 1:
                    comments = ' '.join(value_items[1:])
                    new_bool_value = f'{boolean:{15}}{comments}'
                else:
                    new_bool_value = boolean
                self.json_data['General Settings'].update({param:new_bool_value})


    def toggle_template_fit(self, band):
        """Sets the value of FIX_TEMP of a band to true/false."""
        for param, value in self.json_data['Foreground Templates'].items():
            if 'FIX' in param and band in param:
                value_items = value.split()
                bool_value = value_items[0]
                if 'true' in bool_value:
                    new_bool_value = '.false.'
                elif 'false' in bool_value:
                    new_bool_value = '.true.'
                if len(value_items) > 2:
                    comments = ' '.join(value_items[1:])
                    new_bool_value = f'{new_bool_value:{15}}{comments}'

                self.json_data['Foreground Templates'].update({param:new_bool_value})

    def update_init_files(self, chain_dir, data_dir, tag, sample):
        """Changes all init files in parameterfile."""
        sample = f'k{int(sample):05}'
        for file in os.listdir(chain_dir):
            if file.endswith(f'{sample}.dat'):
                break
        else:
            raise NameError('Sample does not exist in chain directory.')

        for file in os.listdir(chain_dir):
            if file.startswith('temp_amp') and file.endswith(f'{sample}.dat'):
                new_name = f'temp_amp_init_{tag}.dat'
                new_path = shutil.copy(f'{chain_dir}/{file}', f'{data_dir}/{new_name}')
                self.json_data['General Settings'].update({'TEMPLATE_AMP_INPUT':f'data/{new_name}'})

            elif file.startswith('gain_no') and file.endswith('.dat'):
                new_name = f'gain_init_{tag}.dat'
                new_path = shutil.copy(f'{chain_dir}/{file}', f'{data_dir}/{new_name}')
                self.json_data['General Settings'].update({'GAIN_INIT':f'data/{new_name}'})

            elif file.startswith('bp_no') and file.endswith('.dat'):
                new_name = f'bp_init_{tag}.dat'
                new_path = shutil.copy(f'{chain_dir}/{file}', f'{data_dir}/{new_name}')
                self.json_data['General Settings'].update({'BANDPASS_INIT':f'data/{new_name}'})


        map1_samples = ('beta', 'nup', 'EM')
        map2_samples = ('Td','dbeta', 'alpha', 'T_e')
        for fg in self.json_data['Foregrounds']:
            if 'CO_multiline' not in self.json_data['Foregrounds'][fg].get('COMP_TYPE'):
                for file in os.listdir(chain_dir):
                    if file.startswith(fg) and file.endswith(f'{sample}.fits'):
                        match1 = next((sample for sample in map1_samples if sample in file), False)
                        match2 = next((sample for sample in map2_samples if sample in file), False)
                        if match1:
                            new_name = f'{fg}_{match1}_init_{tag}.fits'
                            new_path = shutil.copy(f'{chain_dir}/{file}', f'{data_dir}/{new_name}')
                            self.json_data['Foregrounds'][fg].update({'INIT_INDEX_MAP_01':f'data/{new_name}'})
                        elif match2:
                            new_name = f'{fg}_{match2}_init_{tag}.fits'
                            new_path = shutil.copy(f'{chain_dir}/{file}', f'{data_dir}/{new_name}')
                            self.json_data['Foregrounds'][fg].update({'INIT_INDEX_MAP_02':f'data/{new_name}'})
                        else:
                            new_name = f'{fg}_init_{tag}.fits'
                            new_path = shutil.copy(f'{chain_dir}/{file}', f'{data_dir}/{new_name}')
                            self.json_data['Foregrounds'][fg].update({'INITIAL_AMPLITUDE_MAP':f'data/{new_name}'})

            else:
                regex_str = f'{fg}_' + r'([^_]+)'
                pattern = re.compile(regex_str)
                bands = []
                for band in self.band_labels:
                    if 'WMAP' in band:
                        band = band.split('_')[-1]
                    bands.append(band)

                for file in os.listdir(chain_dir):
                    if file.startswith(fg) and file.endswith(f'{sample}.fits'):
                        match = pattern.search(file)
                        if match and match.group(1) in bands:
                            band = match.group(1)
                            new_name = f'{fg}_{band}_init_{tag}.fits'
                            new_path = shutil.copy(f'{chain_dir}/{file}', f'{data_dir}/{new_name}')
                            for param, value in self.json_data['Foregrounds'][fg].items():
                                if 'LINE_LABEL' in param and band == value.strip("'"):
                                    line_label = param[-2:]
                                    self.json_data['Foregrounds'][fg].update({f'INIT_INDEX_MAP_{line_label}':f'data/{new_name}'})
                        else:
                            new_name = f'{fg}_init_{tag}.fits'
                            new_path = shutil.copy(f'{chain_dir}/{file}', f'{data_dir}/{new_name}')
                            self.json_data['Foregrounds'][fg].update({'INITIAL_AMPLITUDE_MAP':f'data/{new_name}'})

    def rename_fg_templates_to_match_bands(self):
        """Renames the fg_temp params to match bands."""
        self.json_data['Foreground Templates'].clear()
        pattern = re.compile(r'\D+[_]\D+\d{2}')
        for param, value in self.original_data['Foreground Templates'].items():
            match = pattern.search(param)
            if match:
                related_band_label = str(int(match.group(0)[-2:]))
                for band, label in self.band_labels.items():
                    if label == related_band_label:
                        if 'FG' in param:
                            new_key_name = f'FG_{band}-{param[-2:]}'
                        elif 'FIX' in param:
                            new_key_name = f'FIX_{band}-{param[-2:]}'
                        self.json_data['Foreground Templates'].update({new_key_name:value})
            else:
                self.json_data['Foreground Templates'].update({param:value})

    def delete_band(self, band):
        """Deletes a band, eventual co-lines and updates labeling."""
        band_label = self.band_labels.get(band)
        if band_label is None:
            raise ValueError('Band not recognized.')
        for label in self.reference_bands.values():
            if band_label == label:
                raise ValueError('Cannot delete reference band.')

        self.json_data['Frequency Bands'].pop(band)
        self.band_labels.pop(band)
        self.get_labels()
        self.update_reference_band_labels()

        numbands_value = (self.json_data['General Settings']['NUMBAND']).split()
        numbands = int(numbands_value[0]) - 1
        if len(numbands_value) > 2:
            comment = ' '.join(numbands_value[1:])
            numbands = f'{str(numbands):{15}}{comment}'
        self.json_data['General Settings'].update({'NUMBAND':numbands})

        output_freq_to_delete = [key for key in self.json_data['General Settings'].keys()
                              if 'OUTPUT_FREQUENCY_COMPONENT_MAPS' in key][-1]
        self.json_data['General Settings'].pop(output_freq_to_delete)

        for template in self.json_data['Foreground Templates'].copy().keys():
            if band in template:
                self.json_data['Foreground Templates'].pop(template)

        if 'WMAP' in band:
            band = band.split('_')[-1]
        def delete_co_lines():
            """Removes eventual co-lines connected to the band."""
            for fg in self.json_data['Foregrounds']:
                if 'CO_multiline' in self.json_data['Foregrounds'][fg].get('COMP_TYPE'):
                    for param, value in self.json_data['Foregrounds'][fg].items():
                        if 'LINE_LABEL' in param and value.split()[0].strip("'") == band:
                            fg_label_to_delete = param[-2:]
                            fg_to_update = fg
                            break
            try:
                fg_to_update
            except Exception:
                return

            fg_dict = copy.deepcopy(self.json_data['Foregrounds'][fg_to_update])
            for param in self.json_data['Foregrounds'][fg_to_update].keys():
                if param.endswith(fg_label_to_delete):
                    fg_dict.pop(param)
                elif 'NUM_CO_HARMONICS' in param:
                    num_co_harmonics = int(fg_dict['NUM_CO_HARMONICS']) - 1
                    fg_dict.update({'NUM_CO_HARMONICS':num_co_harmonics})

            fg_dict_final = {}
            pattern = re.compile(r'[_]\d{2}')
            i = 1
            j = 0
            for param, value in fg_dict.items():
                match = pattern.search(param)
                if match:
                    if 'INIT_INDEX_MAP' in param:
                        fg_dict_final.update({f'{param[:-2]}{i:02}':value})
                        i += 1
                    else:
                        if 'LINE_LABEL' in param:
                            j += 1
                        fg_dict_final.update({f'{param[:-2]}{j:02}':value})
                else:
                    fg_dict_final.update({param:value})
            self.json_data['Foregrounds'][fg_to_update] = fg_dict_final

        delete_co_lines()

    def add_band(self, band):
        """Adds a band from masterbandlist."""
        band_data = self.masterbands.get(band)
        if band_data is None:
            raise ValueError('Band not recognized.')

        if band in self.json_data['Frequency Bands']:
            band = f'{band}_template'

        for bandnames in self.band_labels:
            final_band = bandnames

        self.json_data['Frequency Bands'].update({band:band_data})
        numbands_value = (self.json_data['General Settings']['NUMBAND']).split()[0]
        number_of_bands = int(numbands_value[0]) + 1
        if len(numbands_value) > 2:
            comment = ' '.join(numbands_value[1:])
            numbands = f'{str(number_of_bands):{15}}{comment}'
        self.json_data['General Settings'].update({'NUMBAND':numbands})
        self.band_labels.update({band:str(number_of_bands)})

        output_freqs = [key for key, value in self.json_data['General Settings'].items()
                              if 'OUTPUT_FREQUENCY_COMPONENT_MAPS' in key]
        if len(output_freqs) < number_of_bands:
            general_settings = copy.deepcopy(self.json_data['General Settings'])
            updated_general_settings = {}
            for param, value in general_settings.items():
                updated_general_settings.update({param:value})
                if param.endswith(f'{number_of_bands-1:02}'):
                    updated_general_settings.update({f'{param[:-2]}{number_of_bands:02}':value})
            self.json_data['General Settings'] = updated_general_settings

        fg_templates = copy.deepcopy(self.json_data['Foreground Templates'])
        updated_fg_templates = {}
        for param, value in fg_templates.items():
            updated_fg_templates.update({param:value})
            if final_band in param:
                if 'FG' in param:
                    param = f'FG_{band}-{param[-2:]}'
                    value = f'----INSERT_TEMPLATE_FOR_{band}_HERE----'
                elif 'FIX' in param:
                    param = f'FIX_{band}-{param[-2:]}'
                updated_fg_templates.update({param:value})
        self.json_data['Foreground Templates'] = updated_fg_templates

        def add_co_lines():
            """Adds co-line templates."""
            if 'template' in band:
                band_name = re.sub(r'_template', '', band)
            else:
                band_name = band

            data = self.original_data['Foregrounds']
            for fg in data:
                if 'CO_multiline' in data[fg].get('COMP_TYPE'):
                    for param, value in data[fg].items():
                        if 'LINE_LABEL' in param and value.split()[0].strip("'") == band_name:
                            fg_to_update = fg
                            break
            try:
                fg_to_update
            except Exception:
                return

            fg_dict = copy.deepcopy(self.json_data['Foregrounds'][fg_to_update])
            line_format = {}
            i = 0

            for param, value in data[fg_to_update].items():
                if 'NUM_CO_HARMONICS' in param:
                    num_co_harmonics = int(fg_dict['NUM_CO_HARMONICS'].split()[0]) + 1
                    fg_dict.update({'NUM_CO_HARMONICS':num_co_harmonics})
                elif 'LINE_LABEL' in param:
                    i += 1
                if i == 1:
                    line_format.update({param:value})

            fg_dict_final = {}
            for param, value in fg_dict.items():
                if 'NUM_CO_HARMONICS' in param:
                    fg_dict_final.update({f'INIT_INDEX_MAP_{num_co_harmonics:02}':f"'----INSERT_INIT_INDEX_MAP_FOR_BAND_{band}_HERE----'"})
                elif param == f'CO_PRIOR_GAUSSIAN_STDDEV_{(num_co_harmonics-1):02}':
                    for param, value in line_format.items():
                        if 'LINE_LABEL' in param:
                            value = f"'{band}'"
                        fg_dict_final.update({f'{param[:-2]}{num_co_harmonics:02}':value})
                fg_dict_final.update({param:value})
            self.json_data['Foregrounds'][fg_to_update] = fg_dict_final

        add_co_lines()

    def delete_foreground(self, foreground):
        """Removes a foreground from the parameterfile."""
        foreground_data = self.json_data['Foregrounds'].get(foreground)
        if foreground_data is None:
            raise ValueError('Foreground not recognized.')

        self.json_data['Foregrounds'].pop(foreground)
        self.fg_labels.pop(foreground)

    def add_foreground(self, foreground):
        """Adds a foreground from the masterforegrounds."""
        foreground_data = self.masterforegrounds.get(foreground)
        if foreground_data is None:
            raise ValueError('Foreground not recognized.')
        if foreground in self.json_data['Foregrounds']:
            foreground = f'{foreground}_template'

        self.json_data['Foregrounds'].update({foreground:foreground_data})
        self.fg_labels.update({foreground:str(len(self.json_data['Foregrounds']))})

    def write_to_file(self, filename):
        """Outputs the settings to file in a typical Commander1 format."""
        format_width = 40

        def write_general_settings():
            """Writes general settings to file."""
            with open(filename, 'w') as f:
                f.write('# Parameter file for Commander1 - Generated by Commander1 Module\n')
                for param, value in self.json_data['General Settings'].items():
                    if param in self.add_space_before:
                        f.write('\n')
                    f.write(f'{param:{format_width}}= {value}\n')

        def write_frequency_bands():
            """Writes frequency bands to file."""
            with open(filename, 'a') as f:
                for i, band in enumerate(self.json_data['Frequency Bands']):
                    f.write(f'\n# ------------ {band}\n')
                    for param, value in self.json_data['Frequency Bands'].get(band).items():
                        if 'MAP' in param:
                            param_comps = param.split('_')
                            param = f'{param_comps[0]}{i+1:02}_{param_comps[1]}'
                        else:
                            param = f'{param}{i+1:02}'
                        f.write(f'{param:{format_width}}= {value}\n')

        def write_fg_templates():
            """Writes fg_templates to file."""
            with open(filename, 'a') as f:
                f.write('\n# Foreground templates\n')
                for param, value in self.json_data['Foreground Templates'].items():
                    for band, label in self.band_labels.items():
                        if band in param:
                            fg_label = int(label)
                    if 'NUM' in param:
                        pass
                    elif 'FG' in param:
                        param = f'FG_TEMPLATE{fg_label:02}_{param[-2:]}'
                    elif 'FIX' in param:
                        param = f'FIX_TEMP{fg_label:02}_{param[-2:]}'
                    if param in self.add_space_before:
                        f.write('\n')
                    f.write(f'{param:{format_width}}= {value}\n')

        def write_pixel_fg_parameters():
            """Writes pixel_fg parameters to file."""
            with open(filename, 'a') as f:
                f.write('\n# Pixel foreground parameters\n')
                for param, value in self.json_data['Pixel Foreground Parameters'].items():
                    if param in self.add_space_before:
                        f.write('\n')
                    f.write(f'{param:{format_width}}= {value}\n')

        def write_foregrounds():
            """Writes foregrounds to file."""
            special_format_params = ['INIT_INDEX_MAP', 'REGION_DEFINITION', 'FWHM_PAR',
                                     'LINE_LABEL', 'BAND', 'DEFAULT_CO_LINE_RATIO',
                                     'CO_PRIOR']
            with open(filename, 'a') as f:
                for i, fg in enumerate(self.json_data['Foregrounds']):
                    f.write(f'\n\n# ------------ {fg}\n')
                    for param, value in self.json_data['Foregrounds'].get(fg).items():
                        if any(substring in param for substring in self.add_space_before):
                            f.write('\n')
                        if (any(substring in param for substring in special_format_params)
                            and 'REFERENCE' not in param):
                            param_comps = param.rsplit('_', 1)
                            param = f'{param_comps[0]}{i+1:02}_{param_comps[1]}'
                        else:
                            if 'OUTPUT_CMB_FREQUENCY' in param:
                                param = f'{param}PS'
                            else:
                                param = f'{param}{i+1:02}'
                        f.write(f'{param:{format_width}}= {value}\n')

        def write_remaining_params():
            """Writes all remaining parameters to file."""
            with open(filename, 'a') as f:
                f.write('\n\n# Object list for individual output\n')
                for param, value in self.json_data['Final Parameters'].items():
                    if param in self.add_space_before:
                        f.write('\n')
                    f.write(f'{param:{format_width}}= {value}\n')

        write_general_settings()
        write_frequency_bands()
        write_fg_templates()
        write_pixel_fg_parameters()
        write_foregrounds()
        write_remaining_params()

if __name__ == '__main__':
    ConfigParams = ConfigureParameterFile('param.txt')
    # ConfigParams.delete_band('044')
    # ConfigParams.add_band('044')
    # ConfigParams.update_nside(64)
    # ConfigParams.add_foreground('dust')
    # ConfigParams.toggle_template_fit('044')
    # ConfigParams.write_to_file('test.txt')
