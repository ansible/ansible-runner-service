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

INV_FILENAME = os.path.expanduser('~/inventory')

def delete_file(filename):
    """ Delete the file passed as parameter if it exists
    """

    if os.path.isfile(filename):
        os.remove(filename)


class TestInventory(unittest.TestCase):
    # setup the inventory file (with/without exclusive access)
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
    

    def setUp(self):
        """ Start with a clean environment in each test
        """

        delete_file(INV_FILENAME)

    def test_01_exclusive_inventory_created(self):
        """Setup the inventory file with exclusive access)
        """
        
        inventory = AnsibleInventory(INV_FILENAME, True)
      
        self.assertTrue(os.path.exists(INV_FILENAME))


        # this should raise an error ... 
        inventory2 = AnsibleInventory(INV_FILENAME, True)

    def test_01_inventory_created(self):
        """Setup the inventory file without exclusive access)
        """
        
        inventory = AnsibleInventory(INV_FILENAME)
      
        self.assertTrue(os.path.exists(INV_FILENAME))

        # This should work
        inventory2 = AnsibleInventory(INV_FILENAME)

    def test_02_check_empty(self):
        """Check inventory is empty
        """
        
        inventory = AnsibleInventory(INV_FILENAME, True)
        
        self.assertEqual(inventory.groups, [])
        self.assertEqual(inventory.hosts, [])
    
    def test_03_group_missing(self):
        """Check error raised when a group does not exist
        """

        inventory = AnsibleInventory(INV_FILENAME, True)
        with self.assertRaises(InventoryGroupMissing):
            inventory.group_remove('dodgy')

    def test_04_group_add(self):
        """Check group addition
        """
        
        inventory = AnsibleInventory(INV_FILENAME, excl=True)
        inventory.group_add('newgroup')
        self.assertIn('newgroup', inventory.groups)


    def test_05_group_remove(self):
        """Check remove a group that exists
        """

        inventory = AnsibleInventory(INV_FILENAME, excl=True)
        inventory.group_add('newgroup')
        self.assertIn('newgroup', inventory.groups)

        # two write operations not supported.. 
        # Needed another AnsibleInventary Object
        inventory = AnsibleInventory(INV_FILENAME, excl=True)  
        inventory.group_remove('newgroup')
        self.assertNotIn('newgroup', inventory.groups)

    def test_06_host_add_invalid(self):
        """add a host to a non-existent group
        """

        inventory = AnsibleInventory(INV_FILENAME, excl=True)
        with self.assertRaises(InventoryGroupMissing):
            inventory.host_add('mygroup', 'myhost')

    def test_08_host_add(self):
        """add a host to an existent group
        """        
        inventory = AnsibleInventory(INV_FILENAME, excl=True)
        inventory.group_add('mygroup')
        self.assertIn('mygroup', inventory.groups)
        
        # two write operations not supported.. 
        # Needed another AnsibleInventary Object 
        inventory = AnsibleInventory(INV_FILENAME, excl=True)       
        inventory.host_add('mygroup', 'myhost')
        self.assertIn('myhost', inventory.group_show('mygroup'))


    def test_09_host_remove(self):
        """remove a host from an existent group
        """ 
        inventory = AnsibleInventory(INV_FILENAME, excl=True)
        inventory.group_add('mygroup')
        self.assertIn('mygroup', inventory.groups)
        
        # two write operations not supported.. 
        # Needed another AnsibleInventary Object 
        inventory = AnsibleInventory(INV_FILENAME, excl=True)       
        inventory.host_add('mygroup', 'myhost')
        self.assertIn('myhost', inventory.group_show('mygroup'))        
        
        # two write operations not supported.. 
        # Needed another AnsibleInventary Object
        inventory = AnsibleInventory(INV_FILENAME, excl=True) 
        inventory.host_remove('mygroup', 'myhost')
        self.assertNotIn('myhost', inventory.group_show('mygroup'))


    def test_11_remove_nonempty(self):
        """remove a group with hosts
        """ 

        inventory = AnsibleInventory(INV_FILENAME, excl=True)
        inventory.group_add('mygroup')
        self.assertIn('mygroup', inventory.groups)
        
        # two write operations not supported.. 
        # Needed another AnsibleInventary Object 
        inventory = AnsibleInventory(INV_FILENAME, excl=True)       
        inventory.host_add('mygroup', 'myhost')
        self.assertIn('myhost', inventory.group_show('mygroup'))        

        # two write operations not supported.. 
        # Needed another AnsibleInventary Object 
        inventory = AnsibleInventory(INV_FILENAME, excl=True)         
        inventory.group_remove('mygroup')
        self.assertNotIn('mygroup', inventory.groups)

    @classmethod
    def tearDownClass(cls):
        # Remove the inventory file we were using
        os.unlink(INV_FILENAME)

def main():
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()
