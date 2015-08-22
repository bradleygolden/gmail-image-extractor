Gmail Image Extractor
=====================
Gmail Image Extractor is a web application that offers gmail users the ability to scan their mailbox for images and save/delete those images. Please see the [documentation](https://github.com/bradleygolden/gmail-image-extractor/blob/master/DOCUMENTATION.md) for a more thorough explanation of this program.

![Alt Text](https://github.com/bradleygolden/gmail-image-extractor/blob/master/preview.gif?raw=true)

Warning
-------
This is version is unstable.  Please do not use unless you are familiar with what that means.

Usage
-----
To use this program, follow the installation instructions below and login using your gmail account information. After logging in, this program will scan your gmail account for gif's, png's, and jpg's and populate them using a web interface. You will then have the option to save and delete those images from your gmail account through this interface.

Installation and Configuration
------------------------------
**Requires python 2.X and pip**

Install Virtualenv
```
$ pip install virtualenv
```

Make a project directory using Virtualenv
```
$ virtualenv gmail-image-extractor
```

Clone this repo in the project directory
```
$ cd gmail-image-extractor
$ git clone https://github.com/bradleygolden/gmail-image-extractor.git
```

Enter virtualenv
```
$ source bin/activate
```

Install dependencies
```
$(gmail-image-extractor) cd gmail-image-extractor
$(gmail-image-extractor) pip install -r requirements.txt
```

Run the server
```
$(gmail-image-extractor) python webapp.py
```

Checkout the app on your browser at
```
localhost:8888
```

Contributing
------------
1. Fork it ( https://github.com/[my-github-username]/gmail-image-extractor/fork )
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create a new Pull Request

[Pull request documentation](http://help.github.com/pull-requests/)

[Fork documentation](http://help.github.com/forking/)

About the Project
-----------------
Gmail Image Extractor is an open source web application that is focused on providing users an alternative to efficiently managing their gmail accounts. Currently gmail accounts offer over 100 gigabytes of storage. This allows most users the freedom to archive emails without the concern of deleting them permanently. These archived emails may contain various attachments including images and ome of those images may be private, contain sensitive information, or have personal value. This application gives users the ability to save and remove those images if they so choose.

License
-------
Please see the file called [License](https://github.com/bradleygolden/gmail-image-extractor/blob/master/LICENSE.txt)

Contributors
------------
Written by [Bradley Golden](https://bradleygolden.github.io) golden.bradley@gmail.com and Pete Snyder psnyde2@uic.edu for Chris Kanich at the University of Illinois at Chicago.

Credits and Acknowledgements
----------------------------
**Special thanks to the [Cloudsweeper](https://cloudsweeper.cs.uic.edu) team:**
* Pete Snyder psnyde2@uic.edu
* Chris Kanich ckanich@uic.edu

Requirements
------------
Please see [requirements.txt](https://github.com/bradleygolden/gmail-image-extractor/blob/master/requirements.txt)
