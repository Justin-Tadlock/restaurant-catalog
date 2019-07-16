# Restaurant Catalog

A project used to show a list of restaurants and their menu items while implementing CRUD functionality on each item type.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

To run the VM, you must have the following:
* [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
* [Vagrant](https://www.vagrantup.com/)
** For more information on the base setup that this project is running off of, visit the [Udacity VM Setup](https://github.com/udacity/fullstack-nanodegree-vm)


### Running the VM

To run the VM you must do the following:
1. Obtain a copy of the repository from: [Repo Zip](https://github.com/udacity/fullstack-nanodegree-vm/archive/master.zip)
2. Unzip the master.zip file into the Vagrant's repository directory under "{repoLocation}/vagrant/catalog"
3. Open a command prompt/PowerShell/terminal window inside the vagrant directory
4. Run the following commands
```
vagrant init
vagrant up
vagrant ssh
```

### Setting up the data

Once you establish a connection to your VM, run the following commands:
```
cd /vagrant/catalog
python3 ./database_setup.py
python3 ./lotsofmenus.py
```

### Running the web server that hosts the application

Run the following command to boot up the web server so that you can navigate the application:
```
python3 ./run_catalog_server.py
```

### Browsing the application

On your host machine, open up your browser and navigate to:
```
localhost:5000
```

Now you will be able to browse around the application project and utilize all the CRUD functionality.

## Built With

* [Python](https://www.python.org/downloads/) - Python is a programming language that lets you work quickly and integrate systems more effectively
* [Flask](https://palletsprojects.com/p/flask/) - A lightweight WSGI web application framework.
* [SQLAlchemy](https://www.sqlalchemy.org/) - The Python SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL.
* HTML
* CSS

## Authors

* **[Justin-Tadlock](https://github.com/Justin-Tadlock)** - *Initial work*

## Acknowledgments

* [Udacity VM Setup](https://github.com/udacity/fullstack-nanodegree-vm) - for the initial setup of the Vagrant VM.
* [lotsofmenus.py](https://github.com/udacity/Full-Stack-Foundations/blob/master/Lesson_1/lotsofmenus.py) - for adding menu item data to the restaurantmenu.db database
