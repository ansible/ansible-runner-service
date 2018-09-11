#!/usr/bin/env python3
import os
import sys
import unittest
import logging
from runner_service import AnsibleInventory, InventoryGroupMissing

logging.basicConfig(stream=sys.stderr)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# requirements
# runner_service needs to be installed
#


class TestInventory(unittest.TestCase):
    # setup the inventory file
    # add a group
    # remove a group that doesn't exist
    # remove a group that does
    # add a host to a group
    # add a host to a non-existent group
    # remove a non-existent host from a group
    # remove a host from a group
    # add multiple hosts to a group
    #   then remove the group
    # shutdown - delete the inventory file
    filename = os.path.expanduser('~/inventory')
    inventory = AnsibleInventory(filename)

    def test_01_inventory_created(self):
        self.assertTrue(os.path.exists(self.filename))

    def test_02_check_empty(self):
        self.assertEqual(self.inventory.groups, [])
        self.assertEqual(self.inventory.hosts, [])
        
    def test_03_group_missing(self):
        with self.assertRaises(InventoryGroupMissing):
            self.inventory.group_remove('dodgy')

    def test_04_group_add(self):
        self.inventory.group_add('newgroup')
        self.assertIn('newgroup', self.inventory.groups)
    
    def test_05_group_remove(self):
        self.inventory.group_remove('newgroup')
        self.assertNotIn('newgroup', self.inventory.groups)

    def test_06_host_add_invalid(self):
        with self.assertRaises(InventoryGroupMissing):
            self.inventory.host_add('mygroup', 'myhost')

    def test_07_group_add(self):
        self.inventory.group_add('mygroup')
        self.assertIn('mygroup', self.inventory.groups)
    
    def test_08_host_add(self):
        self.inventory.host_add('mygroup', 'myhost')
        self.assertIn('myhost', self.inventory.group_show('mygroup'))

    def test_09_host_remove(self):
        self.inventory.host_remove('mygroup', 'myhost')
        self.assertNotIn('myhost', self.inventory.group_show('mygroup'))

    def test_10_save(self):
        self.inventory.host_add('mygroup', 'host-1')
        self.inventory.host_add('mygroup', 'host-2')
        self.inventory.save()
        with open(self.filename) as i:
            data = i.readlines()

        # should only be 6 records in the file
        #['all:\n', '  children:\n', '    mygroup:\n', '
        #  hosts:\n', '        host-1:\n', '        host-2:\n']
        self.assertEqual(len(data), 6)

    def test_11_remove_nonempty(self):
        self.inventory.group_remove('mygroup')
        self.assertNotIn('mygroup', self.inventory.groups)
    

    @classmethod
    def tearDownClass(cls):
        # Remove the inventory file we were using
        os.unlink(TestInventory.filename)

def main():
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()
