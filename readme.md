# Bars

The bars app is a responsive website that display information about drinks available in different bars.

Users can log in using Google+ or facebook in order to create new bars and drinks. Later they can modify or delete them if they want.

## Running

The repository includes a Vagrant Virtual Machine with all the project's dependencies installed. To start it and connect to it run:

	vagrant up
	vagrant ssh

Once in the virtual machine terminal navigate to `/vagrant/bars` and run the app:
	
	python bars.py

Now the app should be up and running in `http://localhost:5000/`

**To load some initial data run** `python some_drinks.py`.

## JSON

The project implements a JSON endpoint that serves the same information as displayed in the HTML endpoints.

- To get all the existing bars: `/bar/JSON`
- To see the complete drink menu of a bar: `/bar/<int:bar_id>/menu/JSON`
- To see a drinks' detail: `/bar/<int:bar_id>/menu/<int:drink_id>/JSON`
- To see the 10 newest drinks: `/newest_drinks/JSON`

<details>
  <summary>Details</summary>
	
  ## TO DO
	  
  Details go here...
</details>
