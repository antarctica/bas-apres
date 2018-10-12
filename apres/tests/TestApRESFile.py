import unittest
import os

from apres.apres import ApRESFile

class TestApRESFile(unittest.TestCase):

    base = os.path.dirname(__file__)

    def test_store_header_ok(self):
        f = ApRESFile('non-existent-file')
        header_lines = ['Temp1=10.0469','Temp2=10.1094','BatteryVoltage=12.2058']
        f.store_header(header_lines)
        self.assertEqual('10.0469', f.header['Temp1'])
        self.assertEqual('10.1094', f.header['Temp2'])
        self.assertEqual('12.2058', f.header['BatteryVoltage'])

    def test_store_header_value_has_delimiter(self):
        f = ApRESFile('non-existent-file')
        header_lines = ['Dummy=value=10']
        f.store_header(header_lines)
        self.assertEqual('value=10', f.header['Dummy'])

    def test_store_header_no_value(self):
        f = ApRESFile('non-existent-file')
        header_lines = ['Dummy=']
        f.store_header(header_lines)
        self.assertEqual('', f.header['Dummy'])

    def test_store_header_no_key(self):
        f = ApRESFile('non-existent-file')
        header_lines = ['=12']
        f.store_header(header_lines)
        self.assertNotIn('', f.header)

    def test_store_header_false_like_key(self):
        f = ApRESFile('non-existent-file')
        header_lines = ['0=12','False=0']
        f.store_header(header_lines)
        self.assertEqual('12', f.header['0'])
        self.assertEqual('0', f.header['False'])

    def test_store_header_invalid_delimiter(self):
        f = ApRESFile('non-existent-file')
        header_lines = ['Dummy:10']
        f.store_header(header_lines)
        self.assertNotIn('Dummy', f.header)

    def test_define_data_shape_ok(self):
        f = ApRESFile('non-existent-file')
        header_lines = ['NSubBursts=100','N_ADC_SAMPLES=40001']
        f.store_header(header_lines)
        f.define_data_shape()
        self.assertEqual((100,40001), f.data_shape)

    def test_define_data_shape_non_integer_value(self):
        f = ApRESFile('non-existent-file')
        header_lines = ['NSubBursts=10.37','N_ADC_SAMPLES=40001']
        f.store_header(header_lines)

        with self.assertRaises(ValueError):
            f.define_data_shape()

    def test_define_data_shape_no_value(self):
        f = ApRESFile('non-existent-file')
        header_lines = ['NSubBursts=','N_ADC_SAMPLES=40001']
        f.store_header(header_lines)

        with self.assertRaises(ValueError):
            f.define_data_shape()

    def test_define_data_shape_invalid_delimiter(self):
        f = ApRESFile('non-existent-file')
        header_lines = ['NSubBursts:100','N_ADC_SAMPLES=40001']
        f.store_header(header_lines)

        with self.assertRaises(KeyError):
            f.define_data_shape()

    def test_define_data_shape_required_key_missing(self):
        f = ApRESFile('non-existent-file')
        header_lines = ['NSubBursts_is_missing=100','N_ADC_SAMPLES=40001']
        f.store_header(header_lines)

        with self.assertRaises(KeyError):
            f.define_data_shape()

    def test_read_header_ok(self):
        in_file = self.base + '/short-test-data.dat'

        with ApRESFile(in_file) as f:
            f.read_header()

