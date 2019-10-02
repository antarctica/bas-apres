import unittest
from unittest.mock import Mock, patch
import os
 
import numpy as np

from apres.apres import ApRESFile

class TestApRESFile(unittest.TestCase):

    base = os.path.dirname(__file__)

    def test_store_header_ok(self):
        f = ApRESFile('non-existent-file')
        f.header_lines = ['Temp1=10.0469','Temp2=10.1094','BatteryVoltage=12.2058']
        f.store_header()
        self.assertEqual('10.0469', f.header['Temp1'])
        self.assertEqual('10.1094', f.header['Temp2'])
        self.assertEqual('12.2058', f.header['BatteryVoltage'])

    def test_store_header_value_has_delimiter(self):
        f = ApRESFile('non-existent-file')
        f.header_lines = ['Dummy=value=10']
        f.store_header()
        self.assertEqual('value=10', f.header['Dummy'])

    def test_store_header_no_value(self):
        f = ApRESFile('non-existent-file')
        f.header_lines = ['Dummy=']
        f.store_header()
        self.assertEqual('', f.header['Dummy'])

    def test_store_header_no_key(self):
        f = ApRESFile('non-existent-file')
        f.header_lines = ['=12']
        f.store_header()
        self.assertNotIn('', f.header)

    def test_store_header_false_like_key(self):
        f = ApRESFile('non-existent-file')
        f.header_lines = ['0=12','False=0']
        f.store_header()
        self.assertEqual('12', f.header['0'])
        self.assertEqual('0', f.header['False'])

    def test_store_header_invalid_delimiter(self):
        f = ApRESFile('non-existent-file')
        f.header_lines = ['Dummy;10']
        f.store_header()
        self.assertNotIn('Dummy', f.header)

    def test_store_header_strip_whitespace(self):
        f = ApRESFile('non-existent-file')
        f.header_lines = ['  Temp1  =  10.0469  ','  Temp2  =  10.1094  ']
        f.store_header()
        self.assertEqual('10.0469', f.header['Temp1'])
        self.assertEqual('10.1094', f.header['Temp2'])

    def test_determine_file_format_version_ok(self):
        f = ApRESFile('non-existent-file')
        f.header_lines = ['NSubBursts=100','N_ADC_SAMPLES=40001']
        f.determine_file_format_version()
        self.assertEqual('=', f.DEFAULTS['header_line_delim'])
        self.assertEqual(['NSubBursts', 'N_ADC_SAMPLES'], f.DEFAULTS['data_dim_keys'])

        f.header_lines = ['SubBursts in burst: 100', 'Samples: 40001']
        f.determine_file_format_version()
        self.assertEqual(':', f.DEFAULTS['header_line_delim'])
        self.assertEqual(['SubBursts in burst', 'Samples'], f.DEFAULTS['data_dim_keys'])

    def test_determine_file_format_version_turned_off(self):
        f = ApRESFile('non-existent-file')
        f.reset_init_defaults()

        # f.DEFAULTS['autodetect_file_format_version'] = False
        f.header_lines = ['SubBursts in burst: 100', 'Samples: 40001']
        # f.determine_file_format_version()
        #self.assertEqual(':', f.DEFAULTS['header_line_delim'])
        #self.assertEqual(['SubBursts in burst', 'Samples'], f.DEFAULTS['data_dim_keys'])

    def test_define_data_shape_ok(self):
        f = ApRESFile('non-existent-file')
        f.header_lines = ['NSubBursts=100','N_ADC_SAMPLES=40001']
        f.store_header()
        f.define_data_shape()
        self.assertEqual((100,40001), f.data_shape)

    def test_define_data_shape_non_integer_value(self):
        f = ApRESFile('non-existent-file')
        f.header_lines = ['NSubBursts=10.37','N_ADC_SAMPLES=40001']
        f.store_header()

        with self.assertRaises(ValueError):
            f.define_data_shape()

    def test_define_data_shape_no_value(self):
        f = ApRESFile('non-existent-file')
        f.header_lines = ['NSubBursts=','N_ADC_SAMPLES=40001']
        f.store_header()

        with self.assertRaises(ValueError):
            f.define_data_shape()

    def test_define_data_shape_invalid_delimiter(self):
        f = ApRESFile('non-existent-file')
        f.header_lines = ['NSubBursts;100','N_ADC_SAMPLES=40001']
        f.store_header()

        with self.assertRaises(KeyError):
            f.define_data_shape()

    def test_define_data_shape_required_key_missing(self):
        f = ApRESFile('non-existent-file')
        f.header_lines = ['NSubBursts_is_missing=100','N_ADC_SAMPLES=40001']
        f.store_header()

        with self.assertRaises(KeyError):
            f.define_data_shape()

    def test_read_header_ok(self):
        in_file = self.base + '/short-test-data.dat'

        with ApRESFile(in_file) as f:
            f.read_header()

    def test_read_header_invalid_file(self):
        in_file = self.base + '/non-existent-file'

        with self.assertRaises(FileNotFoundError):
            with ApRESFile(in_file) as f:
                f.read_header()

    def test_read_header_configures_object(self):
        in_file = self.base + '/short-test-data.dat'

        f = ApRESFile(in_file)
        f.open(in_file)
        f.read_header()
        self.assertEqual(804, f.data_start)
        self.assertEqual((1, 500), f.data_shape)
        self.assertEqual('10.0469', f.header['Temp1'])
        self.assertEqual('10.1094', f.header['Temp2'])
        self.assertEqual('12.2058', f.header['BatteryVoltage'])
        f.close()

    def test_read_data_ok(self):
        in_file = self.base + '/short-test-data.dat'

        with ApRESFile(in_file) as f:
            f.read_data()

    def test_read_data_invalid_file(self):
        in_file = self.base + '/non-existent-file'

        with self.assertRaises(FileNotFoundError):
            with ApRESFile(in_file) as f:
                f.read_data()

    def test_read_data_reads_header_first_if_not_already_done(self):
        in_file = self.base + '/short-test-data.dat'

        f = ApRESFile(in_file)
        f.open(in_file)
        self.assertEqual(-1, f.data_start)
        self.assertEqual(0, len(f.header))
        f.read_data()
        self.assertNotEqual(-1, f.data_start)
        self.assertNotEqual(0, len(f.header))
        f.close()

    def test_read_data_does_not_read_header_if_already_done(self):
        in_file = self.base + '/short-test-data.dat'

        f = ApRESFile(in_file)
        f.open(in_file)

        # Setting an arbitrary file offset position for the start of the data
        # section, will mess up reading the data.  The data cannot be reshaped,
        # because data_shape is an empty tuple
        f.data_start = 7

        with self.assertRaises(ValueError):
            f.read_data()

        self.assertEqual(0, len(f.data_shape))
        self.assertEqual(0, len(f.header))
        f.close()

    def test_read_data_shapes_the_data_according_to_header(self):
        in_file = self.base + '/short-test-data.dat'

        f = ApRESFile(in_file)
        f.open(in_file)
        f.read_data()
        self.assertEqual(f.data_shape, f.data.shape)
        self.assertEqual(f.data_shape[0] * f.data_shape[1], f.data.size)
        f.close()

    def test_read_data_reads_expected_values(self):
        in_file = self.base + '/short-test-data.dat'

        f = ApRESFile(in_file)
        f.open(in_file)
        f.read_data()
        self.assertEqual(33774, f.data[0, 0])
        f.close()

    def test_format_header_line_ok(self):
        f = ApRESFile('non-existent-file')

        # Ensure this is the original default, as it may have been changed by
        # previous tests
        f.DEFAULTS['header_line_delim'] = '='

        s = f.format_header_line('NSubBursts', '1')
        self.assertEqual('NSubBursts=1', s)

    def test_format_header_line_modified_delimiter(self):
        f = ApRESFile('non-existent-file')

        with patch.dict(f.DEFAULTS, {'header_line_delim': ':'}):
            s = f.format_header_line('NSubBursts', '1')
            self.assertEqual('NSubBursts:1', s)

    def test_write_header_ok(self):
        in_file = self.base + '/short-test-data.dat'
 
        fin = ApRESFile(in_file)
        fin.open(in_file)

        # We mock the call to write() to avoid writing an output file
        fout = Mock(write=Mock())

        fin.write_header(fout)
        fout.write.assert_any_call('NSubBursts=1\r\n')
        fin.close()

    def test_write_header_reads_header_first_if_not_already_done(self):
        in_file = self.base + '/short-test-data.dat'
 
        fin = ApRESFile(in_file)
        fin.open(in_file)

        fout = Mock(write=Mock())

        self.assertEqual(-1, fin.data_start)
        self.assertEqual(0, len(fin.header))
        fin.write_header(fout)
        self.assertNotEqual(-1, fin.data_start)
        self.assertNotEqual(0, len(fin.header))
        fin.close()

    def test_write_header_modified_eol(self):
        in_file = self.base + '/short-test-data.dat'

        fin = ApRESFile(in_file)
        fin.open(in_file)

        fout = Mock(write=Mock())

        with patch.dict(fin.DEFAULTS, {'header_line_eol': '\n'}):
            fin.write_header(fout)
            fout.write.assert_any_call('NSubBursts=1\n')

        fin.close()

    def test_write_header_rewrite_dimensions(self):
        in_file = self.base + '/short-test-data.dat'

        fin = ApRESFile(in_file)
        fin.open(in_file)
 
        fout = Mock(write=Mock())

        fin.write_header(fout, samples=range(10))
        fout.write.assert_any_call('N_ADC_SAMPLES=10\r\n')

        fin.close()

    def test_write_header_rewrite_dimensions_invalid_kwarg_type(self):
        in_file = self.base + '/short-test-data.dat'

        fin = ApRESFile(in_file)
        fin.open(in_file)
 
        fout = Mock(write=Mock())

        with self.assertRaises(TypeError):
            # Keyword argument `samples` must be a range object
            fin.write_header(fout, samples=10)

        fin.close()

    def test_write_data_ok(self):
        in_file = self.base + '/short-test-data.dat'
 
        fin = ApRESFile(in_file)
        fin.open(in_file)

        fout = Mock(write=Mock())

        fin.write_data(fout)
        self.assertEqual(fin.data.shape, fin.data_shape)
        fout.write.assert_called()
        fin.close()

    def test_write_data_reads_data_first_if_not_already_done(self):
        in_file = self.base + '/short-test-data.dat'
 
        fin = ApRESFile(in_file)
        fin.open(in_file)

        fout = Mock(write=Mock())

        self.assertEqual(-1, fin.data_start)
        self.assertEqual(0, len(fin.header))
        fin.write_data(fout)
        self.assertNotEqual(-1, fin.data_start)
        self.assertNotEqual(0, len(fin.header))
        fin.close()

    def test_write_data_uses_default_dimensions(self):
        in_file = self.base + '/short-test-data.dat'

        fin = ApRESFile(in_file)
        fin.open(in_file)
 
        fout = Mock(write=Mock())

        fin.write_data(fout)
        records = range(fin.data_shape[0])
        samples = range(fin.data_shape[1])
        data_expected = np.asarray(fin.data[records.start:records.stop:records.step, samples.start:samples.stop:samples.step], order=fin.DEFAULTS['data_dim_order'])
        data_actual = fout.write.call_args[0][0]
        self.assertTrue(np.array_equal(data_actual, data_expected))

        fin.close()

    def test_write_data_rewrite_dimensions(self):
        in_file = self.base + '/short-test-data.dat'
        samples = range(10)

        fin = ApRESFile(in_file)
        fin.open(in_file)
 
        fout = Mock(write=Mock())

        fin.write_data(fout, samples=samples)
        records = range(fin.data_shape[0])
        data_expected = np.asarray(fin.data[records.start:records.stop:records.step, samples.start:samples.stop:samples.step], order=fin.DEFAULTS['data_dim_order'])
        data_actual = fout.write.call_args[0][0]
        self.assertTrue(np.array_equal(data_actual, data_expected))

        fin.close()

    def test_override_path_in_open(self):
        non_existent_file = self.base + '/non-existent-file'
        existent_file = self.base + '/short-test-data.dat'

        f = ApRESFile(non_existent_file)

        with self.assertRaises(FileNotFoundError):
            f.open()
            f.read_header()
            f.close()

        # Override the path given to the constructor with a valid path
        f.open(existent_file)
        f.read_header()
        f.close()

    def test_optional_path_in_open(self):
        in_file = self.base + '/short-test-data.dat'

        f = ApRESFile(in_file)
        f.open()
        f.read_header()
        f.close()

    def test_optional_path_in_constructor(self):
        in_file = self.base + '/short-test-data.dat'

        f = ApRESFile()
        f.open(in_file)
        f.read_header()
        f.close()

