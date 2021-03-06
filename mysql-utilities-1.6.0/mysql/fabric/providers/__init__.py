#
# Copyright (c) 2014 Oracle and/or its affiliates. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
"""This package contains code and wrapper classes to access the different
types of cloud providers. For example, OpenStack, Amazon, etc.

To add support to a different cloud provider, we need to drop a module
within the providers package and define a *configure_provider* function
within the module. This function will be responsible for checking whether
the necessary packages to access the provider are installed will return
information on the provider:

- Unique Provider's Identification which is a string.
- Reference to a concrete calls built upon the AbstractMachineManager.
- Unique Provider's index which is an integer.

For example, the openstack.py module has the following *configure_provider*
function::

  def configure_provider():
    import novaclient.client
    return ("OPENSTACK", MachineManager, 2)

Each supported provider must return a reference to a concrete class that
inherits from the AbstractMachineManager class defined in this module. This
class is an entry point to a set of methods to access a provider.
"""
import pkgutil
import inspect
import logging

from mysql.fabric.errors import ProviderError

PROVIDERS_TYPE = {}
PROVIDERS_IDX = {}

_LOGGER = logging.getLogger(__name__)

def find_providers():
    """Find which are the available commands.
    """
    for imp, name, ispkg in pkgutil.walk_packages(__path__, __name__ + "."):
        mod = imp.find_module(name).load_module(name)
        _LOGGER.debug("%s %s has got __name__ %s",
            "Package" if ispkg else "Module", name, mod.__name__
        )
        for (mem_name, mem_value) in inspect.getmembers(mod):
            if mem_name == "configure_provider" and inspect.isfunction(mem_value):
                try:
                    provider, manager, idx = mem_value()
                    if provider in PROVIDERS_TYPE:
                        raise ProviderError(
                            "Provider type (%s) is already defined (%s)." %
                            (provider, PROVIDERS_TYPE[provider])
                        )
                    if idx in PROVIDERS_IDX:
                        raise ProviderError(
                            "Provider index (%s) is already defined (%s)." %
                            (idx, PROVIDERS_IDX[idx])
                        )
                    PROVIDERS_TYPE[provider] = {'manager' : manager, 'idx' : idx}
                    PROVIDERS_IDX[idx] = {'provider' : provider}
                except ImportError:
                    pass
    _LOGGER.debug("Providers %s.", PROVIDERS_TYPE)

def get_provider_idx(provider_type):
    """Return the index associated to the type.
    """
    try:
        return PROVIDERS_TYPE[provider_type]['idx']
    except KeyError as error:
        raise ProviderError(
            "Provider type (%s) is not supported yet." % (provider_type, )
        )

def get_provider_type(provider_idx):
    """Return the type associated to the index.
    """
    try:
        return PROVIDERS_IDX[provider_idx]['provider']
    except KeyError as error:
        raise ProviderError(
            "Provider index (%s) does not exist." % (provider_idx, )
        )

def get_provider_manager(provider_type):
    """Return a reference to a wrapper class that provides the appropriate
    methods to access the cloud provider.

    :param provider_type: Provider type.
    """
    try:
        return PROVIDERS_TYPE[provider_type]['manager']
    except KeyError as error:
        raise ProviderError(
            "Provider type (%s) is not supported yet." % (provider_type, )
        )


class AbstractMachineManager(object):
    """Wrapper class that is used to manage machines in the cloud.

    :param provider: Reference to provider object.
    :param version: Version.
    :rtype version: string
    """
    def __init__(self, provider, version=None):
        self.__provider = provider
        self.__version = version

    @property
    def provider(self):
        """Return a reference to the provider.
        """
        return self.__provider

    @property
    def version(self):
        """Return version.
        """
        return self.__version

    def create_machines(self, parameters, wait_spawning):
        """Create machines.

        :param parameters: Parameters to create machines.
        :param wait_spwaning: Whether one should wait until the provider
                              finishes its task or not.
        """
        raise NotImplementedError

    def search_machines(self, generic_filters, meta_filters):
        """Return machines based on the provided filters.

        :param generic_filters: Dictionary with criteria to search for.
        :param meta_filters: Dictionary with criteria to search for.
        :return: List with machines that match criteria.
        """
        raise NotImplementedError

    def destroy_machine(self, machine_uuid):
        """Destroy a machine.

        :param machine_uuid: UUID that uniquely identifies the machine.
        """
        raise NotImplementedError

    def assign_public_ip(self, machine, pool):
        """Assign public IP address to a machine.

        :param machine: Reference to a machine.
        :param pool: Pool from where the address will be withdrawn.
        """
        raise NotImplementedError

    def remove_public_ip(self, machine):
        """Remove public addresses assigned to a machine.

        :param machine: Reference to a machine.
        """
        raise NotImplementedError

    def create_snapshot(self, machine_uuid, wait_spawning):
        """Create a snapshot from a machine.

        :param machine_uuid: Machine's UUID.
        :param wait_spwaning: Whether one should wait until the provider
                              finishes its task or not.
        """
        raise NotImplementedError

    def destroy_snapshot(self, machine_uuid):
        """Destroy snapshots associated to a machine.

        :param machine_uuid: Machine's UUID.
        """
        raise NotImplementedError
