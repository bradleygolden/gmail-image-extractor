Gmail Image Extractor
=====================
Gmail Image Extractor is a web application that offers gmail users the ability to scan their mailbox for images and save/delete those images. Please see the [documentation](https://github.com/bradleygolden/gmail-image-extractor/blob/master/DOCUMENTATION.md) for a more thorough explanation of this program.

![Alt Text](https://github.com/bradleygolden/gmail-image-extractor/blob/master/preview.gif?raw=true)

Warning
-------
This is version is unstable.  Please do not use unless you are familiar with what that means.

Usage
-----
To use this program, follow the installation instructions below and login using your gmail account information. You will most likely need to lower your [gmail account security settings](https://myaccount.google.com/security). After logging in, this program will scan your gmail account for gif's, png's, and jpg's and populate them using a web interface. You will then have the option to save and delete those images from your gmail account through this interface.

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
$ cd gmail-image-extractor
$ pip install -r requirements.txt
```

Run the server
```
$ python webapp.py
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

Authors
-------
Written by [Bradley Golden](https://bradleygolden.github.io) golden.bradley@gmail.com and Pete Snyder psnyde2@uic.edu for Chris Kanich at the University of Illinois at Chicago.

Credits and Acknowledgements
----------------------------
**Special thanks to the [Cloudsweeper](https://cloudsweeper.cs.uic.edu) team:**
* Pete Snyder psnyde2@uic.edu
* Chris Kanich ckanich@uic.edu

Known Bugs
------------

##### Save functionality - Broken

*This feature is ridden with issues*

###### Current non-working solution

* I originally tried to send all of the images in packets of 10 via web sockets to the front-end where the front-end combines the packets and puts them in one large zip file. The user can then choose where to download that file. This works intermittently depending on the browser being used and the file size. This doesn't work for large data sets generally 500mb or more. This method makes the solution to the problem difficult.
    
###### Next solution
    
* Create zip file on the server side, save it, and send file to front-end. File size will have to be limited roughly 400mb
    
* For larger image sets, the solution is still unknown...

##### Other bugs

  * The server does not allow for multiple users to run the image extractor at the same time.
    * **Solution - Allow the server to run asynchronously**
  * Gmails security settings make it difficult to access gmail account without manually changing settings in google's security console (this is a tricky process)
    * **Solution - OAuth 2.0**
  * Save functionality breaks after the first save
    * **Solution - This bug hasn't been explored in detail yet**

Upcoming Features
-----------------
  - [x] Display "Are you sure?" prompt to user prior deletion
  - [ ] Save feature - mentioned above
  - [ ] Create save progress bar - looks as if the app is broken, needs a progress bar
  - [ ] Implement web logs for error tracking, etc.
  - [ ] Use HMAC to secure image information in front-end
    > Currently each image is uniquely associated with an id. This id is the memory location in hex format of the image's respective gmail attachment object. The next step for improving security is to hash the id's using HMAC to gurentee secured unqiue id's. The algorithm will look like the following:
      ```
      1. Get hex value of memory location from attachment [image id]
      2. Get image name from attachment
      3. Hash each image id using sha256
      4. Create dict with hashed image id and image id for reference
      5. Create HMAC key from hashed image id and secret
      6. Send HMAC key and image name to front end
      7. Add image name and HMAC key image thumbnail node name and id respectively
      8. Add image name to preview modal title
      ```
      
  - [ ] Create delete progress bar - images already disappear as they are erased, this is extra
  - [ ] Display total images saved/deleted at the top of the page
  - [ ] Feedback feature - allow users to send feedback

Requirements
------------
 * [pygmail](https://github.com/snyderp/pygmail)
 * [tornado](http://www.tornadoweb.org/en/stable/)
 * [google-api-python-client](https://github.com/google/google-api-python-client)
 * [httplib2](https://github.com/jcgregorio/httplib2)
 * [imaplib2](https://github.com/bcoe/imaplib2)
 * [oauth2client](https://github.com/google/oauth2client)
 * [pillow](https://github.com/python-pillow/Pillow)
