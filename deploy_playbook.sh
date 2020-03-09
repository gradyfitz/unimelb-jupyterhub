#!/bin/bash

# Run openrc.sh to set environment variables,
# then run playbook given as second argument.
source ./openrc.sh; ansible-playbook -i inventory/inventory.ini --private-key "$1" $2 $3
