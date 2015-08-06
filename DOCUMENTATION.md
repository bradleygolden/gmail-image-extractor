Intro
-----

Email clients are offering larger and larger storage space for emails as time progresses. Currently, Gmail offers 100 gigabytes of space for their users and this figure is growing each year. As Gmail's storage limit increases, many consumers continue to archive emails for various reasons including saving for later use. Among these saved emails, many may contain images that have sentimental value, contain personal information, and more. The existence of these images also provides opportunities for hackers to exploit users unknowingly.  Therefore, it's important to provide gmail users with tools to effectively manage their email account for the purpose of increasing security and the awareness of the data that exists within their accounts. Gmail Image Extractor is the current solution for providing users the access to secure photo attachments in one easy location. Gmail Image Extractor requires no extra login information then their pre-existing email account information and is completely web based for ease of use.

Related Work
------------

- Cloudsweeper, a web application that provides Gmail users with tools to secure their Gmail accounts. More information can be found here: https://cloudsweeper.cs.uic.edu/ 
- AttachmentExtractor for Thunderbird extracts attachments from emails and allows users to delete, detach, or mark the messages as read. More information can be found here: https://addons.mozilla.org/en-US/thunderbird/addon/attachmentextractor/
- Mail Attachment Downloader for Windows has many options, including the ability to download and delete attachments from emails. More information can be found here: http://gearmage.com/maildownloader.html
- Save Emails and Attachments for Google Sheets has the option to download images and varying attachments from Gmail to Google Drive. More information can be found here: https://chrome.google.com/webstore/detail/save-emails-and-attachmen/nflmnfjphdbeagnilbihcodcophecebc?hl=en


Methodology
-----------

Gmail-Image-Extractor uses the pygmail python module for extracting images from users Gmail accounts. 

Unique Image ID's and Message ID's:
Individual mail messages are loaded from the user's Gmail account and each message is scanned for attachments. Each message has a unique id that is stored for later reference. Upon finding an attachment, each is also linked with a unique id for the purpose creating a key that can be used to reference an attachment within a particular message. The message id consists of an integer value that is assigned by pygmail and the attachment id consists of a hex value. This hex value is determined by the attachment objectÕs current location in memory. Because this particular method is used it's very important that email messages are only extracted once from the userÕs Gmail account. Repeated loading of mail messages from Gmail results in varying memory locations for each attachment object and reduces the likelihood of later locating attachments using the idÕs mention above.

Extracting and Sending Images to the Front End:
Each attachment contains an attachment body in the following formats: jpg, png, and gif format. The current extractor uses each image body to display the attachment to the user. This is done by first reducing the image size to increase overall performance, encoding the image to a base64 string and sending the image body to the front end via web sockets. The front end then uses the unique id of the image and the base64 string to display the image to the user.

Deleting Images from the User's Account:
The user has the option to select various images through Gmail Image Extractor's front-end interface. After all images selected for removal have been verified by the user, corresponding unique image ids and message ids are sent to the back-end. The back-end sorts each message into a list of attachments and then removes each selected attachment where the message id and image id match the userÕs selection. The removal of each message is accomplished through the pygmail module.
 
Results (As of 8/6/2015)
-------

Gmail-Image-Extractor currently allows users to login and scan their inbox for images. The resulting scan displays png, gif, and jpg images within the web browser. 

This scan accounts for the following outlier cases: duplicate image names, duplicate image types, and images of extreme size both small and large. However, there may be cases that have not been explored and further testing is needed to ensure those cases are managed effectively.

Gmail-Image-Extractor successfully deletes images from the user's account according to the cases mentioned above. 

Gmail-Image-Extractor does not currently have a working option to save images. This feature will ideally allow the user to save all selected images within a zip file. Some considerations must be taken when introducing this feature. Some include the type of browser the client is using and the size of the resulting selection of images.

Conclusion
----------

The current version of Gmail-Image-Extractor is well on its way to becoming a promising tool for gmail users to effectively manage their accounts with regard to images. Many features still need to be implemented, most importantly the ability to save images. Without this feature the use of this program is significantly devalued. To track the progress of this project, please visit https://github.com/bradleygolden/gmail-image-extractor.
