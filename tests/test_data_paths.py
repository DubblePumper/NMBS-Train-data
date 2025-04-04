"""
Test cases for the data paths module
"""
import unittest
import os
from nmbs_data.data.data_paths import get_project_paths, ensure_directories, get_realtime_dirs


class TestDataPaths(unittest.TestCase):
    
    def test_paths_exist(self):
        """Test that paths returned by get_project_paths exist or can be created"""
        paths = get_project_paths()
        self.assertIsInstance(paths, dict)
        self.assertIn('project_root', paths)
        self.assertIn('data_dir', paths)
        
    def test_ensure_directories(self):
        """Test that ensure_directories creates the necessary directories"""
        paths = ensure_directories()
        # Check that all directories now exist
        for dir_name in ['data_dir', 'planning_dir', 'realtime_dir', 'maps_dir']:
            self.assertTrue(os.path.exists(paths[dir_name]))
            
    def test_realtime_dirs(self):
        """Test that real-time directories are correctly identified"""
        realtime_dirs = get_realtime_dirs()
        self.assertEqual(len(realtime_dirs), 2)
        self.assertTrue(any('met_info_over_spoorveranderingen' in d for d in realtime_dirs))
        self.assertTrue(any('zonder_info_over_spoorveranderingen' in d for d in realtime_dirs))


if __name__ == '__main__':
    unittest.main()