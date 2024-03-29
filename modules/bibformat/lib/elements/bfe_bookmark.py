# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""BibFormat element - bookmark toolbar using:

    <http://keith-wood.name/bookmark.html>

"""

import cgi

from invenio.config import CFG_SITE_URL, CFG_SITE_RECORD
from invenio.search_engine import record_public_p
from invenio.bibformat_elements.bfe_sciencewise import create_sciencewise_url, \
    get_arxiv_reportnumber

def format_element(bfo, only_public_records=1, sites="linkedin,twitter,facebook,google,delicious,sciencewise"):
    """
    Return a snippet of JavaScript needed for displaying a bookmark toolbar

    @param only_public_records: if set to 1 (the default), prints the box only
        if the record is public (i.e. if it belongs to the root colletion and is
        accessible to the world).

    @param sites: which sites to enable (default is 'linkedin,twitter,facebook,google,delicious,sciencewise'). This should be a
        comma separated list of strings.
        Valid values are available on:
            <http://keith-wood.name/bookmark.html#sites>
        Note that 'sciencewise' is an ad-hoc service that will be displayed
        only in case the record has an arXiv reportnumber and will always
        be displayed last.
    """
    if int(only_public_records) and not record_public_p(bfo.recID):
        return ""

    sitelist = sites.split(',')
    sitelist = [site.strip().lower() for site in sitelist]

    sciencewise = False
    if 'sciencewise' in sitelist:
        sciencewise = True
        sitelist.remove('sciencewise')

    sites_js = ", ".join("'%s'" % site for site in sitelist)

    title = bfo.field('245__a')
    description = bfo.field('520__a')

    sciencewise_script = ""
    if sciencewise:
        reportnumber = get_arxiv_reportnumber(bfo)
        if reportnumber:
            sciencewise_url = create_sciencewise_url(reportnumber)
            if sciencewise_url:
                sciencewise_script = """\
    $.bookmark.addSite('sciencewise', 'ScienceWise.info', '%(siteurl)s/img/sciencewise.png', 'en', 'bookmark', '%(url)s');
    $('#bookmark_sciencewise').bookmark({sites: ['sciencewise']});
""" % {
                    'siteurl': CFG_SITE_URL,
                    'url': sciencewise_url.replace("'", r"\'"),
                }

    return """\
<!-- JQuery Bookmark Button BEGIN -->
<div id="bookmark"></div><div id="bookmark_sciencewise"></div>
<style type="text/css">
    #bookmark_sciencewise, #bookmark { float: left; }
    #bookmark_sciencewise li { padding: 2px; width: 25px}
    #bookmark_sciencewise ul, #bookmark ul { list-style-image: none; }
</style>
<script type="text/javascript" src="%(siteurl)s/js/jquery.bookmark.min.js"></script>
<style type="text/css">@import "%(siteurl)s/css/jquery.bookmark.css";</style>
<script type="text/javascript">// <![CDATA[
    %(sciencewise)s
    $('#bookmark').bookmark({
        sites: [%(sites_js)s],
        icons: '%(siteurl)s/img/bookmarks.png',
        url: '%(siteurl)s/%(record)s/%(recid)s',
        addEmail: true,
        title: '%(title)s',
        description: '%(description)s'
    });
// ]]>
</script>
<!-- JQuery Bookmark Button END -->
""" % {
        'siteurl': CFG_SITE_URL,
        'sciencewise': sciencewise_script,
        'title': cgi.escape(title).replace("'", r"\'"),
        'description': cgi.escape(description).replace("'", r"\'"),
        'sites_js': sites_js,
        'record': CFG_SITE_RECORD,
        'recid': bfo.recID
    }

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
