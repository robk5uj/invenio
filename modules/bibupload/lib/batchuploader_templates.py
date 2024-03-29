# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

""" Batchuploader templates """

__revision__ = "$Id$"

import cgi
from invenio.dbquery import run_sql
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG
from invenio.messages import gettext_set_language
from invenio.bibrankadminlib import addadminbox, tupletotable

class Template:
    """Invenio Template class for creating Web Upload interface"""
    def tmpl_styles(self):
        """Defines the local CSS styles and javascript used in the plugin"""

        styles = """
        <style type="text/css">

        .mandatory_field{
            color:#ff0000
        }
        .italics{
            font-style:italic
        }
        .italics_small{
            font-style:italic;
            font-size: 0.9em;
        }

        #content {width:750px; font:90.1% arial, sans-serif;}

        #uploadform {margin:0 0 1em 0}


        #uploadform div {margin:0.5em 0}
        #uploadform fieldset {border:1px solid #657; padding:0.8em 1em; margin:2em 10px}

        #docuploadform {margin:0 0 1em 0}

        #docuploadform div {margin:0.5em 0}
        #docuploadform fieldset {border:1px solid #657; padding:0.8em 1em; margin:2em 10px}

        div.ui-datepicker{
            font-size:12px;
        }

        span.red{
            color:#df0000;
        }
        span.green{
            color:#060;
            background: transparent;
        }
        span.yellow{
            color:#9f9b00;
        }

        #info_box{
            border: 3px black solid;
            border-width: thin;
            width: 750px;
        }

        img.img_link {
            border-style: none;
        }

        </style>

        """

        styles += """
        <link type="text/css" href="%(site_url)s/img/jquery-ui.css" rel="stylesheet" />
        <script type="text/javascript">
            function clearText(field){
                if (field.value == field.defaultValue){
                    field.value = '';
                }
            }
            function defText(field){
                if (field.value == ''){
                    field.value = field.defaultValue;
                }
            }
        </script>
        <script type="text/javascript" src="%(site_url)s/js/ui.datepicker.min.js"></script>
        """ % {'site_url':CFG_SITE_URL}

        return styles

    def tmpl_display_web_metaupload_form(self, ln=CFG_SITE_LANG, error=0, filetype="marcxml", mode="--insert",
                                        submit_date="yyyy-mm-dd", submit_time="hh:mm:ss"):
        """ Displays Metadata upload form
            @param error: defines the type of error to be displayed
            @param mode: upload mode
            @param submit_date: file upload date
            @param submit_time: file upload time
            @return: the form in HTML format
        """
        _ = gettext_set_language(ln)
        body_content = ""
        body_content += """
        <script type="text/javascript">
            $(function() {
                $("#datepicker").datepicker({dateFormat: 'yy-mm-dd'});
            });
        </script>
        """
        body_content += """<form id="uploadform" method="post" action="%(site_url)s/batchuploader/metasubmit" enctype="multipart/form-data">""" \
                                       % {'site_url': CFG_SITE_URL}
        body_content += """
<div id="content">
<fieldset>
"""
        if error != 0:
            if error == 1:
                body_content += """
                <div><b>%(msg)s</b></div>
                """ % {'msg':_("Warning: Please, select a valid time")}
            elif error == 2:
                body_content += """
                <div><b>%(msg)s</b></div>
                """ % {'msg':_("Warning: Please, select a valid file")}
            elif error == 3:
                body_content += """
                <div><b>%(msg)s</b></div>
                """ % {'msg': _("Warning: The date format is not correct")}
            elif error == 4:
                body_content += """
                <div><b>%(msg)s</b></div>
                """ % {'msg': _("Warning: Please, select a valid date")}
        body_content += """
    <div><span class="mandatory_field""> * </span> %(txt_file)s:<input type="file" name="metafile" size="30" onChange="filename.value=(this.value)"></div>
    <input type="hidden" name="filename" id="filename" value="">
    <div><span class="mandatory_field""> * </span> %(txt_file_type)s:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <select name="filetype">
            <option %(type_sel1)s value="marcxml">MarcXML</option>
            <option %(type_sel2)s value="textmarc">TextMARC</option>
        </select>
    </div>
    <div><span class="mandatory_field""> * </span> %(txt_upload_mode)s:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <select name="mode">
            <option %(mode_sel1)s>--insert</option>
            <option %(mode_sel2)s>--replace</option>
            <option %(mode_sel3)s>--correct</option>
            <option %(mode_sel4)s>--append</option>
            <option %(mode_sel5)s>-ir insert-or-replace</option>
            <option %(mode_sel6)s>--delete</option>
        </select>
    <a href="%(site_url)s/help/admin/bibupload-admin-guide#3.3" target="_blank"><img class="img_link" src="/img/help.png" title="Upload mode help"></a>
    </div>
    <div>&nbsp;&nbsp;%(txt_priority)s:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <select name="priority">
            <option value="1">normal</option>
            <option value="5">high</option>
        </select>
    <br/>
    <div>%(txt_upload_later)s&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <span class="italics">%(txt_date)s:</span>
    <input type="text" id="datepicker" name="submit_date" value=%(submit_date)s onBlur="defText(this)" onFocus="clearText(this)" style="width:100px" >
    &nbsp;&nbsp;<span class="italics">%(txt_time)s:</span>
    <input type="text" name="submit_time" value=%(submit_time)s onBlur="defText(this)" onFocus="clearText(this)" style="width:100px" >
    <span class="italics">%(txt_example)s: 2009-12-20 19:22:18</span>
    <div><i>%(txt_mandatory)s</i></div>
    <div> <input type="submit" value="Upload" class="adminbutton"> </div>
</fieldset>
""" % {'txt_file': _("Select file to upload"),
        'txt_file_type': _("File type"),
        'txt_upload_mode': _("Upload mode"),
        'txt_upload_later': _("Upload later? then select:"),
        'txt_date': _("Date"),
        'txt_time': _("Time"),
        'txt_example': _("Example"),
        'txt_mandatory': _("All fields with %(x_fmt_open)s*%(x_fmt_close)s are mandatory") % \
                  {'x_fmt_open': '<span class="mandatory_field">', 'x_fmt_close': '</span>'},
        'txt_priority': _("Upload priority"),
        'type_sel1': filetype == 'marcxml' and "selected" or "",
        'type_sel2': filetype == 'textmarc' and "selected" or "",
        'mode_sel1': mode == '--insert' and "selected" or "",
        'mode_sel2': mode == '--replace' and "selected" or "",
        'mode_sel3': mode == '--correct' and "selected" or "",
        'mode_sel4': mode == '--append' and "selected" or "",
        'mode_sel5': mode == '-ir insert-or-replace' and "selected" or "",
        'mode_sel6': mode == '--delete' and "selected" or "",
        'site_url': CFG_SITE_URL,
        'submit_date': cgi.escape(submit_date),
        'submit_time': cgi.escape(submit_time)}

        body_content += """</form></div>"""
        return body_content

    def tmpl_upload_successful(self, ln=CFG_SITE_LANG):
        """ Displays message when the upload is successful """
        _ = gettext_set_language(ln)
        body_content = """<br/>"""
        body_content += _("Your file has been successfully queued. You can check your %(x_url1_open)supload history%(x_url1_close)s or %(x_url2_open)ssubmit another file%(x_url2_close)s") %\
             {'x_url1_open': "<a href=\"%s/batchuploader/history\">" % CFG_SITE_URL,
              'x_url1_close': "</a>",
              'x_url2_open': "<a href=\"%s/batchuploader/metadata\">" % CFG_SITE_URL,
              'x_url2_close': "</a>"}
        return body_content

    def tmpl_invalid_marcxml(self, ln=CFG_SITE_LANG):
        """ Displays message when the MARCXML is not valid """
        _ = gettext_set_language(ln)
        body_content = """<br/>"""
        body_content += _("The MARCXML submitted is not valid. Please, review the file and %(x_url2_open)sresubmit it%(x_url2_close)s") %\
             {'x_url2_open': "<a href=\"%s/batchuploader/metadata\">" % CFG_SITE_URL,
              'x_url2_close': "</a>"}
        return body_content

    def tmpl_upload_history(self, ln=CFG_SITE_LANG, upload_meta_list="", upload_doc_list=""):
        """Displays upload history of a given user"""
        _ = gettext_set_language(ln)

        body_content = ""
        body_content += "<h3> Metadata uploads </h3>"
        if not upload_meta_list:
            body_content += _("No metadata files have been uploaded yet.")
            body_content += "<br/>"
        else:
            body_content += """
            <table border=0>
            <tr>
            <b>
            <th>%(txt1)s</th>
            <th>%(txt2)s</th>
            <th>%(txt3)s</th>
            <th>%(txt4)s</th>
            </b>
            </tr>
            """ % {'txt1': _("Submit time"),
                    'txt2': _("File name"),
                    'txt3': _("Execution time"),
                    'txt4': _("Status")}
            for upload in upload_meta_list:
                color = ""
                if "ERROR" in upload[3]:
                    color = "red"
                elif upload[3] == "WAITING":
                    color = "yellow"
                elif upload[3] == "DONE":
                    color = "green"
                body_content += """
                <tr>
                <td style="text-align: center; vertical-align: middle; width: 220px;">%(submit_time)s</td>
                <td style="text-align: center; vertical-align: middle; width: 220px;">%(file_name)s</td>
                <td style="text-align: center; vertical-align: middle; width: 220px;">%(exec_time)s</td>
                <td style="text-align: center; vertical-align: middle; width: 220px;"><span class="%(color)s">%(status)s</span></td>
                </tr>
                """ % {'submit_time': upload[0],
                        'file_name': upload[1],
                        'exec_time': upload[2],
                        'color': color,
                        'status': upload[3]
                      }
            body_content += "</table><br/>"

        body_content += "<h3> Document uploads </h3>"
        if not upload_doc_list:
            body_content += _("No document files have been uploaded yet.")
            body_content += "<br/>"
        else:
            body_content += """
            <table border=0>
            <tr>
            <b>
            <th>%(txt1)s</th>
            <th>%(txt2)s</th>
            <th>%(txt3)s</th>
            <th>%(txt4)s</th>
            </b>
            </tr>
            """ % {'txt1': _("Submit time"),
                    'txt2': _("File name"),
                    'txt3': _("Execution time"),
                    'txt4': _("Status")}
            for upload in upload_doc_list:
                color = ""
                if "ERROR" in upload[3]:
                    color = "red"
                elif upload[3] == "WAITING":
                    color = "yellow"
                elif upload[3] == "DONE":
                    color = "green"
                body_content += """
                <tr>
                <td style="text-align: center; vertical-align: middle; width: 220px;">%(submit_time)s</td>
                <td style="text-align: center; vertical-align: middle; width: 220px;">%(file_name)s</td>
                <td style="text-align: center; vertical-align: middle; width: 220px;">%(exec_time)s</td>
                <td style="text-align: center; vertical-align: middle; width: 220px;"><span class="%(color)s">%(status)s</span></td>
                </tr>
                """ % {'submit_time': upload[0],
                        'file_name': upload[1],
                        'exec_time': upload[2],
                        'color': color,
                        'status': upload[3]
                       }
            body_content += "</table>"

        return body_content

    def tmpl_display_menu(self, ln=CFG_SITE_LANG, ref=""):
        """ Displays menu with all upload options """
        _ = gettext_set_language(ln)
        body_content = """
        <table>
            <td>0.&nbsp;<small>%(upload_open_link)s%(text1)s%(upload_close_link)s</small></td>
            <td>1.&nbsp;<small>%(docupload_open_link)s%(text2)s%(docupload_close_link)s</small></td>
            <td>2.&nbsp;<small>%(history_open_link)s%(text3)s%(history_close_link)s</small></td>
            <td>3.&nbsp;<small>%(daemon_open_link)s%(text4)s%(daemon_close_link)s</small></td>
            </tr>
        </table>
        """ % { 'upload_open_link': not ref == "metadata" and "<a href=\"%s/batchuploader/metadata?ln=%s\">" % (CFG_SITE_URL, ln) or "",
                'upload_close_link': not ref == "metadata" and "</a>" or "",
                'text1': _("Metadata batch upload"),
                'docupload_open_link': not ref == "documents" and "<a href=\"%s/batchuploader/documents?ln=%s\">" % (CFG_SITE_URL, ln) or "",
                'docupload_close_link': not ref == "documents" and "</a>" or "",
                'text2': _("Document batch upload"),
                'history_open_link': not ref == "history" and "<a href=\"%s/batchuploader/history?ln=%s\">" % (CFG_SITE_URL, ln) or "",
                'history_close_link': not ref == "history" and "</a>" or "",
                'text3': _("Upload history"),
                'daemon_open_link': not ref == "daemon" and "<a href=\"%s/batchuploader/daemon?ln=%s\">" % (CFG_SITE_URL, ln) or "",
                'daemon_close_link': not ref == "daemon" and "</a>" or "",
                'text4': _("Daemon monitor")
               }
        return addadminbox("<b>Menu</b>", [body_content])

    def tmpl_display_web_docupload_form(self, ln=CFG_SITE_LANG, submit_date="yyyy-mm-dd", submit_time="hh:mm:ss"):
        """ Display form used for batch document upload """
        _ = gettext_set_language(ln)
        body_content = """
                        <script type="text/javascript">
                        $(function() {
                            $("#datepicker").datepicker({dateFormat: 'yy-mm-dd'});
                        });
                        </script>
                        """
        body_content += """<form id="docuploadform" method="post" action="%(site_url)s/batchuploader/docsubmit" enctype="multipart/form-data">""" \
                           % {'site_url': CFG_SITE_URL}
        body_content += """
        <div id="content">
        <fieldset>
        <div><span class="mandatory_field""> * </span> %(txt1)s:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="text" name="docfolder" size="30" />
        <span class="italics">%(txt2)s: /afs/cern.ch/user/j/user/public/foo/</span></div>
        <div><span class="mandatory_field""> * </span> %(txt3)s:
        <select name="matching">
            <option value="reportnumber">reportnumber</option>
            <option value="recid">recid</option>
        </select>
        </div>
        <div><span class="mandatory_field""> * </span> %(txt4)s:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="radio" name="mode" value="append" "checked" id="appendcheckbox"/><label for="appendcheckbox">append</label>
                                                                <input type="radio" name="mode" value="correct" id="revisecheckbox"/><label for="revisecheckbox">revise</label>
        </div>
        <div>&nbsp;&nbsp;%(txt_priority)s:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <select name="priority">
            <option value="1">normal</option>
            <option value="5">high</option>
        </select>
        <br/>
        <div>%(txt5)s&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <span class="italics">%(txt6)s:</span>
        <input type="text" id="datepicker" name="submit_date" value=%(submit_date)s onBlur="defText(this)" onFocus="clearText(this)" style="width:100px" >
        &nbsp;&nbsp;<span class="italics">%(txt7)s:</span>
        <input type="text" name="submit_time" value=%(submit_time)s onBlur="defText(this)" onFocus="clearText(this)" style="width:100px" >
        <span class="italics">%(txt8)s: 2009-12-20 19:22:18</span>
        <br/>
        <div><i>%(txt9)s</i></div>
        <div> <input type="submit" value="Upload" class="adminbutton"> </div>
        </fieldset>
        </form></div>
        """ % {'submit_date': submit_date,
               'submit_time': submit_time,
               'txt_priority': _("Upload priority"),
               'txt1': _("Input directory"),
               'txt2': _("Example"),
               'txt3': _("Filename matching"),
               'txt4': _("Upload mode"),
               'txt5': _("Upload later? then select:"),
               'txt6': _("Date"),
               'txt7': _("Time"),
               'txt8': _("Example"),
               'txt9': _("All fields with %(x_fmt_open)s*%(x_fmt_close)s are mandatory") % \
                        {'x_fmt_open': '<span class="mandatory_field">', 'x_fmt_close': '</span>'}
               }
        return body_content

    def tmpl_display_web_docupload_result(self, ln=CFG_SITE_LANG, errors=None, info=None):
        """ Display results from the document upload """
        _ = gettext_set_language(ln)
        body_content = "<br/>"
        body_content += _("<b>%s documents</b> have been found." % info[0])
        body_content += "<br/><br/>"
        body_content += _("The following files have been successfully queued:")
        body_content += "<ul>"
        for uploaded_file in info[1]:
            body_content += "<li><b>%s</b></li>" % uploaded_file
        body_content += "</ul>"
        body_content += _("The following errors have occurred:")
        body_content += "<ul>"
        for error in errors:
            if error != 'MoveError':
                body_content += "<li><b>%s</b> : %s</li>" % (cgi.escape(str(error[0])), cgi.escape(str(error[1])))
        body_content += "</ul>"
        if 'MoveError' in errors:
            body_content += "<div><i><b>" + _("Some files could not be moved to DONE folder. Please remove them manually.") + "</b></i></div><br/>"
        else:
            body_content += "<div><i><b>" + _("All uploaded files were moved to DONE folder.") + "</b></i></div><br/>"
        body_content += "<a href=\"%(docupload_url)s\">Return to upload form</a>" % \
                        {'docupload_url': "%s/batchuploader/documents?ln=%s" % (CFG_SITE_URL, ln) }
        return body_content

    def tmpl_daemon_content(self, ln=CFG_SITE_LANG, docs=None, metadata=None):
        """ Displays all information related with batch uploader daemon mode """
        _ = gettext_set_language(ln)
        body_content = "<br/><div id=\"info_box\">"
        body_content += "<ul>"
        body_content += "<li>" + _("Using %(x_fmt_open)sweb interface upload%(x_fmt_close)s, actions are executed a single time.") % \
                        {'x_fmt_open': '<b>', 'x_fmt_close':'</b>'} + "</li>"
        body_content += "<li>" + _("Check the %(x_url_open)sBatch Uploader daemon help page%(x_url_close)s for executing these actions periodically.") % \
                        {'x_url_open': '<a href="%s/help/admin/bibupload-admin-guide#4.2">' % CFG_SITE_URL,
                         'x_url_close': "</a>"} + \
                         "</li>"
        body_content += "</div><br/>"
        body_content += "<h3>%s</h3>" % _("Metadata folders")
        body_content += "<ul>"
        for folder in metadata.keys():
            body_content += "<li><b>" + folder + "</b></li>"
            for filename, info in metadata[folder]:
                body_content += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                for stat in info:
                    body_content += "%s&nbsp;&nbsp;" % stat
                body_content += filename + "<br />"
        body_content += "</ul>"

        body_content += "<h3> Document folders </h3>"
        body_content += "<ul>"
        for folder in docs.keys():
            body_content += "<li><b>" + folder + "</b></li>"
            body_content += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            for filename, info in docs[folder]:
                for stat in info:
                    body_content += "%s&nbsp;&nbsp;" % stat
                body_content += filename + "<br />"
        body_content += "</ul>"

        header = [_("ID"), _("Name"), _("Time"), _("Status"), _("Progress")]
        actions = []
        body_content += """<br /><b>%s</b><br />""" % _("Last BibSched tasks:")
        res = run_sql("select id, proc, host, user, runtime, sleeptime, arguments, status, progress from schTASK where proc='batchuploader' and runtime< now() ORDER by runtime")
        if len(res) > 0:
            (tsk_id, proc, host, user, runtime, sleeptime, arguments, status, progress) = res[len(res) - 1]
            actions.append([tsk_id, proc, runtime, (status !="" and status or ''), (progress !="" and progress or '')])
        else:
            actions.append(['', 'batchuploader', '', '', 'Not executed yet'])

        body_content += tupletotable(header=header, tuple=actions)
        body_content += """<br /><b>%s</b><br />""" % _("Next scheduled BibSched run:")
        actions = []
        res = run_sql("select id, proc, host, user, runtime, sleeptime, arguments, status, progress from schTASK where proc='batchuploader' and runtime > now() ORDER by runtime")
        if len(res) > 0:
            (tskid, proc, host, user, runtime, sleeptime, arguments, status, progress) = res[0]
            actions.append([tskid, proc, runtime, (status !="" and status or ''), (progress !="" and progress or '')])
        else:
            actions.append(['', 'batchuploader', '', '', 'Not scheduled'])

        body_content += tupletotable(header=header, tuple=actions)

        return body_content


