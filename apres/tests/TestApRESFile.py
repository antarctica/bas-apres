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

