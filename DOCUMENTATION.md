Intro
-----

Email clients are offering larger and larger storage space for emails as time progresses. Currently, Gmail offers 100 gigabytes of space for their users and this figure is growing each year. As Gmail's storage limit increases, many consumers continue to archive emails for various reasons, resulting in thousands of old and forgotten emails. Among these emails, many may contain images that have sentimental value, contain personal information, and more. The existence of these images also provides opportunities for hackers to exploit users unknowingly. Therefore, it's important to provide Gmail users with tools to effectively manage their email account for the purpose of increasing security and the awareness. Gmail Image Extractor is the current solution for providing users the ability to secure photo attachments easily. Gmail Image Extractor requires no extra login information other than their pre-existing email account information, and it is completely web based for easy use.

Related Work
------------

Other related projects can be found below. This program is currently stand alone, but it will be merged with Cloudsweeper to further increase the scope of email management tools available to Gmail users.

- Cloudsweeper, a web application that provides Gmail users with tools to secure their Gmail accounts. More information can be found here: https://cloudsweeper.cs.uic.edu/ 
- AttachmentExtractor for Thunderbird extracts attachments from emails and allows users to delete, detach, or mark the messages as read. More information can be found here: https://addons.mozilla.org/en-US/thunderbird/addon/attachmentextractor/
- Mail Attachment Downloader for Windows has many options, including the ability to download and delete attachments from emails. More information can be found here: http://gearmage.com/maildownloader.html
- Save Emails and Attachments for Google Sheets has the option to download images and varying attachments from Gmail to Google Drive. More information can be found here: https://chrome.google.com/webstore/detail/save-emails-and-attachmen/nflmnfjphdbeagnilbihcodcophecebc?hl=en

Gmail Image Extractor in particular offers a variety of benefits versus other solutions. Some of these include a simple to use web application that is both browser and operating system independent, the ability to preview images prior to deletion, and the ability to save/delete images from a custom selection. More features may be released in the future.

Methodology
-----------

The original design of Gmail Image Extractor was intended to be used as a desktop application. This desktop version had a few basic and useful features for Gmail users. Images were first downloaded to the user?s desktop. Users then had the option to delete the images they didn?t want, and to sync the folder in which the images were contained with their Gmail account. For a desktop application this method was very successfully, however if the program was to be easily accessible to a larger audience, a web solution is the next best alternative.

##### Required Knowledge

The list below consists of some of the prerequisite knowledge required for building the Gmail Image Extractor web interface:

* Python
* Pygmail module
* Basic use of Tornado Web Server
* Web sockets
* Basic HTML/JavaScript/CSS/JQuery
* Bootstrap
* Basic use of callbacks
* Program flow between front-end and back-end programs
* Basic use of GIT or other version control software

##### Initial Design Challenges

Due to the nature of Gmail Image Extractor being designed for the desktop, much of the code in the program was un-useable for a web interface. Because browsers do not allow direct access to the client's operating system, another method for displaying, saving, and deleting messages had to be implemented. The later design of the program was executed in the order of: first creating an initial web interface, then displaying images to the user, then allowing users to delete selected images, and lastly giving users the opportunity to save images.

##### Building the Frontend

The frontend for the application has been built using HTML, CSS, JavaScript, JQuery and Bootstrap.

The design of the frontend is and will be an ongoing design process as more features are released and debugged.

##### Displaying Images to the User

The next step in the process of developing the web application involved displaying images in the browser from the user's email accont. This was done by converting all images to strings using base64 in the backend and sending those images to the frontend for display. The process was challenging because there were initial conflicts with duplicate images overwriting each other. Out of this conflict, a unique id for images was created by hashing the image body using the sha1 algorithm in Python.  This method proved successful at first, but later had to be re-visited during the delete process.

Another part of this process that is worth mentioning is the conversion of images before they are converted to strings. To increase display speed in the front end and reduce machine performance requirements, both image size and image quality are reduced using Python's PIL (now known as Pillow) library.

##### Deleting Images 

The delete images option was the first interactive feature implemented in the web interface of the Gmail Image Extractor. 

