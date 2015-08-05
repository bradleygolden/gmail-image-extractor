Gmail Email Extractor
===
Offers Gmail users the ability to scan their mailbox for images and save/delete those images.

## Delete functionality - Working
* This feature works very well with both small and large datasets of varying types.

## Save functionality - Broken
* This feature is ridden with issues
  * Current solution
    * I originally tried to send all of the images in packets of 10 via web sockets to the front-end where the front-end combines the packets and puts them in one large zip file. The user can then choose where to download that file. This works intermittently depending on the browser being used and the file size. This doesn't work for large data sets generally 500mb or more. This method makes the solution to the problem difficult.
  * Next solution
    * Create zip server size, save it, and send file to front-end. File size will have to be limited roughly 400mb
    * For larger image sets, the solution is still unknown...

## Current Bugs
  * The server does not allow for multiple users to run the image extractor at the same time.
    * Solution - Allow the server to run asynchronously
  * Gmails security settings make it difficult to access gmail account without manually changing settings in google's security console (this is a tricky process)
    * Solution - OAuth 2.0
  * Save functionality breaks after the first save
    * Solution - This bug hasn't been explored in detail yet

## Todo's (In order of importance)
  1. Display "Are you sure?" prompt to user prior deletion
  2. Save feature - mentioned above
  3. Create save progress bar - looks as if the app is broken, needs a progress bar
  4. Implement web logs for error tracking, etc.
  5. Use HMAC to secure image information in front-end
    * Currently each image is uniquely associated with an id. This id is the memory location in hex format of the image's respective gmail attachment object. The next step for improving security is to hash the id's using HMAC to gurentee secured unqiue id's. The algorithm will look like the following:
      * Get hex value of memory location from attachment [image id]
      * Get image name from attachment
      * Hash each image id using sha256
      * Create dict with hashed image id and image id for reference
      * Create HMAC key from hashed image id and secret
      * Send HMAC key and image name to front end
      * Add image name and HMAC key image thumbnail node name and id respectively
      * Add image name to preview modal title
  6. Create delete progress bar - images already disappear as they are erased, this is extra
  7. Display otal images saved/deleted at the top of the page
  8. Feedback feature - allow users to send feedback

Requirements
---
 * [pygmail](https://github.com/snyderp/pygmail)
