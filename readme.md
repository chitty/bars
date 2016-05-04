# Bars

## Running

The repository includes a Vagrant Virtual Machine with all the project's dependencies installed. To start it and connect to it run:

	vagrant up
	vagrant ssh

Once in the virtual machine terminal navigate to `vagrant/bars` and create the database by running `python database_setup.py`. Run the actual app `python bars.py`