To begin the actual deletion of images from the user?s Gmail account, a method for which to select and bundle images into a list had to be created in the front end. This was done using arrays which are sent to the backend for reference.

In the backend, each array is organized by a unique message id and image id. After organizing the selected images, each corresponding message is pulled from the user's Gmail account. It is important to note that each message should only be extracted ONCE. Any further extractions result in a different message object that contains a different unique message id and memory location (the memory location is important for later). 

**First deletion method:**

Upon extracting each message, the attachments are also extracted from the message. Each attachment object contains an attachment body that is then matched with the corresponding image id (hash of the image body) to verify if in fact the user actually selected that image for deletion. If the user selected that image, it removed, otherwise the image remains in the mailbox. Due to the fact that multiple duplicate images can exists in a single user's inbox, the message id and image id proved to be non unique. Thus this method failed to produce the desired result.

**Current deletion method:**

The method for extracting images is the same as the first, however rather than using the hash of the image body for constructing an image id, a new strategy had to be used. Because each attachment is a unique object referenced to a unique memory address, the hex value of the memory address proves to always be unique for every attachment. Therefore, it was decided that the hex value of the attachment object's memory location could be used rather than the hash of the image body.

In the end, this method eliminated any id conflicts and is currently being used.

##### Saving Images:

After completing the delete tool, providing the option for users to save images seemed like a necessary option.

**First save method:**

In the first iteration of the save feature, all selected images were bundled in a zip file using Python and sent to the front end through a web socket. This proved to be successful at first, but later testing showed this method to be highly unstable. In the case where the zip file was relatively large, the web socket would lock up. This would result in the front end not receiving the zip file.

**Second and current save method:**

To eliminate the issue of the web socket locking up when receiving large amounts of data, packets were used instead. Rather than zipping the file into one large file in the back end, images are sent in packets of ten to the front end. The front end collects these packets and combines them into a zip file using JSZip. The user is then prompted with a save dialogue. This save dialogue is made possible by FileSaver.js.

**Notes:**

The current save feature is highly unstable but, a rudimentary option is available for testing when using Chrome. At the moment, users in Chrome have the option to save images in a zip format so long as the size of the selected images is not too large. This limit is estimated to be around 500 megabytes.

Take into consideration that the first save method may be viable in other cases that were not initially considered.

Results (As of 8/7/2015)
-------

Gmail-Image-Extractor currently allows users to login and scan their inbox for images. The resulting scan displays png, gif, and jpg images within the web browser. 

This scan accounts for the following outlier cases: duplicate image names, duplicate image types, and images of extreme size both small and large. However, there may be cases that have not been explored and further testing is needed to ensure those cases are managed effectively.

Gmail-Image-Extractor successfully deletes images from the user's account according to the cases mentioned above. 

As explained earlier, Gmail-Image-Extractor does not currently have a stable working option to save images. This feature will ideally allow the user to save all selected images within a zip file, regardless of the amount of images chosen. For testing the current unstable version of this feature, Chrome is recommended.

Conclusion
----------

The current version of Gmail-Image-Extractor is well on its way to becoming a promising tool for Gmail users to effectively manage their accounts with regard to images. Many features still need to be implemented, most importantly the ability to save images. Without this feature the use of this program is significantly devalued. To track the progress of this project, please visit https://github.com/bradleygolden/gmail-image-extractor.

Resources and References
----------

* JSZip https://stuk.github.io/jszip/
* FileSaver.js https://github.com/eligrey/FileSaver.js/
* Pygmail https://github.com/snyderp/pygmail
* Bootstrap http://getbootstrap.com/
* JQuery https://jquery.com
* JavaScript https://developer.mozilla.org/en-US/docs/Web/JavaScript
* HTML http://www.w3.org/html/
* CSS https://developer.mozilla.org/en-US/docs/Web/CSS
* Python https://www.python.org/
* Tornado http://www.tornadoweb.org/en/stable/
* GIT https://git-scm.com/
* Websockets https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API
* See more under ?Related Work?
