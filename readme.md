### Project: Multi user blog

Basic blog that runs on Google App Engine using Python. 

**Registered Users:**
 - Allowed to create new posts
 - Allowed to leave comments
 - Like and unlike posts that they didn't create
 - Delete their own posts and comments

**Visitors:**
 - Allowed to view posts

---

First thing is to change the "secret" key on **line 23** in the **main.py** file.

    secret = "some long key . ...... .."


####**Run Locally:**
 1. Install Python if necessary. 
 2. Install [Google App Engine SDK](https://cloud.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python).
 3. Clone this repository to your local machine:
 4. cd into cloned directory
 5. run: **dev_appserver.py app.yaml**
 6. You should be able to access the site @ http://localhost:8080
 
####**Run on Google App Engine:** 
 6. [Sign Up for a Google App Engine Account](https://console.cloud.google.com/appengine/)
 7. In the project directory run **gcloud app deploy** and **gcloud datastore create-indexes index.yaml**
 8. Visit [Quickstart for Python App Engine Standard Environment](https://cloud.google.com/appengine/docs/standard/python/quickstart) for more information.

---

####Possible Errors
If you get a 500 status error clicking on a post link or authors link. Login to your google app account and goto Datastore. Make sure that your indexes are created and ready. If you have no indexes, run
**gcloud datastore create-indexes index.yaml** to create indexes.

---

[Demo Site](https://udacity-167021.appspot.com)

