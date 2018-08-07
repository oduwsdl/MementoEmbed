==========================
RobustLinks Compatibility
==========================

Thanks to feedback from Los Alamos National Laboratory, MementoEmbed is compatible with `Robust Links <http://robustlinks.mementoweb.org>`_. 

If using social cards from MementoEmbed, there is one change to the instructions in the `RobustLinks documentation <https://github.com/mementoweb/robustlinks/blob/master/README.md>`_: instead of placing the reference of ``robustlinks-min.js`` inside the ``HEAD`` element of a web page's HTML, an author should place it at the end of the page so that ``robustlinks-min.js`` runs after all social cards have been loaded.

If using thumbnails from MementoEmbed, there is no change needed.

For more information on RobustLinks:

* `GitHub Repository with JavaScript and Documentation <https://github.com/mementoweb/robustlinks>`_
* `Link Decoration Documentation <http://robustlinks.mementoweb.org/spec/>`_
