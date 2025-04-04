"""
Test cases for the GTFS realtime reader module
"""
import unittest
import os
import json
from pathlib import Path
from nmbs_data.data.gtfs_realtime_reader import create_sample_files, extract_vehicle_positions


class TestGtfsRealtimeReader(unittest.TestCase):
    
    def test_create_sample_files(self):
        """Test that sample files can be created"""
        # Use a temporary directory for testing
        test_dir = Path(__file__).parent / 'test_output'
        test_dir.mkdir(exist_ok=True)
        
        try:
            # Create test directories
            with_changes_dir = test_dir / 'with_changes'
            without_changes_dir = test_dir / 'without_changes'
            with_changes_dir.mkdir(exist_ok=True)
            without_changes_dir.mkdir(exist_ok=True)
            
            # Create sample files
            files_created = create_sample_files(
                with_platform_changes_dir=str(with_changes_dir),
                without_platform_changes_dir=str(without_changes_dir)
            )
            
            # Check that files were created
            self.assertGreater(files_created, 0)
            
            # Verify at least one file exists in each directory
            self.assertTrue(any(with_changes_dir.glob('*.json')))
            self.assertTrue(any(without_changes_dir.glob('*.json')))
            
            # Check that a sample file has expected structure
            sample_file = next(with_changes_dir.glob('*.json'))
            with open(sample_file, 'r') as f:
                data = json.load(f)
                self.assertIn('header', data)
                self.assertIn('entity', data)
                
        finally:
            # Cleanup test files
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)
    
    def test_extract_vehicle_positions(self):
        """Test extracting vehicle positions from sample data"""
        # Create a minimal sample data structure
        sample_data = {
            'test_source': {
                'header': {
                    'timestamp': 1234567890
                },
                'entity': [
                    {
                        'id': 'vehicle1',
                        'vehicle': {
                            'position': {
                                'latitude': 50.8,
                                'longitude': 4.3,
                                'bearing': 90
                            },
                            'trip': {
                                'trip_id': 'trip1',
                                'route_id': 'route1'
                            },
                            'vehicle': {
                                'id': 'train1'
                            }
                        }
                    }
                ]
            }
        }
        
        # Extract positions
        positions = extract_vehicle_positions(sample_data)
        
        # Verify extraction
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['latitude'], 50.8)
        self.assertEqual(positions[0]['longitude'], 4.3)
        self.assertEqual(positions[0]['trip_id'], 'trip1')


if __name__ == '__main__':
    unittest.main()