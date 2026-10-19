from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import planner


class PlannerTests(unittest.TestCase):
    def test_ipv4_range(self):
        result = planner.describe('192.0.2.0/24')
        self.assertEqual(result['host_range'], {'first':'192.0.2.1','last':'192.0.2.254','count':254})
        self.assertEqual(result['broadcast_address'], '192.0.2.255')

    def test_ipv4_point_to_point_and_single_host(self):
        self.assertEqual(planner.describe('192.0.2.0/31')['host_range']['count'], 2)
        self.assertEqual(planner.describe('192.0.2.5/32')['host_range'], {'first':'192.0.2.5','last':'192.0.2.5','count':1})

    def test_ipv6_range_has_no_broadcast(self):
        result = planner.describe('2001:db8::/126')
        self.assertIsNone(result['broadcast_address'])
        self.assertEqual(result['host_range'], {'first':'2001:db8::1','last':'2001:db8::3','count':3})
        self.assertEqual(planner.describe('2001:db8::/127')['host_range']['count'], 2)
        self.assertEqual(planner.describe('2001:db8::1/128')['host_range']['count'], 1)

    def test_split_and_expansion_limit(self):
        result = planner.split_network('192.0.2.0/24', 26)
        self.assertEqual(result['count'], 4)
        self.assertEqual(result['subnets'][-1]['cidr'], '192.0.2.192/26')
        with self.assertRaises(ValueError):
            planner.split_network('10.0.0.0/8', 32)

    def test_host_bits_and_invalid_prefix_rejected(self):
        with self.assertRaises(ValueError): planner.describe('192.0.2.5/24')
        with self.assertRaises(ValueError): planner.split_network('192.0.2.0/24', 20)

    def test_mixed_families_duplicates_and_adjacent_subnets(self):
        self.assertFalse(planner.overlaps(['192.0.2.0/25','192.0.2.128/25','2001:db8::/32'])['has_overlaps'])
        self.assertTrue(planner.overlaps(['10.0.0.0/8','10.1.0.0/16'])['has_overlaps'])
        self.assertTrue(planner.overlaps(['10.0.0.0/8','10.0.0.0/8'])['has_overlaps'])

    def test_output_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'report.json'
            planner.write_new(path, {'keep': True})
            with self.assertRaises(FileExistsError):planner.write_new(path, {})
            self.assertIn('true', path.read_text())

    def test_cli_overlap_exit_code(self):
        result = subprocess.run([sys.executable, planner.__file__, 'overlap', '10.0.0.0/8','10.1.0.0/16'], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'"has_overlaps": true', result.stdout)


if __name__ == '__main__':
    unittest.main()
