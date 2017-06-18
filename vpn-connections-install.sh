#!/bin/bash
#
# Install OpenVPN profiles in NetworkManager
#

error() {
	echo $@ >&2
	exit 255
}

if [ "$(whoami)" != "root" ]; then
	error "This script needs to be run as root. Try again with 'sudo $0'"
fi

pkgerror="Failed to install the required packages, aborting."

##
# Debian-based distributions
if command -v apt-get 2>&1 >/dev/null; then
	installpkg=()

	if ! dpkg -l python2.7 | grep -q '^ii'; then
		installpkg+=python2.7
	fi
	
	if ! dpkg -l network-manager-openvpn | grep -q '^ii'; then
		installpkg+=network-manager-openvpn
	fi
	
	if [ ! -z "$installpkg" ]; then
		apt-get install $installpkg || error $pkgerror
	fi

##
# RHEL-based distributions
elif command -v rpm 2>&1 >/dev/null; then
	installpkg=()
	
	if ! rpm -q python 2>&1 >/dev/null; then
		installpkg+=python
	fi

	if ! rpm -q NetworkManager-openvpn 2>&1 >/dev/null; then
		installpkg+=NetworkManager-openvpn
	fi
	
	if [ ! -z "$installpkg" ]; then
		if which dnf; then
			dnf install $installpkg || error "$pkgerror" 
		else
			yum install $installpkg || error "$pkgerror"
		fi
	fi

##
# ArchLinux
elif command -v pacman 2>&1 >/dev/null; then
	installpkg=()
	
	if ! pacman -Q python2 2>/dev/null; then
		installpkg+=python2
	fi
	
	if ! pacman -Q networkmanager-openvpn 2>/dev/null; then
		installpkg+=networkmanager-openvpn
	fi

	if [ ! -z "$installpkg" ]; then
		pacman -S $installpkg || error "$pkgerror"
	fi
fi

currentdir=`dirname $0`
vpn_connection_dir="/etc/NetworkManager/system-connections"
vpn_connection_file_mask="$vpn_connection_dir/trial-*"

rm -f $vpn_connection_file_mask
cp $currentdir/venv$vpn_connection_file_mask $vpn_connection_dir
chmod 0600 $vpn_connection_file_mask

nmcli connection reload || \
	error "Failed to reload NetworkManager connections: installation was complete, but may require a restart to be effective."

echo "Installation is complete!"
