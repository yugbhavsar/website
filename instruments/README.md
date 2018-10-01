# instruments

This module aims at implementing two models

- instruments
- methods

as well as some models required for handling them. A method can be connected
to one or more instruments as shown below: 

    ------------------------------------------------
	- Method: example_method                       -
	------------------------------------------------
	- Instruments:                                 -
	-   Instrument 1                               -
	-   Instrument 2                               -
	-   ...                                        -
	------------------------------------------------
	
User can only select methods for their projects, however it is possible to
have instruments which are onbt a member of any method. These instruments are
listed on the website, but cannot be booked directly. One example is [the fast
oscilloscope](https://www.rubion.rub.de/instruments/oszilloscope-tektronix-dpo5204b/)
users can use on request. 

In general, the connection between a user (or a workgroup) and an instrument is
the following:

    + Workgroup
	|
	|--+ Members
	|  |-- User 1
	|  |-- User 2
	|  |-- ...
	|
	|--+ Projects
	   |--+ Project 1
	      |--+ Method 1
		  |  |-- Instrument 1
		  |  |-- Instrument 2
		  |
	      |--+ Method 2
	         |-- Instrument 1
	         |-- Instrument 3

In the above case, *User 1*  and *User 2* are connected to *Instrument 1*,
*Instrument 2* and *Instrument 3*, which means that the safety measures for
the three instruments apply to them.

## Model ``instruments``

For a detailed description of the model ``instruments`` see the source
file (``models.py``). This models defines the safety measures required to use
this instruments (can be set by the admin panel). The general idea is, if a
new user is added to a group, the information regarding the safety measured
are asked directly for all safety measures a user is connected to.

The following safety measures are implemented:

  - ``requires_labcoat``
  - ``requires_overshoes``
  - ``requires_entrance`` This is meant for users in the isotope laboratory,
they can provide their favorite entrance 
  - ``requires_dosemeter``
  - ``requires_isotope_information`` If users deal with unstable isotopes,
  they sould provide the isotope as well as the estimated amount of the
  isotope used

